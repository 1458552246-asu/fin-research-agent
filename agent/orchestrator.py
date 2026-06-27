"""
Orchestrator - Coordinates the multi-agent workflow.

Manages the three-phase pipeline:
1. Research Team (information gathering)
2. Debate Team (bull vs bear analysis)
3. Decision Agent (final recommendation)
"""

from typing import Optional, Callable, Generator, Tuple
from dataclasses import dataclass
from datetime import datetime

from .models import (
    WorkflowState, ResearchReport, DebateResult, Decision
)
from .research_team import ResearchTeam
from .debate_team import DebateTeam
from .decision_agent import DecisionAgent
from .config import Config


@dataclass
class PhaseProgress:
    """Progress update from a workflow phase."""
    phase: int                # 1, 2, or 3
    phase_name: str           # "Research", "Debate", "Decision"
    message: str              # Progress message
    is_complete: bool = False # Whether phase is complete
    data: Optional[any] = None  # Phase output data


class Orchestrator:
    """
    Coordinates the multi-agent financial research workflow.

    Usage:
        orchestrator = Orchestrator()

        # Option 1: Run complete workflow
        result = orchestrator.run(query)

        # Option 2: Stream progress updates
        for progress in orchestrator.run_streaming(query):
            print(progress.message)
    """

    def __init__(self):
        self.research_team = ResearchTeam()
        self.debate_team = DebateTeam()
        self.decision_agent = DecisionAgent()

    def run(
        self,
        query: str,
        enable_cross_exam: bool = False,
        progress_callback: Callable[[str], None] = None
    ) -> WorkflowState:
        """
        Run complete workflow and return final state.

        Args:
            query: User's research question
            enable_cross_exam: Whether to include debate cross-examination
            progress_callback: Optional callback for progress updates

        Returns:
            WorkflowState with all phase outputs
        """
        state = WorkflowState(query=query)

        try:
            # Phase 1: Research
            state.current_phase = 1
            if progress_callback:
                progress_callback("📋 Phase 1: 研究团队开始收集信息...")

            state.research_report = self.research_team.research(
                query, progress_callback
            )

            # Phase 2: Debate
            state.current_phase = 2
            if progress_callback:
                progress_callback("⚔️ Phase 2: 多空辩论开始...")

            state.debate_result = self.debate_team.debate(
                state.research_report,
                enable_cross_exam=enable_cross_exam,
                progress_callback=progress_callback
            )

            # Phase 3: Decision
            state.current_phase = 3
            if progress_callback:
                progress_callback("📈 Phase 3: 生成投资建议...")

            state.decision = self.decision_agent.decide(
                state.research_report,
                state.debate_result,
                progress_callback
            )

            state.mark_complete()
            if progress_callback:
                progress_callback("✅ 分析完成!")

        except Exception as e:
            state.errors.append(str(e))
            if progress_callback:
                progress_callback(f"❌ 错误: {e}")

        return state

    def run_streaming(
        self,
        query: str,
        enable_cross_exam: bool = False
    ) -> Generator[PhaseProgress, None, WorkflowState]:
        """
        Run workflow with streaming progress updates.

        Yields PhaseProgress objects for UI updates.
        Returns final WorkflowState.

        Usage:
            for progress in orchestrator.run_streaming(query):
                update_ui(progress)
            final_state = progress.data  # Last progress contains final state
        """
        state = WorkflowState(query=query)
        progress_messages = []

        def collect_progress(msg: str):
            progress_messages.append(msg)

        try:
            # Phase 1: Research
            state.current_phase = 1
            yield PhaseProgress(
                phase=1,
                phase_name="Research",
                message="📋 Phase 1: 研究团队开始收集信息..."
            )

            state.research_report = self.research_team.research(
                query, collect_progress
            )

            for msg in progress_messages:
                yield PhaseProgress(phase=1, phase_name="Research", message=msg)
            progress_messages.clear()

            yield PhaseProgress(
                phase=1,
                phase_name="Research",
                message=f"✅ Phase 1 完成: 收集了 {state.research_report.total_sources_found} 条信息",
                is_complete=True,
                data=state.research_report
            )

            # Phase 2: Debate
            state.current_phase = 2
            yield PhaseProgress(
                phase=2,
                phase_name="Debate",
                message="⚔️ Phase 2: 多空辩论开始..."
            )

            state.debate_result = self.debate_team.debate(
                state.research_report,
                enable_cross_exam=enable_cross_exam,
                progress_callback=collect_progress
            )

            for msg in progress_messages:
                yield PhaseProgress(phase=2, phase_name="Debate", message=msg)
            progress_messages.clear()

            ratio = state.debate_result.bull_bear_ratio
            stance = "偏多" if ratio > 0.55 else "偏空" if ratio < 0.45 else "中性"
            yield PhaseProgress(
                phase=2,
                phase_name="Debate",
                message=f"✅ Phase 2 完成: 多空比 {ratio:.0%}, 结论 {stance}",
                is_complete=True,
                data=state.debate_result
            )

            # Phase 3: Decision
            state.current_phase = 3
            yield PhaseProgress(
                phase=3,
                phase_name="Decision",
                message="📈 Phase 3: 生成投资建议..."
            )

            state.decision = self.decision_agent.decide(
                state.research_report,
                state.debate_result,
                collect_progress
            )

            for msg in progress_messages:
                yield PhaseProgress(phase=3, phase_name="Decision", message=msg)
            progress_messages.clear()

            rec = state.decision.recommendation.value
            conf = state.decision.confidence
            yield PhaseProgress(
                phase=3,
                phase_name="Decision",
                message=f"✅ Phase 3 完成: 建议 {rec} (置信度 {conf:.0f}%)",
                is_complete=True,
                data=state.decision
            )

            state.mark_complete()

            # Final state
            yield PhaseProgress(
                phase=0,
                phase_name="Complete",
                message="✅ 分析完成!",
                is_complete=True,
                data=state
            )

        except Exception as e:
            state.errors.append(str(e))
            yield PhaseProgress(
                phase=state.current_phase,
                phase_name="Error",
                message=f"❌ 错误: {e}",
                is_complete=True,
                data=state
            )

        return state

    def run_phase_by_phase(
        self,
        query: str,
        enable_cross_exam: bool = False
    ) -> Tuple[ResearchReport, DebateResult, Decision]:
        """
        Run workflow and return each phase's output separately.

        Returns:
            Tuple of (ResearchReport, DebateResult, Decision)
        """
        # Phase 1
        research_report = self.research_team.research(query)

        # Phase 2
        debate_result = self.debate_team.debate(
            research_report,
            enable_cross_exam=enable_cross_exam
        )

        # Phase 3
        decision = self.decision_agent.decide(
            research_report,
            debate_result
        )

        return research_report, debate_result, decision


# Convenience functions
def analyze(
    query: str,
    progress_callback: Callable = None
) -> WorkflowState:
    """Run complete analysis workflow."""
    orchestrator = Orchestrator()
    return orchestrator.run(query, progress_callback=progress_callback)


def analyze_streaming(query: str):
    """Run analysis with streaming progress."""
    orchestrator = Orchestrator()
    return orchestrator.run_streaming(query)
