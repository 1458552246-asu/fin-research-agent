"""
Phase 2: Debate Team (3-Round Structured Debate)

Three-round debate workflow:
- Round 1: Opening arguments (Bull & Bear each present 3-5 points with evidence strength)
- Round 2: Cross-examination (each side responds to opponent's points: accept/rebut/question)
- Round 3: Position revision (accepted points + flip condition statement)
- Moderator: Weighted bull/bear ratio + key disagreements + information gaps
"""

import json
import re
from typing import List, Dict, Any, Optional, Callable

from .models import (
    DebateResult, Argument, DebateRound, DebateExchange,
    ResearchReport, SourceReference, Sentiment
)
from .prompts import (
    BULL_ANALYST_PROMPT,
    BEAR_ANALYST_PROMPT,
    DEBATE_CROSS_EXAM_PROMPT,
    DEBATE_REVISION_PROMPT,
    MODERATOR_PROMPT,
    format_key_facts_for_prompt,
    format_arguments_for_prompt,
)
from .config import Config
from .llm_client import LLMClient, LLMError


# =============================================================================
# Evidence Strength Weights (for bull/bear ratio calculation)
# =============================================================================

STRENGTH_WEIGHTS = {"strong": 3, "medium": 2, "weak": 1}


def calc_weighted_ratio(
    bull_args: List[Dict],
    bear_args: List[Dict],
    bull_rebuttals: Dict = None,
    bear_rebuttals: Dict = None,
) -> float:
    """
    Calculate weighted bull/bear ratio.

    Formula:
        ratio = bull_total_weight / (bull_total_weight + bear_total_weight)

    Weight adjustments:
        - Base: strong=3, medium=2, weak=1
        - Rebutted (opponent accepted) → weight * 0.5
        - Has quantitative data → weight * 1.3
    """
    def score_args(args: List[Dict], opponent_rebuttals: Dict) -> float:
        total = 0.0
        accepted_points = []
        if opponent_rebuttals:
            accepted_points = [
                r.get("targets", "").lower()
                for r in opponent_rebuttals.get("rebuttals", [])
                if r.get("verdict") == "accept"
            ]

        for arg in args:
            strength = arg.get("evidence_strength", arg.get("strength", "medium"))
            if isinstance(strength, (int, float)):
                # Legacy format: convert 0-1 to strong/medium/weak
                strength = "strong" if strength >= 0.8 else "medium" if strength >= 0.5 else "weak"

            weight = STRENGTH_WEIGHTS.get(strength, 2)

            # Check if rebutted
            point_lower = arg.get("point", "").lower()
            if any(point_lower in ap or ap in point_lower for ap in accepted_points if ap):
                weight *= 0.5

            # Quantitative data bonus
            evidence = arg.get("evidence", "")
            if any(c.isdigit() for c in evidence) and any(s in evidence for s in ["%", "$", "B", "M", "x"]):
                weight *= 1.3

            total += weight
        return total

    bull_score = score_args(bull_args, bear_rebuttals)
    bear_score = score_args(bear_args, bull_rebuttals)

    if bull_score + bear_score == 0:
        return 0.5
    return bull_score / (bull_score + bear_score)


# =============================================================================
# LLM Client with Mock Fallback
# =============================================================================

class DebateLLMClient:
    """LLM client for debate with mock fallback."""

    def __init__(self):
        self._client = LLMClient(temperature=0.4, max_tokens=4000)

    def chat(self, prompt: str, system: str = None) -> str:
        """Send request, fallback to mock if unavailable."""
        if not self._client.is_configured:
            return self._mock_response(prompt)

        try:
            return self._client.chat(prompt, system=system)
        except LLMError as e:
            print(f"LLM API error: {e}")
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """Return mock response based on role and company."""
        query_match = re.search(r'【用户问题】\s*\n(.+?)\n', prompt)
        query_text = query_match.group(1).lower() if query_match else prompt.lower()

        is_nvidia = any(k in query_text for k in ["nvidia", "英伟达", "nvda"])

        prompt_start = prompt[:200]
        is_bull = "看多研究员" in prompt_start or "Bull Analyst" in prompt_start
        is_bear = "看空研究员" in prompt_start or "Bear Analyst" in prompt_start
        is_cross_exam = "交叉质询" in prompt_start or "Cross" in prompt_start
        is_revision = "立场修正" in prompt_start or "Round 3" in prompt_start

        if is_revision:
            return json.dumps({
                "accepted_opponent_points": ["估值处于历史高位需要关注"],
                "revised_arguments": [
                    {"point": "AI需求确定性高，短期增速有保障", "evidence_strength": "strong", "revised_strength": 0.9},
                    {"point": "CUDA生态护城河深厚", "evidence_strength": "medium", "revised_strength": 0.8},
                ],
                "flip_condition": "若2026Q2数据中心收入环比下降>10%，或毛利率跌破65%",
                "confidence_after_debate": 0.7
            }, ensure_ascii=False)

        if is_cross_exam:
            return json.dumps({
                "rebuttals": [
                    {
                        "targets": "对方主要论点",
                        "verdict": "rebut",
                        "response": "该论点忽略了关键背景信息",
                        "counter_evidence": "最新季度数据显示趋势仍在加速",
                        "data_needed": ""
                    },
                    {
                        "targets": "对方次要论点",
                        "verdict": "accept",
                        "response": "这一点有道理，需要持续关注",
                        "counter_evidence": "",
                        "data_needed": ""
                    }
                ],
                "strengthened_arguments": ["核心增长逻辑不变"],
                "conceded_points": ["长期竞争风险确实存在"]
            }, ensure_ascii=False)

        if is_bull:
            return json.dumps({
                "opening_statement": "AI基础设施投资处于超级周期，龙头公司业绩持续超预期",
                "arguments": [
                    {
                        "point": "数据中心收入同比增长超预期",
                        "evidence": "最新季度数据中心收入同比+73%，超出市场预期15%",
                        "source": "公司财报",
                        "evidence_strength": "strong",
                        "potential_rebuttal": "高增速能否持续存疑"
                    },
                    {
                        "point": "产品供不应求，订单可见度高",
                        "evidence": "管理层明确表示供不应求状态将持续到2026年底",
                        "source": "业绩会纪要",
                        "evidence_strength": "strong",
                        "potential_rebuttal": "供应改善后需求能否跟上"
                    },
                    {
                        "point": "生态系统护城河不断加深",
                        "evidence": "开发者生态超400万，迁移成本极高",
                        "source": "行业分析",
                        "evidence_strength": "medium",
                        "potential_rebuttal": "开源替代方案在发展"
                    }
                ],
                "key_bullish_factors": ["AI Capex超级周期", "供需严重失衡", "生态护城河"]
            }, ensure_ascii=False)

        if is_bear:
            return json.dumps({
                "opening_statement": "估值已充分反映乐观预期，竞争格局长期恶化",
                "arguments": [
                    {
                        "point": "估值处于历史极高分位",
                        "evidence": "当前P/E约35x，处于5年历史90%分位",
                        "source": "市场数据",
                        "evidence_strength": "strong",
                        "potential_rebuttal": "高增速支撑高估值"
                    },
                    {
                        "point": "大客户自研芯片是结构性威胁",
                        "evidence": "Google TPU、Amazon Trainium持续迭代，性能差距缩小",
                        "source": "行业研报",
                        "evidence_strength": "medium",
                        "potential_rebuttal": "自研芯片短期难以规模化"
                    },
                    {
                        "point": "AI投资回报存疑可能导致Capex收缩",
                        "evidence": "多家企业AI项目ROI尚未明确，存在投资放缓风险",
                        "source": "专家访谈",
                        "evidence_strength": "weak",
                        "potential_rebuttal": "目前无放缓迹象"
                    }
                ],
                "key_bearish_factors": ["估值偏高", "客户自研威胁", "Capex可持续性存疑"]
            }, ensure_ascii=False)

        # Moderator
        return json.dumps({
            "bull_bear_ratio": 0.62,
            "ratio_explanation": "看多方有2个strong论点，看空方1个strong+1个medium，加权后多方占优",
            "consensus": ["AI需求短期确定性高", "供需失衡短期难解"],
            "key_disagreements": ["AI Capex持续性", "估值是否已反映预期"],
            "information_gaps": ["下季度资本开支指引数据", "自研芯片实际部署规模"],
            "flip_triggers": [
                "若Q2数据中心收入环比下降>10%，结论可能翻转为看空",
                "若毛利率跌破65%，Bear Case概率大幅上升"
            ],
            "summary": "当前多空比62:38，偏多但非一边倒。核心分歧在AI Capex持续性和估值合理性。短期基本面强劲支撑看多，但需密切关注下季度指引变化。"
        }, ensure_ascii=False)


# =============================================================================
# Debate Team (3-Round Orchestrator)
# =============================================================================

class DebateTeam:
    """
    3-Round structured debate orchestrator.

    Flow:
        Round 1: Opening → Bull & Bear present arguments
        Round 2: Cross-Exam → Each side responds to opponent (accept/rebut/question)
        Round 3: Revision → Position modification + flip conditions
        Moderator: Final verdict with weighted ratio
    """

    def __init__(self):
        self.llm = DebateLLMClient()

    def debate(
        self,
        research_report: ResearchReport,
        enable_cross_exam: bool = True,  # Now default True (3-round debate)
        progress_callback: Callable = None
    ) -> DebateResult:
        """
        Execute 3-round debate workflow.

        Args:
            research_report: Output from Research Team
            enable_cross_exam: If False, only run Round 1 + Moderator (legacy mode)
            progress_callback: Optional progress reporter

        Returns:
            DebateResult with full debate trace
        """
        query = research_report.query
        result = DebateResult(query=query)

        if progress_callback:
            progress_callback("⚔️ Phase 2: 多空辩论开始（3轮结构化辩论）...")

        # Prepare research context
        research_summary = self._format_research(research_report)
        key_facts = format_key_facts_for_prompt([
            {"content": f.content, "sentiment": f.sentiment.value}
            for f in research_report.key_facts
        ])

        # ─── Round 1: Opening Arguments ───
        if progress_callback:
            progress_callback("📢 Round 1: 开场立论...")

        bull_result = self._run_round1(query, research_summary, key_facts, "bull", progress_callback)
        bear_result = self._run_round1(query, research_summary, key_facts, "bear", progress_callback)

        result.bull_arguments = self._to_arguments(bull_result.get("arguments", []), "bull", research_report)
        result.bear_arguments = self._to_arguments(bear_result.get("arguments", []), "bear", research_report)
        result.debate_rounds.append(DebateRound(
            round_num=1, round_type="opening",
            exchanges=[
                DebateExchange(round_num=1, speaker="bull", statement=bull_result.get("opening_statement", "")),
                DebateExchange(round_num=1, speaker="bear", statement=bear_result.get("opening_statement", "")),
            ]
        ))

        # ─── Round 2: Cross-Examination ───
        bull_rebuttals = {}
        bear_rebuttals = {}

        if enable_cross_exam:
            if progress_callback:
                progress_callback("🔄 Round 2: 交叉质询...")

            bull_rebuttals = self._run_round2(
                query, bull_result, bear_result, "bull", progress_callback
            )
            bear_rebuttals = self._run_round2(
                query, bear_result, bull_result, "bear", progress_callback
            )

            result.debate_rounds.append(DebateRound(
                round_num=2, round_type="cross_examination",
                exchanges=self._rebuttals_to_exchanges(bull_rebuttals, bear_rebuttals)
            ))

            # ─── Round 3: Position Revision ───
            if progress_callback:
                progress_callback("📝 Round 3: 立场修正...")

            bull_revision = self._run_round3(
                query, bull_result, bear_rebuttals, bull_rebuttals, "bull", progress_callback
            )
            bear_revision = self._run_round3(
                query, bear_result, bull_rebuttals, bear_rebuttals, "bear", progress_callback
            )

            result.debate_rounds.append(DebateRound(
                round_num=3, round_type="revision",
                exchanges=[
                    DebateExchange(
                        round_num=3, speaker="bull",
                        statement=f"条件反转：{bull_revision.get('flip_condition', 'N/A')}"
                    ),
                    DebateExchange(
                        round_num=3, speaker="bear",
                        statement=f"条件反转：{bear_revision.get('flip_condition', 'N/A')}"
                    ),
                ]
            ))

        # ─── Moderator Verdict ───
        if progress_callback:
            progress_callback("⚖️ Moderator: 综合评判...")

        moderator_result = self._run_moderator(
            query, bull_result, bear_result,
            bull_rebuttals, bear_rebuttals,
            bull_revision if enable_cross_exam else {},
            bear_revision if enable_cross_exam else {},
            progress_callback
        )

        # Fill result
        result.consensus = moderator_result.get("consensus", [])
        result.disputes = moderator_result.get("key_disagreements", moderator_result.get("disputes", []))
        result.bull_bear_ratio = moderator_result.get("bull_bear_ratio", 0.5)
        result.moderator_summary = moderator_result.get("summary", "")

        # Store extra fields for downstream use
        result.information_gaps = moderator_result.get("information_gaps", [])
        result.flip_triggers = moderator_result.get("flip_triggers", [])

        if progress_callback:
            ratio = result.bull_bear_ratio
            pct = f"{ratio:.0%}:{1-ratio:.0%}"
            progress_callback(f"✅ Phase 2 完成: 多空比 {pct}")

        return result

    # ─── Round Implementations ───

    def _run_round1(
        self, query: str, research_summary: str, key_facts: str,
        side: str, progress_callback: Callable = None
    ) -> Dict:
        """Round 1: Generate opening arguments."""
        template = BULL_ANALYST_PROMPT if side == "bull" else BEAR_ANALYST_PROMPT
        prompt = template.format(
            query=query, research_summary=research_summary, key_facts=key_facts
        )
        response = self.llm.chat(prompt)
        result = self._parse_json(response)

        if progress_callback:
            n = len(result.get("arguments", []))
            label = "🐂 看多" if side == "bull" else "🐻 看空"
            progress_callback(f"  {label}方提出 {n} 个论点")

        return result

    def _run_round2(
        self, query: str, my_result: Dict, opponent_result: Dict,
        side: str, progress_callback: Callable = None
    ) -> Dict:
        """Round 2: Cross-examine opponent's arguments."""
        role = "看多研究员" if side == "bull" else "看空研究员"
        role_desc = "Bull Analyst" if side == "bull" else "Bear Analyst"
        opponent_role = "看空研究员" if side == "bull" else "看多研究员"

        prompt = DEBATE_CROSS_EXAM_PROMPT.format(
            role=role,
            role_description=role_desc,
            opponent_role=opponent_role,
            opponent_arguments=format_arguments_for_prompt(opponent_result.get("arguments", [])),
            your_arguments=format_arguments_for_prompt(my_result.get("arguments", []))
        )
        response = self.llm.chat(prompt)
        result = self._parse_json(response)

        if progress_callback:
            rebuttals = result.get("rebuttals", [])
            accepts = sum(1 for r in rebuttals if r.get("verdict") == "accept")
            rebuts = sum(1 for r in rebuttals if r.get("verdict") == "rebut")
            label = "🐂" if side == "bull" else "🐻"
            progress_callback(f"  {label} 质询完成: 反驳{rebuts}条, 接受{accepts}条")

        return result

    def _run_round3(
        self, query: str, my_result: Dict,
        opponent_rebuttals_to_me: Dict, my_rebuttals_to_opponent: Dict,
        side: str, progress_callback: Callable = None
    ) -> Dict:
        """Round 3: Revise position based on cross-examination."""
        role = "看多研究员" if side == "bull" else "看空研究员"
        role_desc = "Bull Analyst" if side == "bull" else "Bear Analyst"

        prompt = DEBATE_REVISION_PROMPT.format(
            role=role,
            role_description=role_desc,
            your_arguments=format_arguments_for_prompt(my_result.get("arguments", [])),
            opponent_rebuttals=json.dumps(opponent_rebuttals_to_me, ensure_ascii=False, indent=2),
            your_rebuttals=json.dumps(my_rebuttals_to_opponent, ensure_ascii=False, indent=2)
        )
        response = self.llm.chat(prompt)
        result = self._parse_json(response)

        if progress_callback:
            flip = result.get("flip_condition", "未声明")
            label = "🐂" if side == "bull" else "🐻"
            progress_callback(f"  {label} 立场修正完成，反转条件：{flip[:50]}...")

        return result

    def _run_moderator(
        self, query: str,
        bull_result: Dict, bear_result: Dict,
        bull_rebuttals: Dict, bear_rebuttals: Dict,
        bull_revision: Dict, bear_revision: Dict,
        progress_callback: Callable = None
    ) -> Dict:
        """Moderator: Final verdict with weighted ratio."""
        # Format arguments with strength info
        bull_args_str = self._format_args_with_strength(bull_result.get("arguments", []))
        bear_args_str = self._format_args_with_strength(bear_result.get("arguments", []))

        cross_exam_str = json.dumps({
            "bull_cross_exam": bull_rebuttals,
            "bear_cross_exam": bear_rebuttals
        }, ensure_ascii=False, indent=2) if bull_rebuttals else "（未进行交叉质询）"

        revision_str = json.dumps({
            "bull_revision": bull_revision,
            "bear_revision": bear_revision
        }, ensure_ascii=False, indent=2) if bull_revision else "（未进行立场修正）"

        prompt = MODERATOR_PROMPT.format(
            query=query,
            bull_arguments=bull_args_str,
            bear_arguments=bear_args_str,
            cross_exam_results=cross_exam_str,
            revision_results=revision_str
        )
        response = self.llm.chat(prompt)
        result = self._parse_json(response)

        # Also compute our own ratio as a sanity check
        computed_ratio = calc_weighted_ratio(
            bull_result.get("arguments", []),
            bear_result.get("arguments", []),
            bull_rebuttals,
            bear_rebuttals
        )
        # Use LLM ratio if available, fallback to computed
        if "bull_bear_ratio" not in result:
            result["bull_bear_ratio"] = computed_ratio

        if progress_callback:
            ratio = result.get("bull_bear_ratio", 0.5)
            progress_callback(f"  ⚖️ 最终多空比: {ratio:.0%}:{1-ratio:.0%}")

        return result

    # ─── Helpers ───

    def _format_research(self, report: ResearchReport) -> str:
        """Format research report as summary text."""
        parts = []
        for sg in report.sources:
            if sg.findings:
                parts.append(f"【{sg.source_name}】")
                for f in sg.findings[:5]:
                    parts.append(f"  • {f}")
        return "\n".join(parts) if parts else "（无研究数据）"

    def _format_args_with_strength(self, args: List[Dict]) -> str:
        """Format arguments including evidence_strength for moderator."""
        lines = []
        for i, arg in enumerate(args, 1):
            strength = arg.get("evidence_strength", "medium")
            point = arg.get("point", "")
            evidence = arg.get("evidence", "")
            lines.append(f"{i}. [{strength}] {point}")
            if evidence:
                lines.append(f"   证据: {evidence}")
        return "\n".join(lines) if lines else "（无论点）"

    def _to_arguments(self, arg_list: List[Dict], side: str, research_report: ResearchReport = None) -> List[Argument]:
        """Convert dict list to Argument model objects, matching sources to KB documents."""
        # Build lookup of raw documents from research report for source tracing
        raw_docs = []
        if research_report:
            for sg in research_report.sources:
                for doc in sg.raw_documents:
                    if doc.get("file_id"):
                        raw_docs.append(doc)

        arguments = []
        for arg in arg_list:
            if not isinstance(arg, dict):
                continue
            # Map evidence_strength to numeric strength
            es = arg.get("evidence_strength", "medium")
            strength_map = {"strong": 0.9, "medium": 0.7, "weak": 0.4}
            strength = strength_map.get(es, 0.7)

            source_ref = None
            if arg.get("source"):
                # Try to match argument source text to a real KB document
                matched_doc = self._match_source_to_doc(arg.get("source", ""), arg.get("evidence", ""), raw_docs)
                if matched_doc:
                    source_ref = SourceReference(
                        source_type=matched_doc.get("source_type", side),
                        title=matched_doc.get("title", matched_doc.get("file_name", arg["source"])),
                        date=matched_doc.get("date", ""),
                        file_id=matched_doc.get("file_id"),
                        preview=matched_doc.get("content", arg.get("evidence", ""))[:500]
                    )
                else:
                    source_ref = SourceReference(
                        source_type=side,
                        title=arg["source"],
                        preview=arg.get("evidence", "")
                    )

            arguments.append(Argument(
                point=arg.get("point", ""),
                evidence=arg.get("evidence", ""),
                source=source_ref,
                strength=strength,
                rebuttal=arg.get("potential_rebuttal")
            ))
        return arguments

    def _match_source_to_doc(self, source_text: str, evidence: str, raw_docs: List[Dict]) -> Optional[Dict]:
        """Try to match an argument's source description to a real KB document.

        Matching strategy:
        1. Keyword overlap between source_text/evidence and document content/title
        2. Source type keyword matching (e.g. "财报" → AlphaEngine, "专家" → 专家访谈)
        """
        if not raw_docs:
            return None

        source_lower = source_text.lower()
        evidence_lower = evidence.lower()

        # Source type keyword mapping
        type_keywords = {
            "专家访谈": ["专家", "访谈", "调研", "expert"],
            "AlphaEngine": ["财报", "研报", "report", "earnings", "alpha", "业绩"],
            "Twitter推文": ["twitter", "推特", "tweet"],
            "Substack": ["substack", "newsletter"],
            "AceCampTech": ["acecamp", "ace"],
        }

        # Find best matching document
        best_doc = None
        best_score = 0

        for doc in raw_docs:
            score = 0
            doc_type = doc.get("source_type", "")
            doc_title = (doc.get("title", "") or doc.get("file_name", "")).lower()
            doc_content = (doc.get("content", ""))[:500].lower()

            # Check source type keyword match
            for stype, keywords in type_keywords.items():
                if any(kw in source_lower for kw in keywords):
                    if doc_type == stype or stype.lower() in doc_type.lower():
                        score += 3
                    break

            # Check title/content overlap with evidence
            evidence_words = [w for w in evidence_lower.split() if len(w) > 2]
            for word in evidence_words[:10]:
                if word in doc_content or word in doc_title:
                    score += 1

            if score > best_score:
                best_score = score
                best_doc = doc

        # Only return if we have a reasonable match (score >= 2)
        if best_score >= 2 and best_doc:
            return best_doc
        return None

    def _rebuttals_to_exchanges(self, bull_rebuttals: Dict, bear_rebuttals: Dict) -> List[DebateExchange]:
        """Convert rebuttals to DebateExchange list."""
        exchanges = []
        for r in bull_rebuttals.get("rebuttals", []):
            exchanges.append(DebateExchange(
                round_num=2, speaker="bull", is_rebuttal=True,
                statement=f"[{r.get('verdict', '?')}] {r.get('targets', '')}: {r.get('response', '')}",
                targets_argument=r.get("targets")
            ))
        for r in bear_rebuttals.get("rebuttals", []):
            exchanges.append(DebateExchange(
                round_num=2, speaker="bear", is_rebuttal=True,
                statement=f"[{r.get('verdict', '?')}] {r.get('targets', '')}: {r.get('response', '')}",
                targets_argument=r.get("targets")
            ))
        return exchanges

    def _parse_json(self, response: str) -> Dict:
        """Parse JSON from LLM response."""
        try:
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                return json.loads(match.group())
        except json.JSONDecodeError:
            pass
        return {}


# =============================================================================
# Convenience function
# =============================================================================

def run_debate(
    research_report: ResearchReport,
    enable_cross_exam: bool = True,
    progress_callback: Callable = None
) -> DebateResult:
    """Run 3-round debate workflow."""
    team = DebateTeam()
    return team.debate(research_report, enable_cross_exam, progress_callback)
