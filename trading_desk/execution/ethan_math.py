"""
ETHAN — Senior Quantitative Mathematician ($5.00 Risk Sizing, Fee Validator & DTS Circuit Breakers)
--------------------------------------------------------------------------------------------------
Upgraded with Day-Trader-Skill (DTS) institutional guardrails:
1. Consecutive Loss Dampener (Halves risk from $5.00 to $2.50 after 2 consecutive stop-outs)
2. Daily Drawdown Circuit Breaker (Locks execution if daily loss exceeds limit)
3. Session Regime Gate (Enforces London / NY / Asian killzones, rejecting low-edge midday churn)
"""

from typing import Dict, Any, Optional


class EthanRiskMath:
    def __init__(
        self,
        fixed_risk_usd: float = 5.0,
        fee_rate: float = 0.0001,
        daily_loss_limit_usd: float = -15.0,
        enable_loss_dampener: bool = True
    ):
        self.fixed_risk_usd = fixed_risk_usd
        self.fee_rate = fee_rate  # 0.01% Delta Exchange fee per leg
        self.daily_loss_limit_usd = daily_loss_limit_usd
        self.enable_loss_dampener = enable_loss_dampener

    def check_session_killzone(self, est_hour: int) -> bool:
        """
        DTS Session Analog Filter:
        Rejects low-liquidity dead zones (12:00 - 16:59 EST).
        Permits London (02:00-07:59), NY Morning (08:00-11:59), and Asian Open (18:00-01:59).
        """
        if 12 <= est_hour <= 16:
            return False
        return True

    def size_trade(
        self,
        entry_price: float,
        stop_loss: Optional[float],
        tp1: Optional[float],
        tp2: Optional[float],
        direction: str,
        atr: float = 3.5,
        consec_losses: int = 0,
        daily_pnl_usd: float = 0.0,
        est_hour: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculates position size in ounces, applies DTS circuit breakers & dampeners,
        and accounts for Delta Exchange taker fees.
        """
        # 1. Daily Drawdown Circuit Breaker
        if daily_pnl_usd <= self.daily_loss_limit_usd:
            return {
                "approved": False,
                "reason": f"DTS Circuit Breaker: Daily Drawdown limit reached (${daily_pnl_usd:.2f} <= ${self.daily_loss_limit_usd:.2f})"
            }

        # 2. Session Analog Gate
        if est_hour is not None and not self.check_session_killzone(est_hour):
            return {
                "approved": False,
                "reason": f"DTS Session Gate: Hour {est_hour}:00 EST is outside high-edge killzone"
            }

        if stop_loss is None or stop_loss <= 0:
            stop_loss = round(entry_price - 1.20 * atr if direction == "LONG" else entry_price + 1.20 * atr, 2)

        sl_dist = abs(entry_price - stop_loss)
        if sl_dist < 0.50:
            sl_dist = 0.50

        # 3. Consecutive Loss Dampener (0.5x Risk on 2+ losses)
        effective_risk = self.fixed_risk_usd
        is_dampened = False
        if self.enable_loss_dampener and consec_losses >= 2:
            effective_risk = round(self.fixed_risk_usd * 0.50, 2)
            is_dampened = True

        qty_oz = round(effective_risk / sl_dist, 4)
        notional_entry = qty_oz * entry_price
        est_entry_fee = notional_entry * self.fee_rate

        # Default R:R targets if not provided by setup agent
        if tp1 is None:
            tp1 = round(entry_price + 1.65 * sl_dist if direction == "LONG" else entry_price - 1.65 * sl_dist, 2)
        if tp2 is None:
            tp2 = round(entry_price + 3.10 * sl_dist if direction == "LONG" else entry_price - 3.10 * sl_dist, 2)

        tp1_r = abs(tp1 - entry_price) / sl_dist
        tp2_r = abs(tp2 - entry_price) / sl_dist

        return {
            "entry_price": round(entry_price, 2),
            "stop_loss": round(stop_loss, 2),
            "tp1": round(tp1, 2),
            "tp2": round(tp2, 2),
            "risk_pts": round(sl_dist, 2),
            "qty_oz": qty_oz,
            "risk_usd": effective_risk,
            "is_dampened": is_dampened,
            "notional_usd": round(notional_entry, 2),
            "est_entry_fee_usd": round(est_entry_fee, 2),
            "tp1_r": round(tp1_r, 2),
            "tp2_r": round(tp2_r, 2),
            "fee_rate": self.fee_rate,
            "approved": True
        }
