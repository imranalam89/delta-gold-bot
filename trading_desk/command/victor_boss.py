"""
Syndicate Alpha — Victor Boss Command & Live 3-State Consensus Engine
---------------------------------------------------------------------
The institutional decision engine for the trading floor.
Implements:
1. Upcoming Conditional Setups (`PENDING_SETUP` with 0.5x lean, auto-upgrade to INSTANT_ACTION)
2. Neutral Abstention (`WAITING_NO_VISION` excluded from denominator)
3. Opposing Thesis & Veto Shield (`HARD_VETO` / conflict check)
4. Boosted Initiator (2.5x) + Active Majority Confirmation
5. Live state publishing to `/blackboard/live_state.json`
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os

DEFAULT_BLACKBOARD_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "blackboard",
    "live_state.json"
)


@dataclass
class AgentPacket:
    agent_name: str
    # States: "INSTANT_ACTION", "PENDING_SETUP", "BIAS_LEAN", "WAITING_NO_VISION", "HARD_VETO"
    state: str
    direction: str = "NONE"          # "BUY", "SELL", or "NONE"
    trigger_price: Optional[float] = None
    condition: Optional[str] = None  # "5M_CLOSE_ABOVE", "5M_CLOSE_BELOW", "1M_CLOSE_ABOVE", "1M_CLOSE_BELOW"
    ttl_bars: int = 6                # How many bars a PENDING_SETUP stays valid
    veto_target: str = "NONE"        # "BUY", "SELL", or "ALL"
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AgentPacket":
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in d.items() if k in valid_keys}
        return cls(**filtered)


class VictorBlackboardConsensus:
    """
    Live Floor Consensus Engine:
    - Tracks pre-announced PENDING_SETUP levels and auto-triggers them on candle close
    - Ignores WAITING_NO_VISION agents so abstentions don't dilute active setups
    - Vetoes any trade if another agent holds an opposing signal or HARD_VETO
    - Boosts INSTANT_ACTION initiator weight (2.5x) and verifies active majority confirmation
    """

    def __init__(self, initiator_boost: float = 2.5, pending_lean_mult: float = 0.5, blackboard_path: str = DEFAULT_BLACKBOARD_PATH, auto_publish_disk: bool = False):
        self.initiator_boost = initiator_boost
        self.pending_lean_mult = pending_lean_mult
        self.pending_book: Dict[str, AgentPacket] = {}
        self.blackboard_path = blackboard_path
        self.auto_publish_disk = auto_publish_disk
        self.last_decision: Dict[str, Any] = {}
        self.last_packets: Dict[str, AgentPacket] = {}

    def update_and_evaluate(
        self,
        new_packets: Dict[str, AgentPacket],
        bar_1m: Dict[str, float],
        bar_5m: Dict[str, float],
        edge_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        active_buys = []
        active_sells = []
        hard_vetoes = []
        upcoming_setups = []

        close_1m = float(bar_1m["close"])
        close_5m = float(bar_5m["close"])

        # Merge newly submitted packets with any still-active PENDING_SETUP watches
        combined_packets: Dict[str, AgentPacket] = {}
        expired_keys = []
        for name, pkt in list(self.pending_book.items()):
            pkt.ttl_bars -= 1
            if pkt.ttl_bars > 0:
                combined_packets[name] = pkt
            else:
                expired_keys.append(name)
        for k in expired_keys:
            self.pending_book.pop(k, None)

        for name, pkt in new_packets.items():
            combined_packets[name] = pkt
            if pkt.state == "PENDING_SETUP":
                self.pending_book[name] = pkt
            elif name in self.pending_book:
                del self.pending_book[name]

        self.last_packets = combined_packets

        # Evaluate every agent's current state
        for name, pkt in combined_packets.items():
            # Historical edge weight for current session + regime + timeframe (default 1.0)
            hist_edge_w = float(edge_weights.get(name, edge_weights.get(name.split(":")[-1], 1.0)))
            state = pkt.state

            # 1. Check if a PENDING_SETUP condition just triggered on this candle close
            if state == "PENDING_SETUP" and pkt.trigger_price is not None:
                triggered = False
                if pkt.condition == "5M_CLOSE_ABOVE" and close_5m >= pkt.trigger_price:
                    triggered = True
                elif pkt.condition == "5M_CLOSE_BELOW" and close_5m <= pkt.trigger_price:
                    triggered = True
                elif pkt.condition == "1M_CLOSE_ABOVE" and close_1m >= pkt.trigger_price:
                    triggered = True
                elif pkt.condition == "1M_CLOSE_BELOW" and close_1m <= pkt.trigger_price:
                    triggered = True

                if triggered:
                    state = "INSTANT_ACTION"
                    pkt.reason = f"TRIGGERED_PENDING ({pkt.condition} @ {pkt.trigger_price})"
                    self.pending_book.pop(name, None)
                else:
                    # Keep watching the level and register a 0.5x directional lean
                    upcoming_setups.append({
                        "agent": name,
                        "direction": pkt.direction,
                        "condition": pkt.condition,
                        "trigger_price": pkt.trigger_price,
                        "ttl_bars": pkt.ttl_bars,
                        "reason": pkt.reason
                    })
                    lean_w = hist_edge_w * self.pending_lean_mult
                    if pkt.direction == "BUY":
                        active_buys.append((name, lean_w, "PENDING_LEAN", pkt))
                    elif pkt.direction == "SELL":
                        active_sells.append((name, lean_w, "PENDING_LEAN", pkt))
                    continue

            # 2. Ignore agents with no clear vision right now (ABSTAIN = 0 weight)
            if state == "WAITING_NO_VISION":
                continue

            # 3. Collect Hard Vetoes (e.g., SAM opposing L2 wall, ARTHUR HTF ceiling, BEN news shield)
            if state == "HARD_VETO":
                hard_vetoes.append((name, pkt.veto_target, pkt.reason))
                continue

            # 4. Calculate Active Vote Weight (Boost 2.5x if INSTANT_ACTION)
            vote_w = hist_edge_w * self.initiator_boost if state == "INSTANT_ACTION" else hist_edge_w

            if pkt.direction == "BUY":
                active_buys.append((name, vote_w, state, pkt))
            elif pkt.direction == "SELL":
                active_sells.append((name, vote_w, state, pkt))

        # --- FLOOR CONSENSUS & VETO RESOLUTION ---
        buy_score = sum(w for _, w, _, _ in active_buys)
        sell_score = sum(w for _, w, _, _ in active_sells)

        buy_initiators = [a for a, _, s, _ in active_buys if s == "INSTANT_ACTION"]
        sell_initiators = [a for a, _, s, _ in active_sells if s == "INSTANT_ACTION"]

        # CASE A: An agent fired an instant BUY (or a Pending Buy Watch just triggered)
        if buy_initiators:
            blocking_vetoes = [
                f"{a}: {r}" for a, target, r in hard_vetoes if target in ("BUY", "ALL")
            ]
            opposing_sellers = [a for a, _, s, _ in active_sells if s in ("INSTANT_ACTION", "BIAS_LEAN")]

            # Veto immediately if any agent has a Hard Veto or is actively signaling SELL
            if blocking_vetoes or opposing_sellers:
                res = {
                    "decision": "VETOED_CONFLICT",
                    "side": "NONE",
                    "initiators": buy_initiators,
                    "blocked_by_vetoes": blocking_vetoes,
                    "blocked_by_opposing_agents": opposing_sellers,
                    "upcoming_setups": upcoming_setups,
                }
                self.last_decision = res
                self.publish_live_state(bar_1m, bar_5m, res)
                return res

            # Require the Initiator + at least 1 confirming agent (e.g., Price Action + L2)
            # AND verify at least one High-Edge DNA Core Specialist is actively confirming
            dna_core = {"8:ELENA", "7:DEREK", "2:MAYA", "4:NINA", "10:OMAR", "11:LIAM"}
            has_dna_core = any(any(core in a for core in dna_core) for a, _, _, _ in active_buys)

            if len(active_buys) >= 2 and buy_score > sell_score and has_dna_core:
                lead_pkt = next(p for _, _, s, p in active_buys if s == "INSTANT_ACTION")
                res = {
                    "decision": "EXECUTE_BUY",
                    "side": "LONG",
                    "initiators": buy_initiators,
                    "confirming_agents": [a for a, _, _, _ in active_buys],
                    "weighted_buy_score": round(buy_score, 2),
                    "stop_loss": lead_pkt.stop_loss,
                    "tp1": lead_pkt.tp1,
                    "tp2": lead_pkt.tp2,
                    "upcoming_setups": upcoming_setups,
                    "lead_packet": lead_pkt.to_dict()
                }
                self.last_decision = res
                self.publish_live_state(bar_1m, bar_5m, res)
                return res

        # CASE B: An agent fired an instant SELL (or a Pending Sell Watch just triggered)
        if sell_initiators:
            blocking_vetoes = [
                f"{a}: {r}" for a, target, r in hard_vetoes if target in ("SELL", "ALL")
            ]
            opposing_buyers = [a for a, _, s, _ in active_buys if s in ("INSTANT_ACTION", "BIAS_LEAN")]

            if blocking_vetoes or opposing_buyers:
                res = {
                    "decision": "VETOED_CONFLICT",
                    "side": "NONE",
                    "initiators": sell_initiators,
                    "blocked_by_vetoes": blocking_vetoes,
                    "blocked_by_opposing_agents": opposing_buyers,
                    "upcoming_setups": upcoming_setups,
                }
                self.last_decision = res
                self.publish_live_state(bar_1m, bar_5m, res)
                return res

            dna_core = {"8:ELENA", "7:DEREK", "2:MAYA", "4:NINA", "10:OMAR", "11:LIAM"}
            has_dna_core = any(any(core in a for core in dna_core) for a, _, _, _ in active_sells)

            if len(active_sells) >= 2 and sell_score > buy_score and has_dna_core:
                lead_pkt = next(p for _, _, s, p in active_sells if s == "INSTANT_ACTION")
                res = {
                    "decision": "EXECUTE_SELL",
                    "side": "SHORT",
                    "initiators": sell_initiators,
                    "confirming_agents": [a for a, _, _, _ in active_sells],
                    "weighted_sell_score": round(sell_score, 2),
                    "stop_loss": lead_pkt.stop_loss,
                    "tp1": lead_pkt.tp1,
                    "tp2": lead_pkt.tp2,
                    "upcoming_setups": upcoming_setups,
                    "lead_packet": lead_pkt.to_dict()
                }
                self.last_decision = res
                self.publish_live_state(bar_1m, bar_5m, res)
                return res

        # CASE C: No instant trigger yet -> Keep stalking upcoming setups
        res = {
            "decision": "WAIT_AND_STALK",
            "side": "NONE",
            "weighted_buy_score": round(buy_score, 2),
            "weighted_sell_score": round(sell_score, 2),
            "upcoming_setups": upcoming_setups,
        }
        self.last_decision = res
        self.publish_live_state(bar_1m, bar_5m, res)
        return res

    def publish_live_state(self, bar_1m: Dict[str, Any], bar_5m: Dict[str, Any], decision_info: Dict[str, Any], force: bool = False):
        """Serializes current trading floor blackboard to live_state.json for real-time monitoring."""
        if not (self.auto_publish_disk or force):
            return
        try:
            os.makedirs(os.path.dirname(self.blackboard_path), exist_ok=True)
            snapshot = {
                "timestamp": str(bar_1m.get("timestamp", datetime.utcnow().isoformat())),
                "close_1m": float(bar_1m.get("close", 0.0)),
                "close_5m": float(bar_5m.get("close", 0.0)),
                "decision": decision_info.get("decision", "WAIT_AND_STALK"),
                "side": decision_info.get("side", "NONE"),
                "weighted_buy_score": decision_info.get("weighted_buy_score", 0.0),
                "weighted_sell_score": decision_info.get("weighted_sell_score", 0.0),
                "initiators": decision_info.get("initiators", []),
                "confirming_agents": decision_info.get("confirming_agents", []),
                "blocked_by_vetoes": decision_info.get("blocked_by_vetoes", []),
                "blocked_by_opposing_agents": decision_info.get("blocked_by_opposing_agents", []),
                "upcoming_setups": decision_info.get("upcoming_setups", []),
                "active_pending_book": {k: v.to_dict() for k, v in self.pending_book.items()},
                "agents_packets": {k: v.to_dict() for k, v in self.last_packets.items()},
            }
            with open(self.blackboard_path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
        except Exception as e:
            # Non-blocking for high speed execution
            pass
