"""
MARCUS — Volume-Backed Value Area & Box Breakout Expansion Specialist
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class MarcusBreakoutSpecialist:
    def __init__(self, name: str = "3:MARCUS"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        close = float(bar.get("close", 0.0))
        sh20 = float(bar.get("swing_high_20", close + 5.0))
        sl20 = float(bar.get("swing_low_20", close - 5.0))
        rh60 = float(bar.get("range_high_60", close + 5.0))
        rl60 = float(bar.get("range_low_60", close - 5.0))
        vz = float(bar.get("vol_z_score", 0.0))
        d5 = float(bar.get("delta_sum_5", 0.0))
        atr = float(bar.get("atr_5m", bar.get("atr_14", 3.5)))
        chop = float(bar.get("chop_index", 50.0))

        # 1. INSTANT ACTION: Confirmed Expansion Breakout
        if close > sh20 and close > rh60 and vz >= 1.35 and d5 > 0 and chop < 55.0:
            sl = round(close - 1.15 * atr, 2)
            tp1 = round(close + 1.80 * (close - sl), 2)
            tp2 = round(close + 3.35 * (close - sl), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="BUY",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"True Box Breakout Expansion (Vol Z={vz:.2f}σ, Delta5={d5:.0f})"
            )

        if close < sl20 and close < rl60 and vz >= 1.35 and d5 < 0 and chop < 55.0:
            sl = round(close + 1.15 * atr, 2)
            tp1 = round(close - 1.80 * (sl - close), 2)
            tp2 = round(close - 3.35 * (sl - close), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="SELL",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"True Box Breakdown Expansion (Vol Z={vz:.2f}σ, Delta5={d5:.0f})"
            )

        # 2. PENDING SETUP: Range Compression Approaching Breakout Barrier
        if (rh60 - close) <= 1.0 and vz >= 0.8:
            return AgentPacket(
                agent_name=self.name,
                state="PENDING_SETUP",
                direction="BUY",
                trigger_price=rh60,
                condition="1M_CLOSE_ABOVE",
                ttl_bars=6,
                stop_loss=round(rh60 - 1.25 * atr, 2),
                tp1=round(close + 2.0 * atr, 2),
                tp2=round(close + 4.0 * atr, 2),
                reason=f"Stalking Value Area High Breakout at {rh60:.2f}"
            )

        if (close - rl60) <= 1.0 and vz >= 0.8:
            return AgentPacket(
                agent_name=self.name,
                state="PENDING_SETUP",
                direction="SELL",
                trigger_price=rl60,
                condition="1M_CLOSE_BELOW",
                ttl_bars=6,
                stop_loss=round(rl60 + 1.25 * atr, 2),
                tp1=round(close - 2.0 * atr, 2),
                tp2=round(close - 4.0 * atr, 2),
                reason=f"Stalking Value Area Low Breakdown at {rl60:.2f}"
            )

        # 3. Neutral Abstention
        return AgentPacket(
            agent_name=self.name,
            state="WAITING_NO_VISION",
            reason="Inside Range Value Area / No Breakout Energy"
        )
