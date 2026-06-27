"""
Phase 3: Decision Agent

Synthesizes research and debate results to produce final investment recommendation.
"""

import json
import re
from typing import List, Dict, Any, Optional, Callable

from .models import (
    Decision, Recommendation, PriceTarget, TrackingMetric,
    ResearchReport, DebateResult, Sentiment
)
from .prompts import DECISION_AGENT_PROMPT, PRICE_TARGET_PROMPT
from .config import Config


class LLMClient:
    """Simple LLM client for decision prompts."""

    def __init__(self):
        self.api_key = Config.LLM_API_KEY
        self.base_url = Config.LLM_BASE_URL
        self.model = Config.LLM_MODEL

    def chat(self, prompt: str, system: str = None) -> str:
        """Send a chat completion request."""
        if not self.api_key:
            return self._mock_response(prompt)

        try:
            import openai
            import httpx
            # Create custom httpx client to avoid 'proxies' parameter issue with httpx 0.28+
            http_client = httpx.Client(timeout=60.0)
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                http_client=http_client
            )

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,  # Lower temperature for consistent decisions
                max_tokens=3000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM API error: {e}")
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """Return mock response when API unavailable."""
        return json.dumps({
            "recommendation": "持有",
            "confidence": 65,
            "rationale": "AI服务器业务增长强劲，但毛利率压力和竞争加剧带来不确定性。建议等待更多数据验证。",
            "key_risks": ["GPU服务器毛利率持续低迷", "NVIDIA供货分配不确定", "传统业务下滑超预期"],
            "catalysts": ["FY26 Q2毛利率改善", "新企业AI订单公告", "GB200出货超预期"],
            "tracking_metrics": [
                {"metric": "AI服务器毛利率", "direction": "上升", "importance": "high"},
                {"metric": "订单积压金额", "direction": "稳定", "importance": "high"}
            ],
            "time_horizon": "中期",
            "thesis_summary": "Dell正处于AI转型关键期。AI服务器业务增长强劲但毛利率承压，传统业务持续下滑。短期内收入质量与增长速度的权衡是主要矛盾。建议关注毛利率趋势和竞争格局变化。"
        }, ensure_ascii=False)


class DecisionAgent:
    """
    Makes final investment decisions based on research and debate.

    Responsibilities:
    - Synthesize research findings and debate conclusions
    - Calculate confidence based on data quality and consensus
    - Generate actionable recommendations with risk/catalyst analysis
    """

    def __init__(self):
        self.name = "投资决策Agent"
        self.llm = LLMClient()

    def decide(
        self,
        research_report: ResearchReport,
        debate_result: DebateResult,
        progress_callback: Callable = None
    ) -> Decision:
        """
        Generate investment decision.

        Args:
            research_report: Output from Research Team
            debate_result: Output from Debate Team
            progress_callback: Optional function to report progress

        Returns:
            Decision with recommendation, confidence, risks, and catalysts
        """
        query = research_report.query

        if progress_callback:
            progress_callback("📈 Phase 3: 生成投资建议...")

        # Prepare inputs for decision prompt
        research_key_facts = self._format_key_facts(research_report)
        bull_summary = self._format_bull_summary(debate_result)
        bear_summary = self._format_bear_summary(debate_result)

        prompt = DECISION_AGENT_PROMPT.format(
            query=query,
            research_key_facts=research_key_facts,
            bull_summary=bull_summary,
            bear_summary=bear_summary,
            consensus=", ".join(debate_result.consensus) or "无明确共识",
            disputes=", ".join(debate_result.disputes) or "无重大分歧",
            bull_bear_ratio=f"{debate_result.bull_bear_ratio:.2f}"
        )

        if progress_callback:
            progress_callback("🤖 分析中...")

        response = self.llm.chat(prompt)
        result = self._parse_response(response)

        # Adjust confidence based on data quality
        base_confidence = result.get("confidence", 50)
        adjusted_confidence = self._adjust_confidence(
            base_confidence, research_report, debate_result
        )
        result["confidence"] = adjusted_confidence

        # Convert to Decision object
        decision = self._build_decision(query, result)

        if progress_callback:
            rec = decision.recommendation.value
            conf = decision.confidence
            progress_callback(f"✅ Phase 3 完成: 建议 {rec} (置信度 {conf:.0f}%)")

        return decision

    def _format_key_facts(self, report: ResearchReport) -> str:
        """Format research key facts for prompt."""
        lines = []
        for i, fact in enumerate(report.key_facts[:10], 1):
            emoji = {
                Sentiment.POSITIVE: "📈",
                Sentiment.NEGATIVE: "📉",
                Sentiment.NEUTRAL: "➖"
            }.get(fact.sentiment, "")
            lines.append(f"{i}. {emoji} {fact.content}")
        return "\n".join(lines) if lines else "无关键事实"

    def _format_bull_summary(self, debate: DebateResult) -> str:
        """Format bull arguments summary."""
        if not debate.bull_arguments:
            return "无看多论点"
        points = [f"• {arg.point}" for arg in debate.bull_arguments[:5]]
        return "\n".join(points)

    def _format_bear_summary(self, debate: DebateResult) -> str:
        """Format bear arguments summary."""
        if not debate.bear_arguments:
            return "无看空论点"
        points = [f"• {arg.point}" for arg in debate.bear_arguments[:5]]
        return "\n".join(points)

    def _adjust_confidence(
        self,
        base_confidence: float,
        research: ResearchReport,
        debate: DebateResult
    ) -> float:
        """Adjust confidence based on data quality metrics."""
        confidence = base_confidence

        # Source diversity bonus
        num_sources = len(research.sources)
        if num_sources >= 3:
            confidence += 10
        elif num_sources >= 2:
            confidence += 5

        # Data conflict penalty
        if research.data_conflicts:
            confidence -= len(research.data_conflicts) * 5

        # Debate ratio penalty (closer to 0.5 = more uncertainty)
        ratio = debate.bull_bear_ratio
        uncertainty = 1 - abs(ratio - 0.5) * 2  # 0 at extremes, 1 at 0.5
        confidence -= uncertainty * 10

        # Key facts bonus
        if len(research.key_facts) >= 5:
            confidence += 5

        # Clamp to valid range
        return max(20, min(95, confidence))

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        # Fallback parsing
        return {
            "recommendation": "持有",
            "confidence": 50,
            "rationale": response[:500] if response else "需要更多信息",
            "key_risks": [],
            "catalysts": [],
            "tracking_metrics": [],
            "time_horizon": "中期",
            "thesis_summary": response[:1000] if response else ""
        }

    def _build_decision(self, query: str, result: Dict[str, Any]) -> Decision:
        """Build Decision object from parsed result."""
        # Map recommendation string to enum
        rec_str = result.get("recommendation", "持有")
        rec_map = {
            "强烈买入": Recommendation.STRONG_BUY,
            "买入": Recommendation.BUY,
            "持有": Recommendation.HOLD,
            "卖出": Recommendation.SELL,
            "强烈卖出": Recommendation.STRONG_SELL,
        }
        recommendation = rec_map.get(rec_str, Recommendation.HOLD)

        # Build tracking metrics
        tracking_metrics = []
        for m in result.get("tracking_metrics", []):
            if isinstance(m, dict):
                tracking_metrics.append(TrackingMetric(
                    metric_name=m.get("metric", ""),
                    target_direction=m.get("direction", ""),
                    importance=m.get("importance", "medium")
                ))

        return Decision(
            query=query,
            recommendation=recommendation,
            confidence=result.get("confidence", 50),
            rationale=result.get("rationale", ""),
            key_risks=result.get("key_risks", []),
            catalysts=result.get("catalysts", []),
            tracking_metrics=tracking_metrics,
            time_horizon=result.get("time_horizon", "中期"),
            thesis_summary=result.get("thesis_summary", "")
        )


# Convenience function
def make_decision(
    research_report: ResearchReport,
    debate_result: DebateResult,
    progress_callback: Callable = None
) -> Decision:
    """Run decision agent workflow."""
    agent = DecisionAgent()
    return agent.decide(research_report, debate_result, progress_callback)
