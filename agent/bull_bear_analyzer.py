"""Bull/Bear Analyzer - Extract and structure bullish/bearish viewpoints from sources."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from .config import Config

# Try to import anthropic, but make it optional
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None


@dataclass
class Viewpoint:
    """A single bullish or bearish viewpoint."""
    content: str
    source: str
    source_type: str  # e.g., "专家访谈", "AlphaEngine"
    source_date: str
    confidence: str  # "高", "中", "低"


@dataclass
class BullBearAnalysis:
    """Structured Bull/Bear analysis result."""
    query: str
    bull_points: List[Viewpoint]
    bear_points: List[Viewpoint]
    synthesis: str
    overall_stance: str  # "看多", "中性偏多", "中性", "中性偏空", "看空"
    key_factors: List[str]
    sources_used: List[Dict]


BULL_BEAR_SYSTEM_PROMPT = """你是一个专业的金融分析助手，专门负责从多个信息来源中提取并结构化多空观点。

你的任务是：
1. 从提供的信息来源中识别看多(Bull)和看空(Bear)的观点
2. 每个观点必须标注来源
3. 给出综合判断和关键影响因素

输出格式要求（JSON）：
{
    "bull_points": [
        {"content": "观点内容", "source": "来源名称", "source_type": "来源类型", "confidence": "高/中/低"}
    ],
    "bear_points": [
        {"content": "观点内容", "source": "来源名称", "source_type": "来源类型", "confidence": "高/中/低"}
    ],
    "synthesis": "综合分析结论（2-3句话）",
    "overall_stance": "看多/中性偏多/中性/中性偏空/看空",
    "key_factors": ["关键因素1", "关键因素2", "关键因素3"]
}

分析原则：
- 只提取来源中明确提到的观点，不要推测
- 对比不同来源的观点，找出共识和分歧
- 最新的信息权重更高
- 专家访谈和一手调研权重高于二手研报
"""


class BullBearAnalyzer:
    """Analyzes search results to extract structured Bull/Bear viewpoints."""

    def __init__(self):
        self._client = None
        if ANTHROPIC_AVAILABLE and Config.has_llm_api():
            self._client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    def analyze(
        self,
        query: str,
        search_results: List[Dict],
        use_mock: bool = False
    ) -> BullBearAnalysis:
        """Perform Bull/Bear analysis on search results.

        Args:
            query: User's original query
            search_results: List of search result dicts with content and metadata
            use_mock: Force use of mock data

        Returns:
            BullBearAnalysis with structured viewpoints
        """
        if use_mock or not self._client:
            return self._get_mock_analysis(query, search_results)

        return self._llm_analyze(query, search_results)

    def _llm_analyze(self, query: str, search_results: List[Dict]) -> BullBearAnalysis:
        """Use Claude to analyze search results."""
        # Format sources for the prompt
        sources_text = self._format_sources_for_prompt(search_results)

        user_prompt = f"""用户问题：{query}

以下是从多个知识库检索到的相关信息：

{sources_text}

请从上述信息中提取看多和看空的观点，并给出综合分析。"""

        try:
            response = self._client.messages.create(
                model="claude-opus-4-6-20250228",
                max_tokens=2000,
                system=BULL_BEAR_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )

            # Parse JSON response
            import json
            content = response.content[0].text

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())

            return BullBearAnalysis(
                query=query,
                bull_points=[
                    Viewpoint(
                        content=p["content"],
                        source=p["source"],
                        source_type=p.get("source_type", ""),
                        source_date="",
                        confidence=p.get("confidence", "中")
                    )
                    for p in data.get("bull_points", [])
                ],
                bear_points=[
                    Viewpoint(
                        content=p["content"],
                        source=p["source"],
                        source_type=p.get("source_type", ""),
                        source_date="",
                        confidence=p.get("confidence", "中")
                    )
                    for p in data.get("bear_points", [])
                ],
                synthesis=data.get("synthesis", ""),
                overall_stance=data.get("overall_stance", "中性"),
                key_factors=data.get("key_factors", []),
                sources_used=search_results
            )

        except Exception as e:
            print(f"LLM analysis failed: {e}, falling back to mock")
            return self._get_mock_analysis(query, search_results)

    def _format_sources_for_prompt(self, search_results: List[Dict]) -> str:
        """Format search results for the LLM prompt."""
        parts = []
        for i, src in enumerate(search_results, 1):
            source_type = src.get("source_type", "未知来源")
            title = src.get("title", "无标题")
            date = src.get("date", "")
            content = src.get("content", src.get("snippet", ""))

            parts.append(f"""【来源 {i}】{source_type} - {title}
时间：{date}
内容：{content}
""")
        return "\n---\n".join(parts)

    def _get_mock_analysis(self, query: str, search_results: List[Dict]) -> BullBearAnalysis:
        """Return mock analysis for demo purposes."""
        from mock.mock_data import get_mock_analysis
        return get_mock_analysis(query, search_results)
