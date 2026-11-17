"""
ELENA — Session VWAP Magnet & +/- 2.0 SD Mean-Reversion / Extension Specialist (`elena_vwap.py`)
------------------------------------------------------------------------------------------------
Tracks Session VWAP and standard deviation bands (+/- 2.0 SD) alongside price action wick rejection.
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class ElenaVWAP:
    def __init__(self, name: str = "9:ELENA"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        close = float(bar.get("close", 0.0))
        open_px = float(bar.get("open", close))
        vwap_z = float(bar.get("vwap_z_score", 0.0))
        l_wick = float(bar.get("lower_wick_ratio", 0.0))
        u_wick = float(bar.get("upper_wick_ratio", 0.0))
        atr = float(bar.get("atr_14", 3.5))
        ker_1h = float(bar.get("htf_ker_1h", 0.35))

        sl_dist = max(5.5, min(9.0, 1.35 * atr))

        # 1. INSTANT ACTION: Extreme -2.0 SD Lower Band Fade or VWAP Trend Bounce
        if (vwap_z <= -1.85 and close > open_px and l_wick >= 0.30) or (
            -0.45 <= vwap_z <= 0.35 and ker_1h >= 0.38 and close > open_px and l_wick >= 0.35
        ):
            sl = round(close - sl_dist, 2)
            tp1 = round(close + 1.75 * sl_dist, 2)
            tp2 = round(close + 3.40 * sl_dist, 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="BUY",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"VWAP Band Reclaim / Pullback Buy (VWAP Z={vwap_z:.2f} SD, Wick={l_wick:.2f})"
            )

        # 2. INSTANT ACTION: Extreme +2.0 SD Upper Band Fade or VWAP Trend Reject
        if (vwap_z >= 1.85 and close < open_px and u_wick >= 0.30) or (
            -0.35 <= vwap_z <= 0.45 and ker_1h >= 0.38 and close < open_px and u_wick >= 0.35
        ):
            sl = round(close + sl_dist, 2)
            tp1 = round(close - 1.75 * sl_dist, 2)
            tp2 = round(close - 3.40 * sl_dist, 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="SELL",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"VWAP Band Reject / Pullback Sell (VWAP Z={vwap_z:.2f} SD, Wick={u_wick:.2f})"
            )

        # 3. BIAS LEAN
        if vwap_z <= -1.15 or (vwap_z > 0.15 and close > open_px):
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="BUY", reason=f"Bullish VWAP Structure (Z={vwap_z:.2f})")
        if vwap_z >= 1.15 or (vwap_z < -0.15 and close < open_px):
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="SELL", reason=f"Bearish VWAP Structure (Z={vwap_z:.2f})")

        return AgentPacket(agent_name=self.name, state="WAITING_NO_VISION", reason="VWAP Equilibrium")
