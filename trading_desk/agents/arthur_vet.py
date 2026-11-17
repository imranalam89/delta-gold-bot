"""
ARTHUR — Multi-Timeframe Regime, Chop Index (CHOP) & HTF Ceiling/Floor Veto Sentinel
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class ArthurRegimeVet:
    def __init__(self, name: str = "2:ARTHUR"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        close = float(bar.get("close", 0.0))
        chop = float(bar.get("chop_index", 50.0))
        adx = float(bar.get("adx", 20.0))
        ema200 = float(bar.get("ema_200", close))
        emad = float(bar.get("ema_daily", close))
        emam = float(bar.get("ema_macro", close))
        rh60 = float(bar.get("range_high_60", close + 10.0))
        rl60 = float(bar.get("range_low_60", close - 10.0))
        room_h240 = float(bar.get("room_to_high_240", 10.0))
        room_l240 = float(bar.get("room_to_low_240", 10.0))
        atr = float(bar.get("atr_5m", bar.get("atr_14", 3.5)))

        is_chop = chop > 56.0
        htf_bull = (ema200 > emad) and (close > emam)
        htf_bear = (ema200 < emad) and (close < emam)

        # 1. HARD VETO: Ceiling / Overextension Resistance against BUY
        if (close >= rh60 or room_h240 < 1.2 * atr) and (is_chop or adx < 22.0):
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="BUY",
                reason=f"1H/4H Range Ceiling / Low Room-to-Wall ({room_h240:.1f} pts, CHOP={chop:.1f})"
            )

        # 2. HARD VETO: Floor / Major Demand Support against SELL
        if (close <= rl60 or room_l240 < 1.2 * atr) and (is_chop or adx < 22.0):
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="SELL",
                reason=f"1H/4H Range Floor / Major Demand Support ({room_l240:.1f} pts, CHOP={chop:.1f})"
            )

        # 3. Macro Trend Directional Lean
        if not is_chop and adx >= 22.0:
            if htf_bull:
                return AgentPacket(
                    agent_name=self.name,
                    state="BIAS_LEAN",
                    direction="BUY",
                    reason=f"Aligned HTF Bull Trend (ADX={adx:.1f}, CHOP={chop:.1f})"
                )
            elif htf_bear:
                return AgentPacket(
                    agent_name=self.name,
                    state="BIAS_LEAN",
                    direction="SELL",
                    reason=f"Aligned HTF Bear Trend (ADX={adx:.1f}, CHOP={chop:.1f})"
                )

        # 4. Neutral Abstention (Chop or transition zone)
        return AgentPacket(
            agent_name=self.name,
            state="WAITING_NO_VISION",
            reason=f"Neutral / Transition Regime (CHOP={chop:.1f}, ADX={adx:.1f})"
        )
