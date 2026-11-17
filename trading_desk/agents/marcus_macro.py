"""
MARCUS — Macro Efficiency & Timeframe Expansion Specialist (`marcus_macro.py`)
------------------------------------------------------------------------------
Computes 1H/4H Kaufman Efficiency Ratio (`ker_1h`) + Timeframe Expansion Ratio (`ter_ratio = 1H_Box / 1M_ATR`).
Issues `HARD_VETO` if `ker_1h < 0.28` and `ter_ratio < 6.0` (Dead Chop).
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class MarcusMacro:
    def __init__(self, name: str = "1:MARCUS"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        ker_1h = float(bar.get("htf_ker_1h", bar.get("ker_1h", 0.35)))
        ter_ratio = float(bar.get("ter_ratio", 8.0))
        close = float(bar.get("close", 0.0))
        ema_60 = float(bar.get("ema_60", close))
        ema_240 = float(bar.get("ema_240", ema_60))

        # 1. HARD VETO: Dead Macro Compression & Chop
        if ker_1h < 0.28 and ter_ratio < 6.0:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="ALL",
                reason=f"Dead Chop Macro Veto (1H KER={ker_1h:.2f} < 0.28 & TER={ter_ratio:.1f} < 6.0)"
            )

        # 2. Strong Macro Trend Expansion Lean
        if ker_1h >= 0.42 or ter_ratio >= 9.5:
            if close > ema_60 and ema_60 >= ema_240:
                return AgentPacket(
                    agent_name=self.name,
                    state="BIAS_LEAN",
                    direction="BUY",
                    reason=f"Macro Bull Expansion (1H KER={ker_1h:.2f}, TER={ter_ratio:.1f})"
                )
            elif close < ema_60 and ema_60 <= ema_240:
                return AgentPacket(
                    agent_name=self.name,
                    state="BIAS_LEAN",
                    direction="SELL",
                    reason=f"Macro Bear Expansion (1H KER={ker_1h:.2f}, TER={ter_ratio:.1f})"
                )

        return AgentPacket(
            agent_name=self.name,
            state="WAITING_NO_VISION",
            reason=f"Tradable Macro Range (KER={ker_1h:.2f}, TER={ter_ratio:.1f})"
        )
