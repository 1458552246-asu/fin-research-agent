"""
Phase 5: Signal Detection Agent

Classifies events/findings into signal levels and determines action:
- 🔴 Strong: Immediate push (earnings surprise, major insider activity, M&A)
- 🟡 Medium: Include in daily/weekly report (target price changes, policy shifts)
- 🟢 Weak: Archive for reference (trend articles, sentiment shifts)

Can operate in two modes:
1. Post-analysis: Extract signals from completed analysis workflow
2. Scan mode: Proactively scan watchlist for new signals (future: scheduled)
"""

import json
import re
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SignalLevel(Enum):
    """Signal urgency level."""
    STRONG = "strong"    # 🔴 Immediate push
    MEDIUM = "medium"    # 🟡 Daily/weekly report
    WEAK = "weak"        # 🟢 Archive


class SignalCategory(Enum):
    """Signal category for classification."""
    EARNINGS = "earnings"              # Earnings beat/miss
    INSIDER_ACTIVITY = "insider"       # Insider buy/sell
    REGULATORY = "regulatory"          # SEC filings, 8-K
    ANALYST_RATING = "analyst_rating"  # Rating changes
    PRICE_ACTION = "price_action"      # Major price moves
    INDUSTRY_POLICY = "industry"       # Policy/regulation
    PEER_MOVEMENT = "peer"             # Peer stock moves
    INSTITUTIONAL = "institutional"    # 13F changes
    SUPPLY_CHAIN = "supply_chain"      # Supply/customer changes
    SENTIMENT = "sentiment"            # Social/media sentiment
    MACRO = "macro"                    # Macro data
    OTHER = "other"


@dataclass
class Signal:
    """A detected signal with classification."""
    ticker: str
    level: SignalLevel
    category: SignalCategory
    title: str
    description: str
    source: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    action_required: str = ""  # What should the user do
    related_thesis: str = ""   # How it relates to existing thesis
    confidence: float = 0.7    # How confident in the classification


@dataclass
class SignalReport:
    """Collection of signals from a scan or analysis."""
    ticker: str
    signals: List[Signal] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def strong_signals(self) -> List[Signal]:
        return [s for s in self.signals if s.level == SignalLevel.STRONG]

    @property
    def medium_signals(self) -> List[Signal]:
        return [s for s in self.signals if s.level == SignalLevel.MEDIUM]

    @property
    def weak_signals(self) -> List[Signal]:
        return [s for s in self.signals if s.level == SignalLevel.WEAK]

    @property
    def has_immediate_action(self) -> bool:
        return len(self.strong_signals) > 0


# =============================================================================
# Signal Classification Rules
# =============================================================================

# Keywords that indicate strong signals
STRONG_SIGNAL_PATTERNS = [
    # Earnings
    (r"(超预期|beat|surprise).{0,20}(>?\s*10%|大幅)", SignalCategory.EARNINGS),
    (r"(不及预期|miss|下调).{0,20}(>?\s*10%|大幅)", SignalCategory.EARNINGS),
    # Insider activity
    (r"(增持|减持|买入|卖出).{0,20}(>\$?1[Mm]|百万|千万)", SignalCategory.INSIDER_ACTIVITY),
    (r"(CEO|CFO|高管).{0,10}(增持|减持|抛售)", SignalCategory.INSIDER_ACTIVITY),
    # Regulatory / corporate events
    (r"(并购|收购|merger|acquisition)", SignalCategory.REGULATORY),
    (r"(分拆|spin.?off|剥离)", SignalCategory.REGULATORY),
    (r"(诉讼|起诉|SEC调查|lawsuit)", SignalCategory.REGULATORY),
    (r"(停牌|复牌|halt)", SignalCategory.REGULATORY),
    # Analyst rating major shift
    (r"(连续|3家以上).{0,10}(上调|下调)", SignalCategory.ANALYST_RATING),
    (r"(大幅上调|大幅下调).{0,10}(评级|目标价)", SignalCategory.ANALYST_RATING),
]

MEDIUM_SIGNAL_PATTERNS = [
    # Analyst target changes
    (r"(目标价|target).{0,10}(上调|下调|调整)", SignalCategory.ANALYST_RATING),
    (r"(评级|rating).{0,10}(上调|下调|维持)", SignalCategory.ANALYST_RATING),
    # Policy
    (r"(政策|regulation|监管|关税|tariff)", SignalCategory.INDUSTRY_POLICY),
    # Peer moves
    (r"(同行|竞品|peer).{0,10}(涨|跌|暴[涨跌]|>?\s*5%)", SignalCategory.PEER_MOVEMENT),
    # Institutional
    (r"(13F|持仓|机构.{0,5}(增|减|建仓|清仓))", SignalCategory.INSTITUTIONAL),
    # Supply chain
    (r"(供应链|客户|订单).{0,10}(变化|调整|流失|新增)", SignalCategory.SUPPLY_CHAIN),
]


def classify_signal_text(text: str) -> tuple:
    """
    Classify a text snippet into signal level and category.

    Returns:
        (SignalLevel, SignalCategory)
    """
    text_lower = text.lower()

    # Check strong patterns
    for pattern, category in STRONG_SIGNAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return SignalLevel.STRONG, category

    # Check medium patterns
    for pattern, category in MEDIUM_SIGNAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return SignalLevel.MEDIUM, category

    # Default: weak
    return SignalLevel.WEAK, SignalCategory.OTHER


# =============================================================================
# Signal Detection Agent
# =============================================================================

class SignalDetectionAgent:
    """
    Detects and classifies signals from analysis results or proactive scans.

    Two modes:
    1. extract_from_analysis(): Post-analysis signal extraction
    2. scan(): Proactive watchlist scanning (uses research_team)
    """

    def __init__(self):
        self.name = "信号检测Agent"

    def extract_from_analysis(
        self,
        ticker: str,
        decision,          # Decision
        debate_result,     # DebateResult
        valuation_result,  # ValuationResult
        progress_callback: Callable = None,
    ) -> SignalReport:
        """
        Extract signals from a completed analysis workflow.

        Looks for:
        - Flip triggers that are close to firing
        - Valuation extremes (near Bear/Bull case)
        - High-confidence directional calls
        - Key risks that could materialize soon
        """
        if progress_callback:
            progress_callback("📡 Phase 5: 信号检测...")

        signals = []

        # 1. Check valuation positioning
        if valuation_result and valuation_result.current_price:
            signals.extend(
                self._check_valuation_signals(ticker, valuation_result)
            )

        # 2. Check flip triggers from debate
        if debate_result:
            signals.extend(
                self._check_flip_trigger_signals(ticker, debate_result)
            )

        # 3. Check decision confidence extremes
        if decision:
            signals.extend(
                self._check_decision_signals(ticker, decision)
            )

        # 4. Check key facts for event-based signals
        signals.extend(
            self._check_research_signals(ticker, debate_result)
        )

        report = SignalReport(ticker=ticker, signals=signals)

        if progress_callback:
            strong = len(report.strong_signals)
            medium = len(report.medium_signals)
            weak = len(report.weak_signals)
            progress_callback(
                f"✅ Phase 5 完成: 检测到 {len(signals)} 个信号 "
                f"(🔴{strong} 🟡{medium} 🟢{weak})"
            )

        return report

    def _check_valuation_signals(self, ticker: str, val) -> List[Signal]:
        """Check valuation-based signals."""
        signals = []
        price = val.current_price

        if not price or not val.scenarios:
            return signals

        # Near Bear Case → strong signal (potential opportunity or danger)
        bear = next((s for s in val.scenarios if s.label == "Bear"), None)
        if bear and bear.target_price:
            distance_to_bear = (price - bear.target_price) / price
            if distance_to_bear < 0.10:  # Within 10% of bear case
                signals.append(Signal(
                    ticker=ticker,
                    level=SignalLevel.STRONG,
                    category=SignalCategory.PRICE_ACTION,
                    title=f"接近Bear Case目标价",
                    description=(
                        f"当前价${price:.0f}距Bear Case ${bear.target_price:.0f}"
                        f"仅{distance_to_bear:.0%}，风险已较充分定价或超跌机会"
                    ),
                    action_required="评估是否达到Bear Case前提条件，若未触发可考虑逆向建仓",
                    confidence=0.8,
                ))

        # Near Bull Case → medium signal (consider taking profit)
        bull = next((s for s in val.scenarios if s.label == "Bull"), None)
        if bull and bull.target_price:
            distance_to_bull = (bull.target_price - price) / price
            if distance_to_bull < 0.05:  # Within 5% of bull case
                signals.append(Signal(
                    ticker=ticker,
                    level=SignalLevel.MEDIUM,
                    category=SignalCategory.PRICE_ACTION,
                    title=f"接近Bull Case目标价",
                    description=(
                        f"当前价${price:.0f}接近Bull Case ${bull.target_price:.0f}"
                        f"（差{distance_to_bull:.0%}），上行空间有限"
                    ),
                    action_required="考虑部分止盈或重新评估Bull Case前提是否需上调",
                    confidence=0.7,
                ))

        return signals

    def _check_flip_trigger_signals(self, ticker: str, debate) -> List[Signal]:
        """Check if any flip triggers are close to firing."""
        signals = []

        for trigger in getattr(debate, 'flip_triggers', []) or []:
            # Each flip trigger is a potential strong signal if it fires
            signals.append(Signal(
                ticker=ticker,
                level=SignalLevel.MEDIUM,
                category=SignalCategory.OTHER,
                title="条件反转监控点",
                description=trigger,
                action_required="持续监控，若触发需重新评估",
                confidence=0.6,
            ))

        return signals

    def _check_decision_signals(self, ticker: str, decision) -> List[Signal]:
        """Check decision-based signals."""
        signals = []

        # High confidence strong buy/sell → strong signal
        from .models import Recommendation
        if decision.confidence >= 80:
            if decision.recommendation in (Recommendation.STRONG_BUY, Recommendation.STRONG_SELL):
                direction = "买入" if "买" in decision.recommendation.value else "卖出"
                signals.append(Signal(
                    ticker=ticker,
                    level=SignalLevel.STRONG,
                    category=SignalCategory.OTHER,
                    title=f"高置信度{direction}信号",
                    description=(
                        f"置信度{decision.confidence:.0f}%，"
                        f"建议{decision.recommendation.value}。"
                        f"逻辑：{decision.rationale[:100]}"
                    ),
                    action_required=f"建议执行{direction}操作",
                    confidence=decision.confidence / 100,
                ))

        # Key risks that could materialize
        for risk in decision.key_risks[:2]:
            level, category = classify_signal_text(risk)
            if level != SignalLevel.WEAK:
                signals.append(Signal(
                    ticker=ticker,
                    level=level,
                    category=category,
                    title=f"关键风险: {risk[:30]}",
                    description=risk,
                    action_required="纳入风险监控清单",
                    confidence=0.5,
                ))

        return signals

    def _check_research_signals(self, ticker: str, debate) -> List[Signal]:
        """Check debate arguments for event-based signals."""
        signals = []

        if not debate:
            return signals

        # Scan bull/bear arguments for signal-worthy content
        all_args = (debate.bull_arguments or []) + (debate.bear_arguments or [])
        for arg in all_args:
            if not arg.evidence:
                continue
            level, category = classify_signal_text(arg.evidence)
            if level == SignalLevel.STRONG:
                signals.append(Signal(
                    ticker=ticker,
                    level=SignalLevel.STRONG,
                    category=category,
                    title=arg.point[:50],
                    description=arg.evidence,
                    action_required="核实并评估对投资论点的影响",
                    confidence=arg.strength,
                ))

        return signals
