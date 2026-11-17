"""
MAX — Failed Breakout / Bull & Bear Trap Reversal Specialist
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class MaxTrapSpecialist:
    def __init__(self, name: str = "5:MAX"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        close = float(bar.get("close", 0.0))
        high = float(bar.get("high", close))
        low = float(bar.get("low", close))
        open_px = float(bar.get("open", close))
        rh60 = float(bar.get("range_high_60", close + 5.0))
        rl60 = float(bar.get("range_low_60", close - 5.0))
        rpos = float(bar.get("range_pos_60", 0.5))
        u_liq = float(bar.get("upper_liq_score", 30.0))
        l_liq = float(bar.get("lower_liq_score", 30.0))
        atr = float(bar.get("atr_5m", bar.get("atr_14", 3.5)))
        vz = float(bar.get("vol_z_score", 0.0))

        # 1. INSTANT ACTION: Bull Trap at Range High (Price poked above rh60 and snapped back below)
        if high > rh60 and close < rh60 and close < open_px and u_liq >= 40.0 and vz >= 1.2:
            sl = round(max(high, close + 1.15 * atr), 2)
            tp1 = round(close - 1.75 * (sl - close), 2)
            tp2 = round(close - 3.25 * (sl - close), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="SELL",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"Bull Trap Reversal at Range High (VolZ={vz:.2f}, Liq={u_liq:.0f})"
            )

        # INSTANT ACTION: Bear Trap at Range Low (Price poked below rl60 and snapped back above)
        if low < rl60 and close > rl60 and close > open_px and l_liq >= 40.0 and vz >= 1.2:
            sl = round(min(low, close - 1.15 * atr), 2)
            tp1 = round(close + 1.75 * (close - sl), 2)
            tp2 = round(close + 3.25 * (close - sl), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="BUY",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"Bear Trap Reversal at Range Low (VolZ={vz:.2f}, Liq={l_liq:.0f})"
            )

        # 2. PENDING SETUP: Hovering near trap boundary
        if rpos >= 0.88:
            return AgentPacket(
                agent_name=self.name,
                state="PENDING_SETUP",
                direction="SELL",
                trigger_price=rh60,
                condition="1M_CLOSE_BELOW",
                ttl_bars=6,
                stop_loss=round(rh60 + 1.20 * atr, 2),
                tp1=round(close - 2.0 * atr, 2),
                tp2=round(close - 3.5 * atr, 2),
                reason="Stalking Bull Trap at Range Ceiling"
            )

        if rpos <= 0.12:
            return AgentPacket(
                agent_name=self.name,
                state="PENDING_SETUP",
                direction="BUY",
                trigger_price=rl60,
                condition="1M_CLOSE_ABOVE",
                ttl_bars=6,
                stop_loss=round(rl60 - 1.20 * atr, 2),
                tp1=round(close + 2.0 * atr, 2),
                tp2=round(close + 3.5 * atr, 2),
                reason="Stalking Bear Trap at Range Floor"
            )

        # 3. Directional lean
        if rpos <= 0.30:
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="BUY", reason="Lower Third of 60m Range")
        if rpos >= 0.70:
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="SELL", reason="Upper Third of 60m Range")

        # 4. Neutral Abstention
        return AgentPacket(agent_name=self.name, state="WAITING_NO_VISION", reason="Mid-Range Equilibrium")
