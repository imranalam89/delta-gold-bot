"""
Syndicate Alpha — Core Blackboard State Manager
-----------------------------------------------
The central communication bus for all 16 trading agents.
Operates on a 5-Stage Peer-to-Peer Relay Pipeline so VICTOR (The Master Boss)
receives synthesized consensus signals instead of unorganized market noise.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class SetupCandidate:
    agent_name: str
    direction: str          # "LONG" or "SHORT"
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    confidence: float       # 0.0 to 1.0
    setup_type: str         # e.g., "EQL_SWEEP_FVG", "BEAR_TRAP", "VAH_BREAKOUT"
    invalidation_reason: str = ""


@dataclass
class BlackboardState:
    timestamp: datetime = field(default_factory=datetime.utcnow)
    current_price: float = 0.0
    
    # Stage 1: Macro & News (CLARA & ARTHUR)
    news_lockout_veto: bool = False
    news_event_desc: str = "CLEAR"
    regime: str = "BULLISH_TREND"     # "BULLISH_TREND", "BEARISH_TREND", "RANGE_SCALP", "CHOP_LOCKOUT"
    macro_bias: str = "LONG"          # "LONG", "SHORT", "NEUTRAL"
    adx_value: float = 0.0
    chop_index: float = 0.0
    candle_overlap_pct: float = 0.0
    internal_range_active: bool = False
    range_high_vah: float = 0.0
    range_low_val: float = 0.0
    poc_price: float = 0.0

    # Stage 2: Strategy Setup Hunters (MARCUS, NINA, MAX, LEO, KAI, ELENA)
    active_setups: List[SetupCandidate] = field(default_factory=list)
    setup_votes: Dict[str, float] = field(default_factory=dict)
    killzone_active: bool = False
    fib_ote_confluence: bool = False
    mss_confirmed_1m: bool = False

    # Stage 3: Order Flow & L2 Microstructure (SAM, OMAR, JACK)
    l2_bid_ask_imbalance: float = 1.0  # > 2.5:1 bullish, < 0.4:1 bearish
    passive_iceberg_detected: bool = False
    iceberg_price: float = 0.0
    current_spread_ticks: int = 1
    cvd_delta: float = 0.0
    cvd_divergence: bool = False
    vsa_stopping_volume: bool = False

    # Part 1: Field Agents (>60% Confidence Filter) & ANALYSER Agent (LUCAS)
    active_votes_over_60: Dict[str, str] = field(default_factory=dict)   # Only agents >60% sure ("BUY", "SELL", "WAIT")
    skipped_agents_under_60: List[str] = field(default_factory=list)     # Unclear agents (<=60% sure) skipped
    analyser_filtered_noise: str = "NONE"                                # e.g. "Filtered 1 BUY noise; forwarded 5 SELL & 5 WAIT"
    scalper_bypass_wait: bool = False                                    # Scalper/Sideways agent bypassed HTF WAIT vote

    # Part 2: Advisory Council (PSYCHOLOGIST, EXPERT TRADER, MATHEMATICIAN)
    sarah_risk_approved: bool = True
    sarah_veto_reason: str = ""
    psychologist_opinion: str = "APPROVED"
    daily_trades_count: int = 0
    daily_pnl_pct: float = 0.0
    david_veteran_approved: bool = True
    david_veto_reason: str = ""
    expert_trader_opinion: str = "APPROVED"
    ethan_math_approved: bool = True
    mathematician_opinion: str = "APPROVED"
    calculated_contract_qty: int = 1
    contract_symbol: str = "MGC"       # "MGC" or "GC"
    net_rr_ratio: float = 0.0

    # Part 3: CEO Master Agent (VICTOR) & Live Lifecycle (RYAN)
    victor_decision: str = "HOLD"      # "EXECUTE_LONG", "EXECUTE_SHORT", "SCALP_LONG", "SCALP_SHORT", "HOLD"
    consensus_score: float = 0.0       # 0% to 100%
    active_in_trade: bool = False
    in_trade_lifecycle_stage: str = "FLAT" # "PHASE_1_ARMED", "PHASE_2_BE", "PHASE_3_PARTIAL", "PHASE_4_RUNNER", "PHASE_5_EMERGENCY_EXIT"
    trade_entry_price: float = 0.0
    trade_active_sl: float = 0.0
    trade_tp1_price: float = 0.0


class Blackboard:
    """Thread-safe, observable central state manager."""
    def __init__(self):
        self.state = BlackboardState()
        self.history: List[BlackboardState] = []

    def reset_bar(self, timestamp: datetime, price: float):
        """Prepares state for a new bar/tick cycle while preserving in-trade & daily risk trackers."""
        in_trade = self.state.active_in_trade
        lifecycle = self.state.in_trade_lifecycle_stage
        entry_px = self.state.trade_entry_price
        sl_px = self.state.trade_active_sl
        tp1_px = self.state.trade_tp1_price
        daily_trades = self.state.daily_trades_count
        daily_pnl = self.state.daily_pnl_pct

        self.state = BlackboardState(
            timestamp=timestamp,
            current_price=price,
            active_in_trade=in_trade,
            in_trade_lifecycle_stage=lifecycle,
            trade_entry_price=entry_px,
            trade_active_sl=sl_px,
            trade_tp1_price=tp1_px,
            daily_trades_count=daily_trades,
            daily_pnl_pct=daily_pnl
        )

    def record_snapshot(self):
        self.history.append(self.state)
