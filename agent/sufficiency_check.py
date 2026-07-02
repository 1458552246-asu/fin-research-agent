"""
Information Sufficiency Check

Determines whether the debate result has enough data to proceed to Valuation,
or needs to loop back to Research for supplemental data collection.

Criteria:
- Information gaps count
- Bull/Bear argument count
- Evidence quality (strong vs weak ratio)
- Key disagreements that need data resolution
"""

from typing import List, Tuple
from .models import DebateResult, ResearchReport


class SufficiencyResult:
    """Result of information sufficiency check."""

    def __init__(
        self,
        is_sufficient: bool,
        score: float,
        gaps_to_fill: List[str],
        reason: str,
    ):
        self.is_sufficient = is_sufficient
        self.score = score  # 0-1, higher = more sufficient
        self.gaps_to_fill = gaps_to_fill  # Specific queries to search for
        self.reason = reason


def check_sufficiency(
    debate_result: DebateResult,
    research_report: ResearchReport,
    threshold: float = 0.6,
) -> SufficiencyResult:
    """
    Check if information gathered is sufficient to proceed.

    Scoring rubric (0-1):
        - Has >= 3 bull arguments with evidence: +0.15
        - Has >= 3 bear arguments with evidence: +0.15
        - Has >= 5 key facts from research:      +0.15
        - Has >= 2 source types:                 +0.15
        - Information gaps <= 1:                  +0.20
        - Has strong evidence ratio >= 40%:      +0.20

    If score < threshold → insufficient, return gaps_to_fill for re-search.

    Args:
        debate_result: Output from debate phase
        research_report: Output from research phase
        threshold: Minimum score to pass (default 0.6)

    Returns:
        SufficiencyResult with pass/fail and actionable gaps
    """
    score = 0.0
    reasons = []

    # Check bull arguments
    bull_with_evidence = [
        a for a in debate_result.bull_arguments
        if a.evidence and len(a.evidence) > 10
    ]
    if len(bull_with_evidence) >= 3:
        score += 0.15
    else:
        reasons.append(f"看多论据不足（{len(bull_with_evidence)}/3）")

    # Check bear arguments
    bear_with_evidence = [
        a for a in debate_result.bear_arguments
        if a.evidence and len(a.evidence) > 10
    ]
    if len(bear_with_evidence) >= 3:
        score += 0.15
    else:
        reasons.append(f"看空论据不足（{len(bear_with_evidence)}/3）")

    # Check key facts volume
    num_facts = len(research_report.key_facts)
    if num_facts >= 5:
        score += 0.15
    else:
        reasons.append(f"关键事实不足（{num_facts}/5）")

    # Check source diversity
    num_source_types = len(research_report.sources)
    if num_source_types >= 2:
        score += 0.15
    else:
        reasons.append(f"数据源单一（{num_source_types}/2）")

    # Check information gaps
    info_gaps = getattr(debate_result, 'information_gaps', []) or []
    if len(info_gaps) <= 1:
        score += 0.20
    else:
        reasons.append(f"信息缺口较多（{len(info_gaps)}个）")

    # Check evidence quality (strong ratio)
    all_args = debate_result.bull_arguments + debate_result.bear_arguments
    if all_args:
        strong_count = sum(1 for a in all_args if a.strength >= 0.8)
        strong_ratio = strong_count / len(all_args)
        if strong_ratio >= 0.4:
            score += 0.20
        else:
            reasons.append(f"强证据比例偏低（{strong_ratio:.0%}）")
    else:
        reasons.append("无任何论据")

    # Determine gaps to fill
    gaps_to_fill = list(info_gaps)  # Start with moderator-identified gaps

    # Add data needed from cross-exam "question" verdicts
    for debate_round in debate_result.debate_rounds:
        if debate_round.round_type == "cross_examination":
            for exchange in debate_round.exchanges:
                if "[question]" in exchange.statement.lower():
                    # Extract the topic needing more data
                    gaps_to_fill.append(exchange.statement)

    is_sufficient = score >= threshold
    reason = "信息充分" if is_sufficient else f"信息不足: {'; '.join(reasons)}"

    return SufficiencyResult(
        is_sufficient=is_sufficient,
        score=score,
        gaps_to_fill=gaps_to_fill[:5],  # Cap at 5 gaps to search
        reason=reason,
    )
