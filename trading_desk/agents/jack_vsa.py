"""
JACK — Volume Spread Analysis (VSA) Z-Score Anomaly & Stopping Volume Specialist
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class JackVSASpecialist:
    def __init__(self, name: str = "11:JACK"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        vz = float(bar.get("vol_z_score", 0.0))
        stop_b = bool(bar.get("stopping_vol_bull", False))
        stop_s = bool(bar.get("stopping_vol_bear", False))
        l_wick = float(bar.get("lower_wick_ratio", 0.0))
        u_wick = float(bar.get("upper_wick_ratio", 0.0))
        close = float(bar.get("close", 0.0))
        atr = float(bar.get("atr_5m", bar.get("atr_14", 3.5)))

        # 1. HARD VETO: Dead tape / zero volume (slippage and false moves risk)
        if vz < -1.10:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="ALL",
                reason=f"Dead Tape Volume Anomaly (Vol Z-Score = {vz:.2f}σ)"
            )

        # 2. INSTANT ACTION: Institutional Stopping Volume Absorption
        if stop_b or (vz >= 1.5 and l_wick >= 1.5):
            sl = round(close - 1.15 * atr, 2)
            tp1 = round(close + 1.75 * (close - sl), 2)
            tp2 = round(close + 3.25 * (close - sl), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="BUY",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"VSA Stopping Volume Bull Absorption (Z={vz:.2f}σ, Wick={l_wick:.1f}x)"
            )

        if stop_s or (vz >= 1.5 and u_wick >= 1.5):
            sl = round(close + 1.15 * atr, 2)
            tp1 = round(close - 1.75 * (sl - close), 2)
            tp2 = round(close - 3.25 * (sl - close), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="SELL",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"VSA Stopping Volume Bear Absorption (Z={vz:.2f}σ, Wick={u_wick:.1f}x)"
            )

        # 3. BIAS LEAN: Volume Expansion
        if vz >= 1.10:
            d_bias = "BUY" if close > float(bar.get("open", close)) else "SELL"
            return AgentPacket(
                agent_name=self.name,
                state="BIAS_LEAN",
                direction=d_bias,
                reason=f"Institutional Volume Surge (+{vz:.2f}σ) in {d_bias} Candle"
            )

        # 4. Neutral Abstention
        return AgentPacket(
            agent_name=self.name,
            state="WAITING_NO_VISION",
            reason=f"Average Volume Pace (Z={vz:.2f}σ)"
        )
