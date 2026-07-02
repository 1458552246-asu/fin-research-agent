"""
Phase 3 (New): Valuation Agent

Relative valuation + scenario analysis (replaces DCF which requires too much forward data).

Components:
- Analyst consensus (target prices, rating distribution)
- Relative valuation (P/E, EV/EBITDA vs peers vs historical)
- Three-scenario pricing (Bull/Base/Bear with probability weights)
- Margin of safety calculation
"""

import json
import re
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class AnalystConsensus:
    """Analyst consensus data."""
    median_target: Optional[float] = None
    target_range_low: Optional[float] = None
    target_range_high: Optional[float] = None
    buy_count: int = 0
    hold_count: int = 0
    sell_count: int = 0

    @property
    def total_analysts(self) -> int:
        return self.buy_count + self.hold_count + self.sell_count


@dataclass
class RelativeValuation:
    """Relative valuation metrics."""
    current_pe: Optional[float] = None
    industry_pe: Optional[float] = None
    historical_pe_low: Optional[float] = None
    historical_pe_high: Optional[float] = None
    pe_percentile: Optional[float] = None  # 0-100, current position in 5yr range

    ev_ebitda: Optional[float] = None
    industry_ev_ebitda: Optional[float] = None

    ps_ratio: Optional[float] = None
    industry_ps: Optional[float] = None

    @property
    def pe_vs_industry(self) -> Optional[str]:
        if self.current_pe and self.industry_pe:
            diff = (self.current_pe / self.industry_pe - 1) * 100
            if diff > 20:
                return "偏贵"
            elif diff < -20:
                return "偏便宜"
            return "合理"
        return None


@dataclass
class ScenarioTarget:
    """Single scenario price target."""
    label: str           # "Bull" / "Base" / "Bear"
    target_price: float
    upside_pct: float    # vs current price
    premise: str         # Key assumption for this scenario
    probability: float   # Probability weight (0-1)


@dataclass
class ValuationResult:
    """Complete valuation output."""
    ticker: str
    current_price: Optional[float] = None
    consensus: Optional[AnalystConsensus] = None
    relative_valuation: Optional[RelativeValuation] = None
    scenarios: List[ScenarioTarget] = field(default_factory=list)
    weighted_target: Optional[float] = None
    margin_of_safety: Optional[str] = None  # Qualitative assessment
    key_assumptions: List[Dict] = field(default_factory=list)
    flip_triggers: List[str] = field(default_factory=list)

    @property
    def weighted_upside(self) -> Optional[float]:
        if self.weighted_target and self.current_price:
            return (self.weighted_target / self.current_price - 1) * 100
        return None


# =============================================================================
# Valuation Prompts
# =============================================================================

VALUATION_PROMPT = """你是一位估值分析师，负责基于辩论结论和市场数据进行相对估值和情景分析。

【标的】{ticker}
【当前价格】{current_price}（如未知标注"未知"）

【辩论结论摘要】
- 多空比：{bull_bear_ratio}
- 看多核心论点：{bull_summary}
- 看空核心论点：{bear_summary}
- 关键分歧：{key_disagreements}
- 条件反转触发：{flip_triggers}

【研究数据摘要】
{research_summary}

【任务】
1. 估算分析师一致预期（基于研报数据或WebSearch结果）
2. 相对估值分析（P/E、EV/EBITDA 与行业和历史比较）
3. 构建三情景目标价（Bull/Base/Bear），每个情景需：
   - 具体前提条件
   - 目标价和相对当前价涨跌幅
   - 概率权重（三者之和=100%）
4. 计算加权目标价和安全边际
5. 提取关键假设

【输出格式 - JSON】
{{
    "current_price": 850,
    "consensus": {{
        "median_target": 950,
        "target_range_low": 650,
        "target_range_high": 1200,
        "buy_count": 38,
        "hold_count": 8,
        "sell_count": 2
    }},
    "relative_valuation": {{
        "current_pe": 65,
        "industry_pe": 45,
        "historical_pe_low": 25,
        "historical_pe_high": 90,
        "pe_percentile": 78,
        "ev_ebitda": 52,
        "industry_ev_ebitda": 30,
        "ps_ratio": 28,
        "industry_ps": 12
    }},
    "scenarios": [
        {{
            "label": "Bull",
            "target_price": 1100,
            "upside_pct": 29,
            "premise": "AI Capex持续加速，数据中心收入YoY>50%",
            "probability": 30
        }},
        {{
            "label": "Base",
            "target_price": 900,
            "upside_pct": 6,
            "premise": "AI投资温和增长，数据中心收入YoY 30-40%",
            "probability": 50
        }},
        {{
            "label": "Bear",
            "target_price": 650,
            "upside_pct": -24,
            "premise": "企业IT支出收缩，竞争加剧",
            "probability": 20
        }}
    ],
    "key_assumptions": [
        {{"assumption": "AI Capex增速维持30%+", "confidence": "high"}},
        {{"assumption": "GPU市占率>80%", "confidence": "medium"}},
        {{"assumption": "毛利率维持70%+", "confidence": "low"}}
    ]
}}"""


# =============================================================================
# Valuation Agent
# =============================================================================

class ValuationAgent:
    """
    Relative valuation + scenario analysis agent.

    Does NOT do DCF (requires forward financial projections that WebSearch can't support).
    Instead: analyst consensus + relative multiples + 3-scenario pricing.
    """

    def __init__(self):
        from .llm_client import LLMClient, LLMError
        self._client = LLMClient(temperature=0.2, max_tokens=4000)
        self._LLMError = LLMError

    def evaluate(
        self,
        ticker: str,
        debate_result,  # DebateResult
        research_report,  # ResearchReport
        current_price: Optional[float] = None,
        progress_callback: Callable = None,
    ) -> ValuationResult:
        """
        Run valuation analysis.

        Args:
            ticker: Stock ticker symbol
            debate_result: Output from debate phase
            research_report: Output from research phase
            current_price: Current stock price (if known)
            progress_callback: Progress reporter

        Returns:
            ValuationResult with scenarios and margin of safety
        """
        if progress_callback:
            progress_callback("💰 估值分析开始...")

        # Build prompt context
        bull_summary = ", ".join(
            arg.point for arg in debate_result.bull_arguments[:3]
        ) if debate_result.bull_arguments else "N/A"

        bear_summary = ", ".join(
            arg.point for arg in debate_result.bear_arguments[:3]
        ) if debate_result.bear_arguments else "N/A"

        research_summary = self._format_research(research_report)

        prompt = VALUATION_PROMPT.format(
            ticker=ticker,
            current_price=current_price or "未知",
            bull_bear_ratio=f"{debate_result.bull_bear_ratio:.0%}",
            bull_summary=bull_summary,
            bear_summary=bear_summary,
            key_disagreements=", ".join(debate_result.disputes[:3]) or "无",
            flip_triggers=", ".join(debate_result.flip_triggers[:2]) or "无",
            research_summary=research_summary,
        )

        if progress_callback:
            progress_callback("  📊 计算相对估值...")

        # Call LLM or use mock
        raw = self._call_llm(prompt)
        data = self._parse_json(raw)

        if progress_callback:
            progress_callback("  🎯 构建三情景目标价...")

        # Build result
        result = self._build_result(ticker, data, debate_result)

        if progress_callback:
            if result.weighted_target:
                progress_callback(
                    f"✅ 估值完成: 加权目标价 ${result.weighted_target:.0f}"
                    f" ({'+'if result.weighted_upside and result.weighted_upside > 0 else ''}"
                    f"{result.weighted_upside:.1f}%)"
                )
            else:
                progress_callback("✅ 估值完成")

        return result

    def _call_llm(self, prompt: str) -> str:
        """Call LLM with fallback to mock."""
        if not self._client.is_configured:
            return self._mock_response(prompt)
        try:
            return self._client.chat(prompt)
        except self._LLMError as e:
            print(f"Valuation LLM error: {e}")
            return self._mock_response(prompt)

    def _build_result(self, ticker: str, data: Dict, debate_result) -> ValuationResult:
        """Build ValuationResult from parsed LLM output."""
        # Consensus
        consensus = None
        if data.get("consensus"):
            c = data["consensus"]
            consensus = AnalystConsensus(
                median_target=c.get("median_target"),
                target_range_low=c.get("target_range_low"),
                target_range_high=c.get("target_range_high"),
                buy_count=c.get("buy_count", 0),
                hold_count=c.get("hold_count", 0),
                sell_count=c.get("sell_count", 0),
            )

        # Relative valuation
        rel_val = None
        if data.get("relative_valuation"):
            rv = data["relative_valuation"]
            rel_val = RelativeValuation(
                current_pe=rv.get("current_pe"),
                industry_pe=rv.get("industry_pe"),
                historical_pe_low=rv.get("historical_pe_low"),
                historical_pe_high=rv.get("historical_pe_high"),
                pe_percentile=rv.get("pe_percentile"),
                ev_ebitda=rv.get("ev_ebitda"),
                industry_ev_ebitda=rv.get("industry_ev_ebitda"),
                ps_ratio=rv.get("ps_ratio"),
                industry_ps=rv.get("industry_ps"),
            )

        # Scenarios
        scenarios = []
        for s in data.get("scenarios", []):
            scenarios.append(ScenarioTarget(
                label=s.get("label", "?"),
                target_price=s.get("target_price", 0),
                upside_pct=s.get("upside_pct", 0),
                premise=s.get("premise", ""),
                probability=s.get("probability", 0) / 100,  # Convert to 0-1
            ))

        # Weighted target
        current_price = data.get("current_price")
        weighted_target = None
        if scenarios:
            weighted_target = sum(
                s.target_price * s.probability for s in scenarios
            )

        # Margin of safety assessment
        margin_of_safety = None
        if current_price and scenarios:
            bear_case = next((s for s in scenarios if s.label == "Bear"), None)
            if bear_case:
                bear_distance = (current_price - bear_case.target_price) / current_price * 100
                if bear_distance > 25:
                    margin_of_safety = f"距Bear Case {bear_distance:.0f}%，风险偏高"
                elif bear_distance > 10:
                    margin_of_safety = f"距Bear Case {bear_distance:.0f}%，风险适中"
                else:
                    margin_of_safety = f"距Bear Case仅{bear_distance:.0f}%，安全边际不足"

        return ValuationResult(
            ticker=ticker,
            current_price=current_price,
            consensus=consensus,
            relative_valuation=rel_val,
            scenarios=scenarios,
            weighted_target=weighted_target,
            margin_of_safety=margin_of_safety,
            key_assumptions=data.get("key_assumptions", []),
            flip_triggers=debate_result.flip_triggers if debate_result else [],
        )

    def _format_research(self, report) -> str:
        """Format research report summary for valuation context."""
        parts = []
        for sg in report.sources:
            if sg.findings:
                parts.append(f"【{sg.source_name}】")
                for f in sg.findings[:3]:
                    parts.append(f"  • {f}")
        return "\n".join(parts) if parts else "（无研究数据）"

    def _parse_json(self, response: str) -> Dict:
        """Parse JSON from LLM response."""
        try:
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                return json.loads(match.group())
        except json.JSONDecodeError:
            pass
        return {}

    def _mock_response(self, prompt: str) -> str:
        """Mock valuation response."""
        # Detect ticker from prompt
        ticker_match = re.search(r'【标的】\s*(\S+)', prompt)
        ticker = ticker_match.group(1) if ticker_match else "UNKNOWN"

        if "nvda" in ticker.lower() or "nvidia" in ticker.lower():
            return json.dumps({
                "current_price": 850,
                "consensus": {
                    "median_target": 950,
                    "target_range_low": 650,
                    "target_range_high": 1200,
                    "buy_count": 38,
                    "hold_count": 8,
                    "sell_count": 2
                },
                "relative_valuation": {
                    "current_pe": 65,
                    "industry_pe": 45,
                    "historical_pe_low": 25,
                    "historical_pe_high": 90,
                    "pe_percentile": 78,
                    "ev_ebitda": 52,
                    "industry_ev_ebitda": 30,
                    "ps_ratio": 28,
                    "industry_ps": 12
                },
                "scenarios": [
                    {
                        "label": "Bull",
                        "target_price": 1100,
                        "upside_pct": 29,
                        "premise": "AI Capex持续加速，数据中心收入YoY>50%",
                        "probability": 30
                    },
                    {
                        "label": "Base",
                        "target_price": 900,
                        "upside_pct": 6,
                        "premise": "AI投资温和增长，数据中心收入YoY 30-40%",
                        "probability": 50
                    },
                    {
                        "label": "Bear",
                        "target_price": 650,
                        "upside_pct": -24,
                        "premise": "企业IT支出收缩，竞争加剧（AMD/自研芯片）",
                        "probability": 20
                    }
                ],
                "key_assumptions": [
                    {"assumption": "AI Capex增速维持30%+", "confidence": "high"},
                    {"assumption": "GPU市占率>80%", "confidence": "medium"},
                    {"assumption": "毛利率维持70%+", "confidence": "low"}
                ]
            }, ensure_ascii=False)

        # Generic fallback
        return json.dumps({
            "current_price": 100,
            "consensus": {
                "median_target": 115,
                "target_range_low": 80,
                "target_range_high": 140,
                "buy_count": 12,
                "hold_count": 5,
                "sell_count": 2
            },
            "relative_valuation": {
                "current_pe": 25,
                "industry_pe": 20,
                "historical_pe_low": 12,
                "historical_pe_high": 35,
                "pe_percentile": 65,
                "ev_ebitda": 18,
                "industry_ev_ebitda": 14,
                "ps_ratio": 5,
                "industry_ps": 3
            },
            "scenarios": [
                {
                    "label": "Bull",
                    "target_price": 140,
                    "upside_pct": 40,
                    "premise": "核心业务加速增长，新催化剂兑现",
                    "probability": 25
                },
                {
                    "label": "Base",
                    "target_price": 115,
                    "upside_pct": 15,
                    "premise": "业务稳健增长，估值小幅修复",
                    "probability": 50
                },
                {
                    "label": "Bear",
                    "target_price": 80,
                    "upside_pct": -20,
                    "premise": "增速放缓，行业竞争加剧",
                    "probability": 25
                }
            ],
            "key_assumptions": [
                {"assumption": "收入增速维持15%+", "confidence": "medium"},
                {"assumption": "毛利率稳定", "confidence": "medium"}
            ]
        }, ensure_ascii=False)
