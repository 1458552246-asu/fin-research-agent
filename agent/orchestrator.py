"""
Orchestrator - Coordinates the multi-agent workflow.

Pipeline (4 phases):
1. Research Team (information gathering)
2. Debate Team (3-round bull/bear debate)
3. Valuation Agent (relative valuation + scenario pricing)
4. Decision Agent (final recommendation + scorecard)

Optional Phase 0: ReAct Agent (intelligent routing + data collection)
"""

from typing import Optional, Callable, Generator, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

from .models import (
    WorkflowState, ResearchReport, DebateResult, Decision,
    SourceGroup, KeyFact, SourceReference, Sentiment
)
from .research_team import ResearchTeam
from .debate_team import DebateTeam
from .valuation_agent import ValuationAgent, ValuationResult
from .decision_agent import DecisionAgent
from .signal_detection import SignalDetectionAgent, SignalReport
from .sufficiency_check import check_sufficiency, SufficiencyResult
from .scorecard import Scorecard, build_scorecard
from .smart_summary import generate_smart_summary, generate_summary_json
from .react_agent import ReActAgent, AgentStep, AgentOutput
from .tools import get_all_tools
from .config import Config


@dataclass
class PhaseProgress:
    """Progress update from a workflow phase."""
    phase: int                # 1-4
    phase_name: str           # "Research", "Debate", "Valuation", "Decision"
    message: str              # Progress message
    is_complete: bool = False # Whether phase is complete
    data: Optional[any] = None  # Phase output data


def _extract_ticker(query: str) -> str:
    """Try to extract a stock ticker from the query."""
    # Common patterns: "NVDA", "分析NVIDIA", "$TSLA"
    ticker_match = re.search(r'\$?([A-Z]{2,5})\b', query.upper())
    if ticker_match:
        return ticker_match.group(1)

    # Chinese company name mapping (basic)
    name_map = {
        "英伟达": "NVDA", "nvidia": "NVDA",
        "特斯拉": "TSLA", "tesla": "TSLA",
        "苹果": "AAPL", "apple": "AAPL",
        "台积电": "TSM", "tsmc": "TSM",
        "戴尔": "DELL", "dell": "DELL",
        "海力士": "000660.KS",
    }
    query_lower = query.lower()
    for name, ticker in name_map.items():
        if name in query_lower:
            return ticker

    return "UNKNOWN"


class Orchestrator:
    """
    Coordinates the 4-phase financial research workflow.

    Pipeline:
        Research → Debate (3-round) → Valuation → Decision

    Usage:
        orchestrator = Orchestrator()
        result = orchestrator.run("分析英伟达")

        # Or with streaming:
        for progress in orchestrator.run_streaming("分析英伟达"):
            print(progress.message)
    """

    def __init__(self):
        self.research_team = ResearchTeam()
        self.debate_team = DebateTeam()
        self.valuation_agent = ValuationAgent()
        self.decision_agent = DecisionAgent()
        self.signal_agent = SignalDetectionAgent()
        self.react_agent = ReActAgent(tools=get_all_tools(), max_steps=5)

    def run_react_phase(
        self,
        query: str,
        on_step: Optional[Callable[[AgentStep], None]] = None
    ) -> AgentOutput:
        """
        Phase 0: Run ReAct Agent for intelligent information gathering.

        Args:
            query: User's research question
            on_step: Callback for each reasoning step (for UI)

        Returns:
            AgentOutput with reasoning trace and collected documents
        """
        return self.react_agent.run(query, on_step=on_step)

    def build_report_from_agent(self, agent_output: AgentOutput, query: str) -> ResearchReport:
        """
        Build a ResearchReport from ReAct Agent's collected documents.

        Converts the agent's gathered data into the structured format
        expected by downstream phases.
        """
        documents = agent_output.collected_documents

        if not documents:
            return self.research_team.research(query)

        # Group documents by source_type
        groups = {}
        for doc in documents:
            source_type = doc.get("source_type", "unknown")
            if source_type not in groups:
                groups[source_type] = []
            groups[source_type].append(doc)

        # Build SourceGroups
        sources = []
        for source_type, docs in groups.items():
            source_group = SourceGroup(
                source_type=source_type,
                source_name=source_type,
                date=docs[0].get("date") if docs else None,
                findings=[doc.get("content", "") for doc in docs],
                raw_documents=docs
            )
            sources.append(source_group)

        # Extract key facts
        key_facts = []
        for source in sources:
            for finding in source.findings[:3]:
                if not finding:
                    continue
                sentiment = Sentiment.NEUTRAL
                if any(word in finding.lower() for word in ["增长", "上升", "强劲", "超预期", "bullish", "growth"]):
                    sentiment = Sentiment.POSITIVE
                elif any(word in finding.lower() for word in ["下降", "风险", "下滑", "压力", "bearish", "decline"]):
                    sentiment = Sentiment.NEGATIVE

                key_facts.append(KeyFact(
                    content=finding[:200] + "..." if len(finding) > 200 else finding,
                    sentiment=sentiment,
                    source=SourceReference(
                        source_type=source.source_name,
                        title=source.source_name,
                        date=source.date
                    )
                ))

        return ResearchReport(
            query=query,
            sources=sources,
            key_facts=key_facts,
            total_sources_found=len(documents),
            search_terms_used=[query]
        )

    def run(
        self,
        query: str,
        ticker: Optional[str] = None,
        current_price: Optional[float] = None,
        progress_callback: Callable[[str], None] = None
    ) -> WorkflowState:
        """
        Run complete 4-phase workflow.

        Args:
            query: User's research question
            ticker: Stock ticker (auto-detected if not provided)
            current_price: Current stock price (optional)
            progress_callback: Optional callback for progress updates

        Returns:
            WorkflowState with all phase outputs
        """
        state = WorkflowState(query=query)
        ticker = ticker or _extract_ticker(query)

        try:
            # Phase 1: Research
            state.current_phase = 1
            if progress_callback:
                progress_callback("📋 Phase 1: 研究团队收集信息...")

            # research_team callback takes (phase, msg) - wrap it
            def research_cb(phase, msg):
                if progress_callback:
                    progress_callback(f"  [{phase}] {msg}")

            state.research_report = self.research_team.research(
                query, research_cb
            )

            # Phase 2: Debate (3-round) + Sufficiency Check (max 1 retry)
            state.current_phase = 2
            if progress_callback:
                progress_callback("⚔️ Phase 2: 多空辩论（3轮）...")

            max_debate_attempts = 2
            for attempt in range(max_debate_attempts):
                state.debate_result = self.debate_team.debate(
                    state.research_report,
                    enable_cross_exam=True,
                    progress_callback=progress_callback
                )

                # Sufficiency check
                sufficiency = check_sufficiency(
                    state.debate_result, state.research_report
                )

                if sufficiency.is_sufficient or attempt >= max_debate_attempts - 1:
                    if progress_callback:
                        if sufficiency.is_sufficient:
                            progress_callback(
                                f"  ✓ 信息充分度: {sufficiency.score:.0%} — 通过"
                            )
                        else:
                            progress_callback(
                                f"  ⚠️ 信息充分度: {sufficiency.score:.0%} — "
                                f"仍不足但已达最大重试，继续"
                            )
                    break
                else:
                    # Insufficient: supplement research and retry
                    if progress_callback:
                        progress_callback(
                            f"  ⚠️ 信息充分度: {sufficiency.score:.0%} — 不足，"
                            f"回退补充检索（{len(sufficiency.gaps_to_fill)}个缺口）"
                        )
                        for gap in sufficiency.gaps_to_fill[:3]:
                            progress_callback(f"    → 补充: {gap[:60]}")

                    # Supplement research with gap queries
                    supplemental = self._supplement_research(
                        state.research_report, sufficiency.gaps_to_fill,
                        progress_callback
                    )
                    state.research_report = supplemental

            # Phase 3: Valuation
            state.current_phase = 3
            if progress_callback:
                progress_callback("💰 Phase 3: 估值分析...")

            state.valuation_result = self.valuation_agent.evaluate(
                ticker=ticker,
                debate_result=state.debate_result,
                research_report=state.research_report,
                current_price=current_price,
                progress_callback=progress_callback
            )

            # Phase 4: Decision
            state.current_phase = 4
            if progress_callback:
                progress_callback("📈 Phase 4: 生成投资决策...")

            state.decision = self.decision_agent.decide(
                state.research_report,
                state.debate_result,
                progress_callback
            )

            # Phase 5: Signal Detection
            state.current_phase = 5
            if progress_callback:
                progress_callback("📡 Phase 5: 信号检测...")

            state.signal_report = self.signal_agent.extract_from_analysis(
                ticker=ticker,
                decision=state.decision,
                debate_result=state.debate_result,
                valuation_result=state.valuation_result,
                progress_callback=progress_callback,
            )

            # Generate Scorecard & Smart Summary
            if progress_callback:
                progress_callback("📊 生成决策打分卡与投研简报...")

            scorecard = build_scorecard(
                ticker=ticker,
                decision=state.decision,
                valuation_result=state.valuation_result,
                debate_result=state.debate_result,
                research_report=state.research_report,
            )
            state.scorecard = scorecard
            state.smart_summary = generate_smart_summary(state, scorecard)
            state.summary_json = generate_summary_json(state, scorecard)

            if progress_callback:
                progress_callback(
                    f"  综合评分: {scorecard.total_score:.2f}/10 — {scorecard.interpretation}"
                )

            state.mark_complete()
            if progress_callback:
                progress_callback("✅ 分析完成!")

        except Exception as e:
            state.errors.append(str(e))
            if progress_callback:
                progress_callback(f"❌ 错误: {e}")

        return state

    def _supplement_research(
        self,
        existing_report: ResearchReport,
        gaps: List[str],
        progress_callback: Callable = None,
    ) -> ResearchReport:
        """
        Supplement existing research with additional queries to fill gaps.

        Runs additional research queries and merges results into the existing report.
        """
        if progress_callback:
            progress_callback("  🔍 补充检索中...")

        # Run supplemental research for each gap
        for gap_query in gaps[:3]:  # Limit to 3 supplement queries
            try:
                supplement_report = self.research_team.research(
                    gap_query, lambda phase, msg: None  # Silent callback
                )
                # Merge supplemental data into existing report
                existing_report.sources.extend(supplement_report.sources)
                existing_report.key_facts.extend(supplement_report.key_facts)
                existing_report.total_sources_found += supplement_report.total_sources_found
                existing_report.search_terms_used.append(gap_query)
            except Exception as e:
                if progress_callback:
                    progress_callback(f"  ⚠️ 补充检索失败: {gap_query[:30]}... ({e})")

        if progress_callback:
            progress_callback(
                f"  ✓ 补充完成: 现有 {existing_report.total_sources_found} 条数据, "
                f"{len(existing_report.key_facts)} 个关键事实"
            )

        return existing_report

    def run_streaming(
        self,
        query: str,
        ticker: Optional[str] = None,
        current_price: Optional[float] = None,
    ) -> Generator[PhaseProgress, None, WorkflowState]:
        """
        Run workflow with streaming progress updates.

        Yields PhaseProgress objects for UI updates.

        Usage:
            for progress in orchestrator.run_streaming(query):
                update_ui(progress)
        """
        state = WorkflowState(query=query)
        ticker = ticker or _extract_ticker(query)
        progress_messages = []

        def collect_progress(msg: str):
            progress_messages.append(msg)

        def research_progress(phase, msg):
            progress_messages.append(f"[{phase}] {msg}")

        try:
            # Phase 1: Research
            state.current_phase = 1
            yield PhaseProgress(
                phase=1, phase_name="Research",
                message="📋 Phase 1: 研究团队收集信息..."
            )

            state.research_report = self.research_team.research(
                query, research_progress
            )

            for msg in progress_messages:
                yield PhaseProgress(phase=1, phase_name="Research", message=msg)
            progress_messages.clear()

            yield PhaseProgress(
                phase=1, phase_name="Research",
                message=f"✅ Phase 1 完成: 收集了 {state.research_report.total_sources_found} 条信息",
                is_complete=True, data=state.research_report
            )

            # Phase 2: Debate + Sufficiency Check (max 1 retry)
            state.current_phase = 2
            yield PhaseProgress(
                phase=2, phase_name="Debate",
                message="⚔️ Phase 2: 多空辩论（3轮）..."
            )

            max_debate_attempts = 2
            for attempt in range(max_debate_attempts):
                state.debate_result = self.debate_team.debate(
                    state.research_report,
                    enable_cross_exam=True,
                    progress_callback=collect_progress
                )

                for msg in progress_messages:
                    yield PhaseProgress(phase=2, phase_name="Debate", message=msg)
                progress_messages.clear()

                # Sufficiency check
                sufficiency = check_sufficiency(
                    state.debate_result, state.research_report
                )

                if sufficiency.is_sufficient or attempt >= max_debate_attempts - 1:
                    suffix = "通过" if sufficiency.is_sufficient else "仍不足，继续"
                    yield PhaseProgress(
                        phase=2, phase_name="Debate",
                        message=f"  ✓ 信息充分度: {sufficiency.score:.0%} — {suffix}"
                    )
                    break
                else:
                    yield PhaseProgress(
                        phase=2, phase_name="Debate",
                        message=f"  ⚠️ 信息充分度: {sufficiency.score:.0%} — 不足，回退补充检索"
                    )
                    # Supplement research
                    self._supplement_research(
                        state.research_report, sufficiency.gaps_to_fill,
                        collect_progress
                    )
                    for msg in progress_messages:
                        yield PhaseProgress(phase=2, phase_name="Debate", message=msg)
                    progress_messages.clear()

            ratio = state.debate_result.bull_bear_ratio
            yield PhaseProgress(
                phase=2, phase_name="Debate",
                message=f"✅ Phase 2 完成: 多空比 {ratio:.0%}:{1-ratio:.0%}",
                is_complete=True, data=state.debate_result
            )

            # Phase 3: Valuation
            state.current_phase = 3
            yield PhaseProgress(
                phase=3, phase_name="Valuation",
                message="💰 Phase 3: 估值分析..."
            )

            state.valuation_result = self.valuation_agent.evaluate(
                ticker=ticker,
                debate_result=state.debate_result,
                research_report=state.research_report,
                current_price=current_price,
                progress_callback=collect_progress
            )

            for msg in progress_messages:
                yield PhaseProgress(phase=3, phase_name="Valuation", message=msg)
            progress_messages.clear()

            val_msg = "✅ Phase 3 完成"
            if state.valuation_result.weighted_target:
                val_msg += f": 加权目标价 ${state.valuation_result.weighted_target:.0f}"
            yield PhaseProgress(
                phase=3, phase_name="Valuation",
                message=val_msg, is_complete=True,
                data=state.valuation_result
            )

            # Phase 4: Decision
            state.current_phase = 4
            yield PhaseProgress(
                phase=4, phase_name="Decision",
                message="📈 Phase 4: 生成投资决策..."
            )

            state.decision = self.decision_agent.decide(
                state.research_report,
                state.debate_result,
                collect_progress
            )

            for msg in progress_messages:
                yield PhaseProgress(phase=4, phase_name="Decision", message=msg)
            progress_messages.clear()

            rec = state.decision.recommendation.value
            conf = state.decision.confidence
            yield PhaseProgress(
                phase=4, phase_name="Decision",
                message=f"✅ Phase 4 完成: {rec} (置信度 {conf:.0f}%)",
                is_complete=True, data=state.decision
            )

            # Phase 5: Signal Detection
            state.current_phase = 5
            yield PhaseProgress(
                phase=5, phase_name="Signal",
                message="📡 Phase 5: 信号检测..."
            )

            state.signal_report = self.signal_agent.extract_from_analysis(
                ticker=ticker,
                decision=state.decision,
                debate_result=state.debate_result,
                valuation_result=state.valuation_result,
                progress_callback=collect_progress,
            )

            for msg in progress_messages:
                yield PhaseProgress(phase=5, phase_name="Signal", message=msg)
            progress_messages.clear()

            strong = len(state.signal_report.strong_signals)
            medium = len(state.signal_report.medium_signals)
            yield PhaseProgress(
                phase=5, phase_name="Signal",
                message=f"✅ Phase 5 完成: 🔴{strong}个强信号 🟡{medium}个中信号",
                is_complete=True, data=state.signal_report
            )

            # Generate Scorecard & Smart Summary
            scorecard = build_scorecard(
                ticker=ticker,
                decision=state.decision,
                valuation_result=state.valuation_result,
                debate_result=state.debate_result,
                research_report=state.research_report,
            )
            state.scorecard = scorecard
            state.smart_summary = generate_smart_summary(state, scorecard)
            state.summary_json = generate_summary_json(state, scorecard)

            yield PhaseProgress(
                phase=5, phase_name="Summary",
                message=f"📊 综合评分: {scorecard.total_score:.2f}/10 — {scorecard.interpretation}"
            )

            state.mark_complete()
            yield PhaseProgress(
                phase=0, phase_name="Complete",
                message="✅ 全部分析完成!",
                is_complete=True, data=state
            )

        except Exception as e:
            state.errors.append(str(e))
            yield PhaseProgress(
                phase=state.current_phase, phase_name="Error",
                message=f"❌ 错误: {e}",
                is_complete=True, data=state
            )

        return state


# =============================================================================
# Convenience functions
# =============================================================================

def analyze(
    query: str,
    ticker: str = None,
    current_price: float = None,
    progress_callback: Callable = None
) -> WorkflowState:
    """Run complete 4-phase analysis workflow."""
    orchestrator = Orchestrator()
    return orchestrator.run(
        query, ticker=ticker, current_price=current_price,
        progress_callback=progress_callback
    )


def analyze_streaming(query: str, ticker: str = None, current_price: float = None):
    """Run analysis with streaming progress."""
    orchestrator = Orchestrator()
    return orchestrator.run_streaming(query, ticker=ticker, current_price=current_price)
