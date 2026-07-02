"""
Hit Rate Recording System (命中率记录系统)

Records every analysis for future backtesting. After 3 months, automatically
evaluates whether the recommendation was correct.

Key features:
- Persist every analysis as an AnalysisRecord (JSONL storage)
- 3-month backtest: compare prediction vs actual outcome
- Monthly aggregate stats: hit rate, target accuracy, assumption accuracy
- Storage: local JSONL files (portable, no DB dependency)
"""

import json
import os
import uuid
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class AnalysisRecord:
    """A single analysis record for hit rate tracking."""
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    ticker: str = ""
    query: str = ""
    analysis_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Debate conclusion
    debate_verdict: str = "neutral"  # "bullish" | "bearish" | "neutral"
    bull_bear_ratio: float = 0.5
    key_disagreements: List[str] = field(default_factory=list)

    # Valuation
    current_price: Optional[float] = None
    bull_target: Optional[float] = None
    base_target: Optional[float] = None
    bear_target: Optional[float] = None
    weighted_target: Optional[float] = None
    margin_of_safety: Optional[str] = None

    # Decision
    recommendation: str = "持有"      # "买入" / "持有" / "卖出" etc
    confidence: float = 50.0
    key_risks: List[str] = field(default_factory=list)
    catalysts: List[str] = field(default_factory=list)

    # Key assumptions (for verification)
    key_assumptions: List[Dict] = field(default_factory=list)
    # e.g. [{"assumption": "AI Capex增速>30%", "confidence": "high"}]

    # Flip triggers
    flip_triggers: List[str] = field(default_factory=list)

    # Signals detected
    strong_signals: int = 0
    medium_signals: int = 0

    # === 3-month backtest fields (filled later) ===
    backtest_date: Optional[str] = None
    actual_price_3m: Optional[float] = None
    actual_return_3m: Optional[float] = None  # % return
    target_hit: Optional[bool] = None         # Did price reach base target?
    direction_correct: Optional[bool] = None  # Did price move in predicted direction?
    verdict_correct: Optional[bool] = None    # Overall assessment
    backtest_notes: Optional[str] = None


@dataclass
class BacktestSummary:
    """Monthly/aggregate backtest statistics."""
    period: str                         # "2026-07" or "all-time"
    total_records: int = 0
    backtested_records: int = 0
    pending_backtest: int = 0

    # Hit rates
    direction_hit_rate: Optional[float] = None   # % predictions correct direction
    target_hit_rate: Optional[float] = None      # % that hit target price
    avg_confidence: Optional[float] = None

    # Breakdowns
    buy_calls: int = 0
    buy_correct: int = 0
    sell_calls: int = 0
    sell_correct: int = 0
    hold_calls: int = 0


# =============================================================================
# Storage (JSONL file-based)
# =============================================================================

DEFAULT_RECORDS_DIR = Path(__file__).parent.parent / "data" / "records"


class RecordStore:
    """JSONL-based storage for analysis records."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or DEFAULT_RECORDS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._records_file = self.base_dir / "analysis_records.jsonl"

    def save(self, record: AnalysisRecord) -> str:
        """Append a record to storage. Returns record ID."""
        data = asdict(record)
        with open(self._records_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        return record.id

    def load_all(self) -> List[AnalysisRecord]:
        """Load all records from storage."""
        records = []
        if not self._records_file.exists():
            return records

        with open(self._records_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    records.append(self._dict_to_record(data))
                except (json.JSONDecodeError, TypeError):
                    continue
        return records

    def load_by_ticker(self, ticker: str) -> List[AnalysisRecord]:
        """Load records for a specific ticker."""
        return [r for r in self.load_all() if r.ticker.upper() == ticker.upper()]

    def load_pending_backtest(self) -> List[AnalysisRecord]:
        """Load records that are due for backtesting (>= 3 months old, not yet tested)."""
        cutoff = datetime.now() - timedelta(days=90)
        records = []
        for r in self.load_all():
            if r.backtest_date:
                continue  # Already backtested
            try:
                record_date = datetime.fromisoformat(r.timestamp)
                if record_date <= cutoff:
                    records.append(r)
            except (ValueError, TypeError):
                continue
        return records

    def update_record(self, record_id: str, updates: Dict) -> bool:
        """Update a record in-place (rewrite file). Returns success."""
        all_records = self.load_all()
        found = False
        for r in all_records:
            if r.id == record_id:
                for key, val in updates.items():
                    if hasattr(r, key):
                        setattr(r, key, val)
                found = True
                break

        if found:
            self._rewrite_all(all_records)
        return found

    def _rewrite_all(self, records: List[AnalysisRecord]):
        """Rewrite entire records file (used for updates)."""
        with open(self._records_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")

    def _dict_to_record(self, data: Dict) -> AnalysisRecord:
        """Convert dict to AnalysisRecord, handling missing fields."""
        valid_fields = {f.name for f in AnalysisRecord.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return AnalysisRecord(**filtered)


# =============================================================================
# Hit Rate Tracker
# =============================================================================

class HitRateTracker:
    """
    Main interface for the hit rate system.

    Usage:
        tracker = HitRateTracker()

        # After analysis completes:
        record_id = tracker.record_analysis(workflow_state)

        # Periodic backtest (e.g. daily cron):
        results = tracker.run_backtest()

        # Get stats:
        summary = tracker.get_summary()
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.store = RecordStore(base_dir)

    def record_analysis(self, state) -> str:
        """
        Record a completed analysis workflow for future backtesting.

        Args:
            state: WorkflowState from Orchestrator.run()

        Returns:
            Record ID for reference
        """
        record = AnalysisRecord(
            ticker=self._extract_ticker(state),
            query=state.query,
        )

        # Debate data
        if state.debate_result:
            d = state.debate_result
            record.bull_bear_ratio = d.bull_bear_ratio
            record.key_disagreements = d.disputes[:5]
            record.flip_triggers = d.flip_triggers[:3]
            if d.bull_bear_ratio > 0.55:
                record.debate_verdict = "bullish"
            elif d.bull_bear_ratio < 0.45:
                record.debate_verdict = "bearish"
            else:
                record.debate_verdict = "neutral"

        # Valuation data
        if state.valuation_result:
            v = state.valuation_result
            record.current_price = v.current_price
            record.weighted_target = v.weighted_target
            record.margin_of_safety = v.margin_of_safety
            for s in v.scenarios:
                if s.label == "Bull":
                    record.bull_target = s.target_price
                elif s.label == "Base":
                    record.base_target = s.target_price
                elif s.label == "Bear":
                    record.bear_target = s.target_price
            record.key_assumptions = v.key_assumptions[:5]

        # Decision data
        if state.decision:
            dec = state.decision
            record.recommendation = dec.recommendation.value
            record.confidence = dec.confidence
            record.key_risks = dec.key_risks[:5]
            record.catalysts = dec.catalysts[:5]

        # Signal data
        if state.signal_report:
            sr = state.signal_report
            record.strong_signals = len(sr.strong_signals)
            record.medium_signals = len(sr.medium_signals)

        # Save
        return self.store.save(record)

    def run_backtest(self, price_fetcher=None) -> List[Dict]:
        """
        Run backtest on records that are >= 3 months old.

        Args:
            price_fetcher: Optional function(ticker) -> float
                           If None, backtest is skipped (needs manual or API price)

        Returns:
            List of backtest results
        """
        pending = self.store.load_pending_backtest()
        results = []

        for record in pending:
            if not price_fetcher:
                # Without price data, we can only mark as pending
                results.append({
                    "id": record.id,
                    "ticker": record.ticker,
                    "status": "needs_price_data",
                    "analysis_date": record.analysis_date,
                })
                continue

            try:
                current_price = price_fetcher(record.ticker)
                result = self._evaluate_record(record, current_price)
                results.append(result)

                # Update the record with backtest results
                self.store.update_record(record.id, {
                    "backtest_date": datetime.now().strftime("%Y-%m-%d"),
                    "actual_price_3m": current_price,
                    "actual_return_3m": result.get("actual_return"),
                    "target_hit": result.get("target_hit"),
                    "direction_correct": result.get("direction_correct"),
                    "verdict_correct": result.get("verdict_correct"),
                    "backtest_notes": result.get("notes"),
                })
            except Exception as e:
                results.append({
                    "id": record.id,
                    "ticker": record.ticker,
                    "status": "error",
                    "error": str(e),
                })

        return results

    def _evaluate_record(self, record: AnalysisRecord, actual_price: float) -> Dict:
        """Evaluate a single record against actual price."""
        result = {
            "id": record.id,
            "ticker": record.ticker,
            "analysis_date": record.analysis_date,
            "recommendation": record.recommendation,
            "entry_price": record.current_price,
            "actual_price": actual_price,
            "status": "evaluated",
        }

        if record.current_price:
            actual_return = (actual_price / record.current_price - 1) * 100
            result["actual_return"] = actual_return

            # Direction check
            is_buy = record.recommendation in ("买入", "强烈买入")
            is_sell = record.recommendation in ("卖出", "强烈卖出")

            if is_buy:
                result["direction_correct"] = actual_return > 0
            elif is_sell:
                result["direction_correct"] = actual_return < 0
            else:  # Hold
                result["direction_correct"] = abs(actual_return) < 15  # Within ±15% = hold correct

            # Target hit check
            if record.base_target:
                if is_buy:
                    result["target_hit"] = actual_price >= record.base_target
                elif is_sell:
                    result["target_hit"] = actual_price <= record.bear_target if record.bear_target else False
                else:
                    result["target_hit"] = None

            # Overall verdict
            result["verdict_correct"] = result.get("direction_correct", False)

            # Notes
            notes = f"入场${record.current_price:.0f}→实际${actual_price:.0f} ({actual_return:+.1f}%)"
            if record.base_target:
                notes += f", Base目标${record.base_target:.0f}"
            result["notes"] = notes

        return result

    def get_summary(self, ticker: str = None) -> BacktestSummary:
        """
        Get aggregate backtest statistics.

        Args:
            ticker: If provided, filter to specific ticker. Otherwise all.

        Returns:
            BacktestSummary with hit rates and breakdown
        """
        if ticker:
            records = self.store.load_by_ticker(ticker)
        else:
            records = self.store.load_all()

        summary = BacktestSummary(
            period="all-time" if not ticker else f"{ticker}",
            total_records=len(records),
        )

        backtested = [r for r in records if r.backtest_date]
        pending = [r for r in records if not r.backtest_date]
        summary.backtested_records = len(backtested)
        summary.pending_backtest = len(pending)

        if not backtested:
            return summary

        # Calculate hit rates
        direction_correct = [r for r in backtested if r.direction_correct is True]
        target_hits = [r for r in backtested if r.target_hit is True]

        summary.direction_hit_rate = len(direction_correct) / len(backtested) * 100
        target_eligible = [r for r in backtested if r.target_hit is not None]
        if target_eligible:
            summary.target_hit_rate = len(target_hits) / len(target_eligible) * 100

        # Average confidence
        confidences = [r.confidence for r in backtested if r.confidence]
        if confidences:
            summary.avg_confidence = sum(confidences) / len(confidences)

        # Breakdown by recommendation
        for r in records:
            if r.recommendation in ("买入", "强烈买入"):
                summary.buy_calls += 1
                if r.direction_correct is True:
                    summary.buy_correct += 1
            elif r.recommendation in ("卖出", "强烈卖出"):
                summary.sell_calls += 1
                if r.direction_correct is True:
                    summary.sell_correct += 1
            else:
                summary.hold_calls += 1

        return summary

    def _extract_ticker(self, state) -> str:
        """Extract ticker from state."""
        if hasattr(state, 'valuation_result') and state.valuation_result:
            return getattr(state.valuation_result, 'ticker', 'UNKNOWN')
        # Fallback: try to find from query
        import re
        match = re.search(r'\$?([A-Z]{2,5})\b', state.query.upper())
        return match.group(1) if match else "UNKNOWN"
