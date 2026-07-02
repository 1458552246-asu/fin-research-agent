"""
Smart Summary - Structured output formatter.

Generates the final structured report in a format suitable for:
- Terminal display
- 飞书/Slack card messages
- Export as plain text

Format follows the optimization document's "投研简报" template.
"""

from typing import Optional
from datetime import datetime

from .models import WorkflowState, Recommendation
from .scorecard import Scorecard, build_scorecard


def generate_smart_summary(state: WorkflowState, scorecard: Scorecard = None) -> str:
    """
    Generate a structured Smart Summary from completed workflow state.

    Args:
        state: Completed WorkflowState
        scorecard: Optional pre-built scorecard (will build one if not provided)

    Returns:
        Formatted string report
    """
    ticker = "UNKNOWN"
    if state.valuation_result:
        ticker = state.valuation_result.ticker

    if not scorecard:
        scorecard = build_scorecard(
            ticker=ticker,
            decision=state.decision,
            valuation_result=state.valuation_result,
            debate_result=state.debate_result,
            research_report=state.research_report,
        )

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []

    # ═══ Header ═══
    lines.append("═" * 45)
    lines.append(f"  {ticker} 投研简报")
    lines.append(f"  生成时间：{now}")
    lines.append("═" * 45)
    lines.append("")

    # ═══ Key Takeaways ═══
    lines.append("📋 Key Takeaways（核心结论）")
    takeaways = _build_takeaways(state, scorecard)
    for i, t in enumerate(takeaways, 1):
        lines.append(f"  {i}. {t}")
    lines.append("")

    # ═══ Debate Conclusion ═══
    if state.debate_result:
        d = state.debate_result
        ratio = d.bull_bear_ratio
        lines.append("⚔️ 多空辩论结论")
        lines.append(f"  多空比：{ratio:.0%}:{1-ratio:.0%}")
        if d.disputes:
            lines.append(f"  关键分歧：{' | '.join(d.disputes[:3])}")
        if d.flip_triggers:
            lines.append(f"  条件反转：{d.flip_triggers[0]}")
        if d.information_gaps:
            lines.append(f"  信息缺口：{', '.join(d.information_gaps[:2])}")
        lines.append("")

    # ═══ Valuation ═══
    if state.valuation_result:
        v = state.valuation_result
        lines.append("💰 估值")

        # Scenarios
        if v.scenarios:
            scenario_parts = []
            for s in v.scenarios:
                emoji = {"Bull": "🟢", "Base": "🟡", "Bear": "🔴"}.get(s.label, "")
                scenario_parts.append(f"{emoji}{s.label} ${s.target_price:.0f}")
            lines.append(f"  三情景目标价：{' | '.join(scenario_parts)}")

        if v.current_price and v.weighted_target:
            upside = v.weighted_upside
            lines.append(
                f"  当前价 ${v.current_price:.0f} vs "
                f"加权目标 ${v.weighted_target:.0f} → "
                f"{'上涨' if upside >= 0 else '下跌'}空间 {abs(upside):.1f}%"
            )

        if v.margin_of_safety:
            lines.append(f"  安全边际：{v.margin_of_safety}")

        # Relative valuation
        if v.relative_valuation and v.relative_valuation.pe_percentile is not None:
            rv = v.relative_valuation
            lines.append(
                f"  P/E {rv.current_pe:.0f}x (行业{rv.industry_pe:.0f}x, "
                f"5年分位{rv.pe_percentile:.0f}%)"
            )

        lines.append("")

    # ═══ Scorecard ═══
    lines.append("📊 决策打分卡")
    lines.append("  ┌──────────────────────────────────────────┐")
    lines.append("  │ 维度          权重    评分    加权分       │")
    lines.append("  ├──────────────────────────────────────────┤")
    for dim in scorecard.dimensions:
        name_padded = dim.name.ljust(6, "　")  # Pad with wide space
        lines.append(
            f"  │ {name_padded}    "
            f"{dim.weight:.0%}    "
            f"{dim.score:.1f}     "
            f"{dim.weighted_score:.2f}       │"
        )
    lines.append("  ├──────────────────────────────────────────┤")
    lines.append(f"  │ 综合评分              {scorecard.total_score:.2f} / 10         │")
    lines.append("  └──────────────────────────────────────────┘")
    lines.append(f"  解读：{scorecard.interpretation}")
    lines.append(f"  建议仓位：{scorecard.position_suggestion}")
    lines.append("")

    # ═══ Decision ═══
    if state.decision:
        dec = state.decision
        emoji = dec.recommendation_emoji()
        lines.append(f"📈 投资建议：{emoji} {dec.recommendation.value} (置信度 {dec.confidence:.0f}%)")
        lines.append(f"  核心逻辑：{dec.rationale}")
        lines.append(f"  时间维度：{dec.time_horizon}")

        if dec.catalysts:
            lines.append(f"  催化剂：{' | '.join(dec.catalysts[:3])}")
        if dec.key_risks:
            lines.append(f"  风险：{' | '.join(dec.key_risks[:3])}")

        lines.append("")

    # ═══ Action Plan ═══
    lines.append("📝 行动建议")
    lines.append(f"  仓位建议：{scorecard.position_suggestion}")

    if state.valuation_result and state.valuation_result.scenarios:
        v = state.valuation_result
        bear = next((s for s in v.scenarios if s.label == "Bear"), None)
        base = next((s for s in v.scenarios if s.label == "Base"), None)

        if v.current_price and base:
            # Suggest entry below current for better margin
            entry_price = v.current_price * 0.92  # ~8% below
            lines.append(f"  建仓区间：< ${entry_price:.0f}（安全边际更充足）")
        if bear:
            lines.append(f"  止损参考：${bear.target_price:.0f}（Bear Case触发）")
        if base:
            lines.append(f"  目标价：${base.target_price:.0f}（Base Case）")

    lines.append("")

    # ═══ Signals ═══
    if state.signal_report and state.signal_report.signals:
        sr = state.signal_report
        lines.append("🔔 监控信号")
        for s in sr.strong_signals[:2]:
            lines.append(f"  🔴 强：{s.title}")
        for s in sr.medium_signals[:3]:
            lines.append(f"  🟡 中：{s.title}")
        for s in sr.weak_signals[:2]:
            lines.append(f"  🟢 弱：{s.title}")
        lines.append("")

    # ═══ Footer ═══
    lines.append("═" * 45)

    return "\n".join(lines)


def _build_takeaways(state: WorkflowState, scorecard: Scorecard) -> list:
    """Build 3-5 key takeaway bullet points."""
    takeaways = []

    # 1. Core thesis from decision
    if state.decision:
        takeaways.append(state.decision.rationale[:80])

    # 2. Valuation position
    if state.valuation_result and state.valuation_result.relative_valuation:
        rv = state.valuation_result.relative_valuation
        if rv.pe_percentile:
            val_desc = "偏贵" if rv.pe_percentile > 70 else "合理" if rv.pe_percentile > 40 else "偏低"
            takeaways.append(f"当前估值处于历史{rv.pe_percentile:.0f}分位，{val_desc}")

    # 3. Key risk
    if state.decision and state.decision.key_risks:
        takeaways.append(f"最大风险：{state.decision.key_risks[0]}")

    # 4. Scorecard summary
    takeaways.append(
        f"综合评分 {scorecard.total_score:.2f}/10，{scorecard.interpretation}"
    )

    return takeaways[:5]


def generate_summary_json(state: WorkflowState, scorecard: Scorecard = None) -> dict:
    """
    Generate Smart Summary as JSON (for API/webhook delivery).

    Returns a dict suitable for 飞书/Slack card payloads.
    """
    ticker = "UNKNOWN"
    if state.valuation_result:
        ticker = state.valuation_result.ticker

    if not scorecard:
        scorecard = build_scorecard(
            ticker=ticker,
            decision=state.decision,
            valuation_result=state.valuation_result,
            debate_result=state.debate_result,
            research_report=state.research_report,
        )

    result = {
        "ticker": ticker,
        "generated_at": datetime.now().isoformat(),
        "recommendation": state.decision.recommendation.value if state.decision else None,
        "confidence": state.decision.confidence if state.decision else None,
        "score": scorecard.total_score,
        "interpretation": scorecard.interpretation,
        "position_suggestion": scorecard.position_suggestion,
    }

    if state.debate_result:
        result["bull_bear_ratio"] = state.debate_result.bull_bear_ratio
        result["key_disagreements"] = state.debate_result.disputes[:3]
        result["flip_triggers"] = state.debate_result.flip_triggers[:2]

    if state.valuation_result:
        v = state.valuation_result
        result["current_price"] = v.current_price
        result["weighted_target"] = v.weighted_target
        result["scenarios"] = [
            {"label": s.label, "target": s.target_price, "probability": s.probability}
            for s in v.scenarios
        ]
        result["margin_of_safety"] = v.margin_of_safety

    if state.decision:
        result["catalysts"] = state.decision.catalysts[:3]
        result["risks"] = state.decision.key_risks[:3]
        result["time_horizon"] = state.decision.time_horizon

    result["scorecard"] = [
        {"dimension": d.name, "weight": d.weight, "score": d.score, "rationale": d.rationale}
        for d in scorecard.dimensions
    ]

    if state.signal_report:
        result["signals"] = {
            "strong": len(state.signal_report.strong_signals),
            "medium": len(state.signal_report.medium_signals),
            "weak": len(state.signal_report.weak_signals),
        }

    return result
