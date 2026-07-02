"""
Decision Scorecard (决策打分卡)

5-dimension weighted scoring model:
- 基本面 (Fundamentals): 30% — earnings growth, margins, ROE
- 估值 (Valuation): 25% — P/E vs industry/historical
- 催化剂 (Catalysts): 20% — near-term triggers
- 风险 (Risk/Downside): 15% — bear case distance
- 动量 (Momentum): 10% — price trend + sentiment

Output: 0-10 composite score → action mapping
"""

from typing import Optional, Dict, List
from dataclasses import dataclass, field


@dataclass
class DimensionScore:
    """Score for a single dimension."""
    name: str
    weight: float       # 0-1
    score: float        # 1-10
    rationale: str      # Why this score

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class Scorecard:
    """Complete 5-dimension scorecard."""
    ticker: str
    dimensions: List[DimensionScore] = field(default_factory=list)

    @property
    def total_score(self) -> float:
        """Weighted composite score (0-10)."""
        if not self.dimensions:
            return 5.0
        return sum(d.weighted_score for d in self.dimensions)

    @property
    def interpretation(self) -> str:
        """Score interpretation."""
        s = self.total_score
        if s >= 8:
            return "强烈看多，积极建仓"
        elif s >= 6:
            return "谨慎看多，可小仓位参与"
        elif s >= 4:
            return "中性，观望为主"
        elif s >= 2:
            return "谨慎看空，考虑减仓"
        else:
            return "强烈看空，建议清仓"

    @property
    def position_suggestion(self) -> str:
        """Suggested position size."""
        s = self.total_score
        if s >= 8:
            return "20-30%"
        elif s >= 7:
            return "15-20%"
        elif s >= 6:
            return "10-15%"
        elif s >= 5:
            return "5-10%"
        elif s >= 4:
            return "0-5%（观望）"
        else:
            return "0%（回避）"


def build_scorecard(
    ticker: str,
    decision,           # Decision
    valuation_result,   # ValuationResult
    debate_result,      # DebateResult
    research_report,    # ResearchReport
) -> Scorecard:
    """
    Build a 5-dimension scorecard from analysis results.

    Scoring rules:
    - Fundamentals (30%): Based on key facts sentiment, data quality
    - Valuation (25%): Based on PE percentile, relative to peers
    - Catalysts (20%): Based on catalyst count and proximity
    - Risk (15%): Based on bear case distance
    - Momentum (10%): Based on bull/bear ratio and sentiment
    """
    dimensions = []

    # 1. Fundamentals (30%)
    fund_score = _score_fundamentals(research_report, decision)
    dimensions.append(DimensionScore(
        name="基本面", weight=0.30, score=fund_score[0], rationale=fund_score[1]
    ))

    # 2. Valuation (25%)
    val_score = _score_valuation(valuation_result)
    dimensions.append(DimensionScore(
        name="估值", weight=0.25, score=val_score[0], rationale=val_score[1]
    ))

    # 3. Catalysts (20%)
    cat_score = _score_catalysts(decision)
    dimensions.append(DimensionScore(
        name="催化剂", weight=0.20, score=cat_score[0], rationale=cat_score[1]
    ))

    # 4. Risk / Downside Protection (15%)
    risk_score = _score_risk(valuation_result, decision)
    dimensions.append(DimensionScore(
        name="风险", weight=0.15, score=risk_score[0], rationale=risk_score[1]
    ))

    # 5. Momentum (10%)
    mom_score = _score_momentum(debate_result, research_report)
    dimensions.append(DimensionScore(
        name="动量", weight=0.10, score=mom_score[0], rationale=mom_score[1]
    ))

    return Scorecard(ticker=ticker, dimensions=dimensions)


# =============================================================================
# Dimension Scoring Functions
# =============================================================================

def _score_fundamentals(research_report, decision) -> tuple:
    """
    Score fundamentals based on research data quality and sentiment.

    8-10: Revenue growth >30%, margins >60%
    6-8:  Revenue growth 15-30%, margins 40-60%
    4-6:  Revenue growth 5-15%, margins 30-40%
    <4:   Revenue growth <5% or negative
    """
    if not research_report:
        return (5.0, "数据不足，给予中性评分")

    # Count positive vs negative facts
    positive = len(research_report.get_positive_facts())
    negative = len(research_report.get_negative_facts())
    total = len(research_report.key_facts)

    if total == 0:
        return (5.0, "无关键事实数据")

    pos_ratio = positive / total

    # Check data quality from sources
    num_sources = len(research_report.sources)

    # Base score from sentiment
    if pos_ratio >= 0.7 and num_sources >= 3:
        score = 8.0
        rationale = f"正面信号占{pos_ratio:.0%}，{num_sources}个数据源，基本面强劲"
    elif pos_ratio >= 0.5:
        score = 6.5
        rationale = f"正面信号占{pos_ratio:.0%}，基本面良好"
    elif pos_ratio >= 0.3:
        score = 5.0
        rationale = f"正面信号占{pos_ratio:.0%}，基本面中性"
    else:
        score = 3.5
        rationale = f"正面信号仅{pos_ratio:.0%}，基本面偏弱"

    # Bonus for confidence
    if decision and decision.confidence >= 75:
        score = min(10, score + 0.5)

    return (score, rationale)


def _score_valuation(valuation_result) -> tuple:
    """
    Score valuation based on PE percentile and relative positioning.

    8-10: PE below 25th percentile (cheap)
    6-8:  PE at 40-60th percentile (fair)
    4-6:  PE at 60-80th percentile (rich)
    <4:   PE above 80th percentile (expensive)
    """
    if not valuation_result or not valuation_result.relative_valuation:
        return (5.0, "估值数据不足")

    rv = valuation_result.relative_valuation
    percentile = rv.pe_percentile

    if percentile is None:
        # Fallback: use PE vs industry
        if rv.current_pe and rv.industry_pe:
            premium = (rv.current_pe / rv.industry_pe - 1) * 100
            if premium < -20:
                return (8.0, f"P/E低于行业{-premium:.0f}%，估值偏低")
            elif premium < 20:
                return (6.0, f"P/E接近行业均值，估值合理")
            elif premium < 50:
                return (4.5, f"P/E高于行业{premium:.0f}%，估值偏高")
            else:
                return (3.0, f"P/E高于行业{premium:.0f}%，估值昂贵")
        return (5.0, "估值数据不足")

    if percentile <= 25:
        score = 8.5
        rationale = f"PE处于5年{percentile:.0f}%分位，估值偏低"
    elif percentile <= 50:
        score = 7.0
        rationale = f"PE处于5年{percentile:.0f}%分位，估值合理"
    elif percentile <= 75:
        score = 5.0
        rationale = f"PE处于5年{percentile:.0f}%分位，估值偏高"
    else:
        score = 3.0
        rationale = f"PE处于5年{percentile:.0f}%分位，估值昂贵"

    return (score, rationale)


def _score_catalysts(decision) -> tuple:
    """
    Score catalysts based on count and implied proximity.

    8-10: 3+ clear catalysts with near-term timing
    6-8:  2 catalysts
    4-6:  1 catalyst or uncertain timing
    <4:   No clear catalysts
    """
    if not decision:
        return (5.0, "无决策数据")

    catalysts = decision.catalysts or []
    num = len(catalysts)

    if num >= 3:
        score = 8.0
        rationale = f"{num}个催化剂（{', '.join(c[:15] for c in catalysts[:2])}...）"
    elif num == 2:
        score = 6.5
        rationale = f"2个催化剂（{', '.join(c[:20] for c in catalysts)}）"
    elif num == 1:
        score = 5.0
        rationale = f"1个催化剂（{catalysts[0][:30]}）"
    else:
        score = 3.5
        rationale = "无明确催化剂"

    # Time horizon adjustment
    if decision.time_horizon == "短期":
        score = min(10, score + 1.0)  # Near-term = higher catalyst score
    elif decision.time_horizon == "长期":
        score = max(1, score - 0.5)

    return (score, rationale)


def _score_risk(valuation_result, decision) -> tuple:
    """
    Score downside risk (higher score = better protected).

    8-10: Bear case >30% below current (well protected)
    6-8:  Bear case 15-30% below current
    4-6:  Bear case 5-15% below current
    <4:   Bear case <5% below current (high risk)
    """
    if not valuation_result or not valuation_result.current_price:
        # Fallback: use decision risks count
        if decision and decision.key_risks:
            num_risks = len(decision.key_risks)
            if num_risks >= 4:
                return (3.5, f"{num_risks}个关键风险，下行保护不足")
            elif num_risks >= 2:
                return (5.0, f"{num_risks}个关键风险，风险适中")
            else:
                return (7.0, "关键风险较少")
        return (5.0, "风险数据不足")

    price = valuation_result.current_price
    bear_case = None
    for s in valuation_result.scenarios:
        if s.label == "Bear":
            bear_case = s.target_price
            break

    if not bear_case:
        return (5.0, "无Bear Case数据")

    distance = (price - bear_case) / price * 100  # % above bear case

    if distance >= 30:
        score = 8.5
        rationale = f"距Bear Case {distance:.0f}%，下行保护充分"
    elif distance >= 15:
        score = 6.5
        rationale = f"距Bear Case {distance:.0f}%，保护适中"
    elif distance >= 5:
        score = 4.5
        rationale = f"距Bear Case仅{distance:.0f}%，保护不足"
    else:
        score = 2.5
        rationale = f"距Bear Case仅{distance:.0f}%，下行风险大"

    return (score, rationale)


def _score_momentum(debate_result, research_report) -> tuple:
    """
    Score momentum based on debate ratio and sentiment.

    8-10: Strong bullish ratio (>70%) + positive sentiment
    6-8:  Moderate bullish (55-70%)
    4-6:  Neutral (45-55%)
    <4:   Bearish (<45%)
    """
    if not debate_result:
        return (5.0, "无辩论数据")

    ratio = debate_result.bull_bear_ratio

    if ratio >= 0.70:
        score = 8.5
        rationale = f"多空比{ratio:.0%}，强看多共识"
    elif ratio >= 0.55:
        score = 6.5
        rationale = f"多空比{ratio:.0%}，偏看多"
    elif ratio >= 0.45:
        score = 5.0
        rationale = f"多空比{ratio:.0%}，中性"
    elif ratio >= 0.30:
        score = 3.5
        rationale = f"多空比{ratio:.0%}，偏看空"
    else:
        score = 2.0
        rationale = f"多空比{ratio:.0%}，强看空共识"

    return (score, rationale)
