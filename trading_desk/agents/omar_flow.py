"""
OMAR — Cumulative Volume Delta (CVD) Absorption & Delta Momentum Specialist
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class OmarOrderFlow:
    def __init__(self, name: str = "10:OMAR"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        d5 = float(bar.get("delta_sum_5", 0.0))
        d15 = float(bar.get("delta_sum_15", 0.0))
        b_abs = bool(bar.get("bull_absorption", False))
        s_abs = bool(bar.get("bear_absorption", False))
        close = float(bar.get("close", 0.0))
        atr = float(bar.get("atr_5m", bar.get("atr_14", 3.5)))

        # 1. HARD VETO: Violent opposing order flow continuation
        if d15 <= -180.0 and d5 <= -60.0:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="BUY",
                reason=f"Extreme Negative Order Flow Dump (15m CVD={d15:.0f}, 5m={d5:.0f})"
            )
        if d15 >= 180.0 and d5 >= 60.0:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="SELL",
                reason=f"Extreme Positive Order Flow Surge (15m CVD={d15:.0f}, 5m={d5:.0f})"
            )

        open_px = float(bar.get("open", close))
        l_wick = float(bar.get("lower_wick_ratio", 0.0))
        u_wick = float(bar.get("upper_wick_ratio", 0.0))

        # 2. INSTANT ACTION: Confirmed Passive Limit Absorption at Key Level
        if b_abs and d5 < -30 and (close > open_px or l_wick >= 1.4):
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
                reason=f"Bullish Limit Absorption (Aggressive Sells Absorbed, 5m Delta={d5:.0f})"
            )

        if s_abs and d5 > 30 and (close < open_px or u_wick >= 1.4):
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
                reason=f"Bearish Limit Absorption (Aggressive Buys Absorbed, 5m Delta={d5:.0f})"
            )

        # 3. BIAS LEAN: Aligned delta momentum
        if d5 > 40 and d15 > 0:
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="BUY", reason=f"Positive CVD Momentum (+{d5:.0f})")
        if d5 < -40 and d15 < 0:
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="SELL", reason=f"Negative CVD Momentum ({d5:.0f})")

        # 4. Neutral Abstention
        return AgentPacket(agent_name=self.name, state="WAITING_NO_VISION", reason="Flat Order Flow Delta")
