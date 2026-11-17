"""
DAVID — 20-Year Institutional Veteran Trader (Spread & Structural Clearance Veto Shield)
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class DavidVeteranTrader:
    def __init__(self, name: str = "13:DAVID"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        spread = float(bar.get("avg_spread_pts", bar.get("spread", 0.10)))
        room_h = float(bar.get("room_to_high_240", 10.0))
        room_l = float(bar.get("room_to_low_240", 10.0))
        atr = float(bar.get("atr_5m", bar.get("atr_14", 3.5)))

        # 1. HARD VETO: Wide Spread Slippage Hazard
        if spread > 0.65:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="ALL",
                reason=f"Veteran Spread Veto: Dangerous Spread ({spread:.2f} pts > 0.65)"
            )

        # 2. HARD VETO: Insufficient Room to 4H Structure Wall
        min_room = 1.35 * atr
        if room_h < min_room:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="BUY",
                reason=f"Veteran Room-to-Wall Veto: Only {room_h:.1f} pts to 4H Resistance (Need >= {min_room:.1f})"
            )
        if room_l < min_room:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="SELL",
                reason=f"Veteran Room-to-Wall Veto: Only {room_l:.1f} pts to 4H Support (Need >= {min_room:.1f})"
            )

        # 3. Structural Clearance Lean
        if room_h >= 2.5 * min_room:
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="BUY", reason=f"Wide Open 4H Room (+{room_h:.1f} pts)")
        if room_l >= 2.5 * min_room:
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="SELL", reason=f"Wide Open 4H Room (+{room_l:.1f} pts)")

        # 4. Neutral Abstention
        return AgentPacket(
            agent_name=self.name,
            state="WAITING_NO_VISION",
            reason=f"Adequate Structural Clearance (Spread={spread:.2f} pts)"
        )
