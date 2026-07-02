"""
Data models for multi-agent financial research system.

Defines the core data structures for:
- Phase 1: Research Team output (ResearchReport)
- Phase 2: Debate Team output (DebateResult)
- Phase 3: Decision Agent output (Decision)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class Sentiment(Enum):
    """Sentiment classification for research findings."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Recommendation(Enum):
    """Investment recommendation levels."""
    STRONG_BUY = "强烈买入"
    BUY = "买入"
    HOLD = "持有"
    SELL = "卖出"
    STRONG_SELL = "强烈卖出"


class SourceType(Enum):
    """Types of data sources."""
    EXPERT_INTERVIEW = "专家访谈"
    ALPHA_ENGINE = "AlphaEngine"
    TWITTER = "Twitter推文"
    SUBSTACK = "Substack"
    ACECAMP = "AceCampTech"
    WEB_SEARCH = "网络搜索"
    OTHER = "其他"


# =============================================================================
# Phase 1: Research Team Data Structures
# =============================================================================

@dataclass
class SourceReference:
    """Reference to an original source document."""
    source_type: str              # "专家访谈", "AlphaEngine", etc.
    title: str                    # Document title
    date: Optional[str] = None    # Publication date
    url: Optional[str] = None     # Link to source
    file_id: Optional[int] = None # KB file ID
    preview: Optional[str] = None # Text preview/excerpt


@dataclass
class DataPoint:
    """A quantitative data point extracted from sources."""
    metric: str              # e.g., "AI服务器收入"
    value: str               # e.g., "$4.5B"
    date: Optional[str] = None
    source: Optional[SourceReference] = None
    context: Optional[str] = None  # Additional context


@dataclass
class KeyFact:
    """A key fact or finding from research."""
    content: str                     # The fact statement
    sentiment: Sentiment             # positive/negative/neutral
    source: Optional[SourceReference] = None
    confidence: float = 0.8          # 0-1 confidence level


@dataclass
class SourceGroup:
    """Group of findings from a single source type."""
    source_type: str              # "专家访谈", "AlphaEngine", etc.
    source_name: str              # Display name
    date: Optional[str] = None    # Most recent date
    findings: List[str] = field(default_factory=list)
    data_points: List[DataPoint] = field(default_factory=list)
    raw_documents: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DataConflict:
    """Records conflicting information between sources."""
    topic: str                    # What the conflict is about
    source_a: SourceReference
    claim_a: str
    source_b: SourceReference
    claim_b: str
    resolution: Optional[str] = None  # How to resolve/interpret


@dataclass
class TimelineEvent:
    """An event on the research timeline."""
    date: str
    event: str
    source: Optional[SourceReference] = None
    importance: str = "medium"  # high/medium/low


@dataclass
class ResearchReport:
    """
    Output from Phase 1: Research Team.

    Contains structured findings from multiple analysts:
    - FundamentalAnalyst (AlphaEngine)
    - IndustryAnalyst (专家访谈)
    - SentimentAnalyst (Twitter/Substack)
    """
    query: str                               # Original user query
    company: Optional[str] = None            # Identified company (if any)
    sources: List[SourceGroup] = field(default_factory=list)
    key_facts: List[KeyFact] = field(default_factory=list)
    data_points: List[DataPoint] = field(default_factory=list)
    timeline: List[TimelineEvent] = field(default_factory=list)
    data_conflicts: List[DataConflict] = field(default_factory=list)
    total_sources_found: int = 0
    search_terms_used: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_all_findings(self) -> List[str]:
        """Get all findings as flat list."""
        findings = []
        for group in self.sources:
            findings.extend(group.findings)
        return findings

    def get_positive_facts(self) -> List[KeyFact]:
        """Get all positive sentiment facts."""
        return [f for f in self.key_facts if f.sentiment == Sentiment.POSITIVE]

    def get_negative_facts(self) -> List[KeyFact]:
        """Get all negative sentiment facts."""
        return [f for f in self.key_facts if f.sentiment == Sentiment.NEGATIVE]


# =============================================================================
# Phase 2: Debate Team Data Structures
# =============================================================================

@dataclass
class Argument:
    """A debate argument (bull or bear)."""
    point: str                           # The argument statement
    evidence: str                        # Supporting evidence
    source: Optional[SourceReference] = None
    strength: float = 0.7                # 0-1 argument strength
    rebuttal: Optional[str] = None       # Counter-argument if challenged


@dataclass
class DebateExchange:
    """A single exchange in the debate."""
    round_num: int
    speaker: str              # "bull" or "bear"
    statement: str
    is_rebuttal: bool = False
    targets_argument: Optional[str] = None  # What argument it's responding to


@dataclass
class DebateRound:
    """A complete round of debate."""
    round_num: int
    round_type: str           # "opening", "cross_examination", "closing"
    exchanges: List[DebateExchange] = field(default_factory=list)
    summary: Optional[str] = None


@dataclass
class DebateResult:
    """
    Output from Phase 2: Debate Team.

    Contains structured bull vs bear analysis:
    - BullAnalyst arguments
    - BearAnalyst arguments
    - Moderator summary of consensus/disputes
    - Information gaps and flip triggers (from 3-round debate)
    """
    query: str
    bull_arguments: List[Argument] = field(default_factory=list)
    bear_arguments: List[Argument] = field(default_factory=list)
    debate_rounds: List[DebateRound] = field(default_factory=list)
    consensus: List[str] = field(default_factory=list)        # Points both sides agree on
    disputes: List[str] = field(default_factory=list)         # Key disagreements
    bull_bear_ratio: float = 0.5        # 0=全看空, 0.5=中性, 1=全看多
    moderator_summary: Optional[str] = None
    information_gaps: List[str] = field(default_factory=list)  # Data needed for better judgment
    flip_triggers: List[str] = field(default_factory=list)     # Conditions that would flip conclusion
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_bull_strength(self) -> float:
        """Calculate average bull argument strength."""
        if not self.bull_arguments:
            return 0.0
        return sum(a.strength for a in self.bull_arguments) / len(self.bull_arguments)

    def get_bear_strength(self) -> float:
        """Calculate average bear argument strength."""
        if not self.bear_arguments:
            return 0.0
        return sum(a.strength for a in self.bear_arguments) / len(self.bear_arguments)


# =============================================================================
# Phase 3: Decision Agent Data Structures
# =============================================================================

@dataclass
class PriceTarget:
    """Price target recommendation."""
    aggressive_buy: Optional[float] = None   # 激进买入价
    conservative_buy: Optional[float] = None # 保守买入价
    stop_loss: Optional[float] = None        # 止损位
    current_price: Optional[float] = None    # 当前价格
    currency: str = "USD"


@dataclass
class TrackingMetric:
    """A metric to track for investment thesis."""
    metric_name: str              # e.g., "AI服务器毛利率"
    current_value: Optional[str] = None
    target_direction: str = ""    # "上升", "下降", "稳定"
    importance: str = "high"      # high/medium/low
    rationale: Optional[str] = None


@dataclass
class Decision:
    """
    Output from Phase 3: Decision Agent.

    Contains final investment recommendation with:
    - Recommendation and confidence
    - Key risks and catalysts
    - Price targets and tracking metrics
    """
    query: str
    recommendation: Recommendation
    confidence: float             # 0-100%
    rationale: str                # Core investment thesis (2-3 sentences)
    key_risks: List[str] = field(default_factory=list)
    catalysts: List[str] = field(default_factory=list)       # Potential positive triggers
    tracking_metrics: List[TrackingMetric] = field(default_factory=list)
    price_targets: Optional[PriceTarget] = None
    time_horizon: str = "中期"    # 短期/中期/长期
    thesis_summary: Optional[str] = None  # Detailed thesis
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def confidence_display(self) -> str:
        """Get confidence as display string."""
        return f"{self.confidence:.0f}%"

    def recommendation_emoji(self) -> str:
        """Get emoji for recommendation."""
        emojis = {
            Recommendation.STRONG_BUY: "🚀",
            Recommendation.BUY: "📈",
            Recommendation.HOLD: "⚖️",
            Recommendation.SELL: "📉",
            Recommendation.STRONG_SELL: "🔻",
        }
        return emojis.get(self.recommendation, "")


# =============================================================================
# Workflow State
# =============================================================================

@dataclass
class WorkflowState:
    """
    Tracks the state of the entire multi-agent workflow.
    Used by Orchestrator to manage phase transitions.

    Phases: 1=Research, 2=Debate, 3=Valuation, 4=Decision, 5=Signal
    """
    query: str
    current_phase: int = 0                    # 0=not started, 1-5=phases
    research_report: Optional[ResearchReport] = None
    debate_result: Optional[DebateResult] = None
    valuation_result: Optional[Any] = None    # ValuationResult (avoid circular import)
    decision: Optional[Decision] = None
    signal_report: Optional[Any] = None       # SignalReport (avoid circular import)
    scorecard: Optional[Any] = None           # Scorecard (avoid circular import)
    smart_summary: Optional[str] = None       # Formatted text summary
    summary_json: Optional[Dict] = None       # JSON summary for API/webhook
    errors: List[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.current_phase >= 5 and self.decision is not None

    def mark_complete(self):
        """Mark workflow as complete."""
        self.completed_at = datetime.now().isoformat()
