"""
RYAN — Dynamic 5-Phase Trade Lifecycle & Order Execution Engine
"""

from typing import Dict, Any, Optional, List


class RyanExecutionLifecycle:
    def __init__(
        self,
        be_trigger_r: float = 1.80,
        be_lock_r: float = 0.38,
        stall_trigger_r: float = 1.05,
        stall_bars: int = 6,
        stall_lock_r: float = 0.28,
        trail_trigger_r: float = 2.50,
        trail_dist_r: float = 0.85,
        max_hold_mins: int = 270,
        fee_rate: float = 0.0001,
    ):
        self.be_trigger_r = be_trigger_r
        self.be_lock_r = be_lock_r
        self.stall_trigger_r = stall_trigger_r
        self.stall_bars = stall_bars
        self.stall_lock_r = stall_lock_r
        self.trail_trigger_r = trail_trigger_r
        self.trail_dist_r = trail_dist_r
        self.max_hold_mins = max_hold_mins
        self.fee_rate = fee_rate
        self.active_trade: Optional[Dict[str, Any]] = None

    def is_in_trade(self) -> bool:
        return self.active_trade is not None

    def open_trade(self, decision: Dict[str, Any], sized_order: Dict[str, Any], bar_idx: int, timestamp: Any) -> Dict[str, Any]:
        direction = decision["side"]
        entry_px = sized_order["entry_price"]
        sl_px = sized_order["stop_loss"]
        tp1_px = sized_order["tp1"]
        tp2_px = sized_order["tp2"]
        risk_pts = sized_order["risk_pts"]
        qty_oz = sized_order["qty_oz"]

        self.active_trade = {
            "entry_idx": bar_idx,
            "entry_time": timestamp,
            "direction": direction,
            "entry_price": entry_px,
            "sl_price": sl_px,
            "tp1_price": tp1_px,
            "tp2_price": tp2_px,
            "init_risk_pts": risk_pts,
            "qty_oz": qty_oz,
            "risk_usd": sized_order["risk_usd"],
            "initiators": decision.get("initiators", []),
            "confirming_agents": decision.get("confirming_agents", []),
            "stage": "PHASE_1_ARMED",
            "peak_r": 0.0,
            "banked_pts": 0.0,
            "rem_weight": 1.0,
        }
        return self.active_trade

    def update_lifecycle(self, bar: Dict[str, Any], bar_idx: int) -> Optional[Dict[str, Any]]:
        """
        Updates in-trade stop adjustments, partials, and evaluates exit triggers on this bar.
        Returns trade log dict if trade exited, otherwise None.
        """
        if self.active_trade is None:
            return None

        t = self.active_trade
        direction = t["direction"]
        entry_px = t["entry_price"]
        init_risk = t["init_risk_pts"]
        stage = t["stage"]
        tp1_px = t["tp1_price"]
        tp2_px = t["tp2_price"]

        high = float(bar["high"])
        low = float(bar["low"])
        close = float(bar["close"])
        bars_held = bar_idx - t["entry_idx"]

        exit_px = None
        exit_reason = None

        if direction == "LONG":
            cur_mfe_r = (high - entry_px) / init_risk
            cur_r = (close - entry_px) / init_risk
            if cur_mfe_r > t["peak_r"]:
                t["peak_r"] = cur_mfe_r

            # Stop loss or trailing stop hit
            if low <= t["sl_price"]:
                exit_px = t["sl_price"]
                exit_reason = "STOP_LOSS" if stage == "PHASE_1_ARMED" else f"TRAIL_STOP ({stage})"
            elif high >= tp2_px:
                exit_px = tp2_px
                exit_reason = "TP2_FULL_RUNNER_TARGET"
            else:
                # Stall-Lock (+1.05R MFE with stall for 6 bars -> lock +0.28R)
                if stage == "PHASE_1_ARMED" and cur_mfe_r >= self.stall_trigger_r:
                    if bars_held >= self.stall_bars and cur_r <= 0.45:
                        t["sl_price"] = max(t["sl_price"], entry_px + self.stall_lock_r * init_risk)
                        t["stage"] = "PHASE_2_BREAKEVEN"
                        stage = "PHASE_2_BREAKEVEN"

                # Phase 2 Break-Even Lock
                if stage == "PHASE_1_ARMED" and (high - entry_px) >= self.be_trigger_r * init_risk:
                    t["sl_price"] = max(t["sl_price"], entry_px + self.be_lock_r * init_risk)
                    t["stage"] = "PHASE_2_BREAKEVEN"
                    stage = "PHASE_2_BREAKEVEN"

                # Phase 3/4 Partial TP1 + Structure Runner Trail
                if stage in ("PHASE_1_ARMED", "PHASE_2_BREAKEVEN") and high >= tp1_px:
                    partial_pts = tp1_px - entry_px
                    t["banked_pts"] += 0.50 * partial_pts
                    t["rem_weight"] = 0.50
                    t["sl_price"] = max(t["sl_price"], entry_px + 0.45 * init_risk)
                    t["stage"] = "PHASE_4_STRUCTURE_RUNNER"
                    stage = "PHASE_4_STRUCTURE_RUNNER"
                elif stage == "PHASE_4_STRUCTURE_RUNNER":
                    if (high - entry_px) >= self.trail_trigger_r * init_risk:
                        trail_px = close - self.trail_dist_r * init_risk
                        if trail_px > t["sl_price"]:
                            t["sl_price"] = trail_px

        else:  # SHORT
            cur_mfe_r = (entry_px - low) / init_risk
            cur_r = (entry_px - close) / init_risk
            if cur_mfe_r > t["peak_r"]:
                t["peak_r"] = cur_mfe_r

            if high >= t["sl_price"]:
                exit_px = t["sl_price"]
                exit_reason = "STOP_LOSS" if stage == "PHASE_1_ARMED" else f"TRAIL_STOP ({stage})"
            elif low <= tp2_px:
                exit_px = tp2_px
                exit_reason = "TP2_FULL_RUNNER_TARGET"
            else:
                if stage == "PHASE_1_ARMED" and cur_mfe_r >= self.stall_trigger_r:
                    if bars_held >= self.stall_bars and cur_r <= 0.45:
                        t["sl_price"] = min(t["sl_price"], entry_px - self.stall_lock_r * init_risk)
                        t["stage"] = "PHASE_2_BREAKEVEN"
                        stage = "PHASE_2_BREAKEVEN"

                if stage == "PHASE_1_ARMED" and (entry_px - low) >= self.be_trigger_r * init_risk:
                    t["sl_price"] = min(t["sl_price"], entry_px - self.be_lock_r * init_risk)
                    t["stage"] = "PHASE_2_BREAKEVEN"
                    stage = "PHASE_2_BREAKEVEN"

                if stage in ("PHASE_1_ARMED", "PHASE_2_BREAKEVEN") and low <= tp1_px:
                    partial_pts = entry_px - tp1_px
                    t["banked_pts"] += 0.50 * partial_pts
                    t["rem_weight"] = 0.50
                    t["sl_price"] = min(t["sl_price"], entry_px - 0.45 * init_risk)
                    t["stage"] = "PHASE_4_STRUCTURE_RUNNER"
                    stage = "PHASE_4_STRUCTURE_RUNNER"
                elif stage == "PHASE_4_STRUCTURE_RUNNER":
                    if (entry_px - low) >= self.trail_trigger_r * init_risk:
                        trail_px = close + self.trail_dist_r * init_risk
                        if trail_px < t["sl_price"]:
                            t["sl_price"] = trail_px

        # Max hold time exit
        if exit_px is None and bars_held >= self.max_hold_mins:
            exit_px = close
            exit_reason = f"TIME_EXIT_{self.max_hold_mins}M"

        if exit_px is not None:
            rem_pts = (exit_px - entry_px) if direction == "LONG" else (entry_px - exit_px)
            total_pts = t["banked_pts"] + t["rem_weight"] * rem_pts
            r_mult = total_pts / max(init_risk, 0.50)
            gross_usd = r_mult * t["risk_usd"]

            # Exact 0.01% Delta Exchange fee per leg
            qty_oz = t["qty_oz"]
            entry_notional = qty_oz * entry_px
            exit_notional = qty_oz * (0.50 * tp1_px + 0.50 * exit_px) if t["rem_weight"] < 1.0 else qty_oz * exit_px
            fee_usd = self.fee_rate * (entry_notional + exit_notional)
            net_usd = gross_usd - fee_usd

            log = {
                "entry_idx": t["entry_idx"],
                "exit_idx": bar_idx,
                "entry_time": str(t["entry_time"]),
                "exit_time": str(bar.get("timestamp", bar_idx)),
                "direction": direction,
                "initiators": t["initiators"],
                "confirming_agents": t["confirming_agents"],
                "entry_price": round(entry_px, 2),
                "exit_price": round(exit_px, 2),
                "sl_price": round(t["sl_price"], 2),
                "tp1_price": round(tp1_px, 2),
                "tp2_price": round(tp2_px, 2),
                "init_risk_pts": round(init_risk, 2),
                "pnl_pts": round(total_pts, 2),
                "r_multiple": round(r_mult, 2),
                "qty_oz": round(qty_oz, 4),
                "gross_pnl_usd": round(gross_usd, 2),
                "delta_fee_usd": round(fee_usd, 2),
                "net_pnl_usd": round(net_usd, 2),
                "peak_r": round(t["peak_r"], 2),
                "exit_reason": exit_reason,
                "bars_held": bars_held,
            }
            self.active_trade = None
            return log

        return None
