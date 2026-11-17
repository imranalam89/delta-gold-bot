"""
SAM — Level-2 MBP-10 DOM & Institutional Liquidity Wall Sentinel
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class SamOrderBookDOM:
    def __init__(self, name: str = "9:SAM"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        has_l2 = bool(bar.get("has_real_l2", False))
        l2_mean = float(bar.get("l2_bid_ask_ratio_mean", 1.0))
        l2_max = float(bar.get("l2_bid_ask_ratio_max", 1.5))
        u_liq = float(bar.get("upper_liq_score", 30.0))
        l_liq = float(bar.get("lower_liq_score", 30.0))
        close = float(bar.get("close", 0.0))
        room_h = float(bar.get("room_to_high_60", 5.0))
        room_l = float(bar.get("room_to_low_60", 5.0))
        u_grab = bool(bar.get("upper_liq_grabbed", False))
        l_grab = bool(bar.get("lower_liq_grabbed", False))

        # 1. HARD VETO: Direct Opposing L2 Wall Blocking Path
        if has_l2 and l2_mean <= 0.80:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="BUY",
                reason=f"Opposing Level-2 Ask Wall Overhead (Bid/Ask={l2_mean:.2f})"
            )
        if has_l2 and l2_mean >= 1.25:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="SELL",
                reason=f"Opposing Level-2 Bid Wall Underneath (Bid/Ask={l2_mean:.2f})"
            )

        # Proximity Veto: Heavy untouched liquidity magnet blocking immediate path (< 2.2 pts)
        if u_liq >= 48.0 and room_h < 2.0 and not u_grab:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="BUY",
                reason=f"Resting Ask Liquidity Wall at {room_h:.1f} pts Overhead (Score={u_liq:.0f})"
            )
        if l_liq >= 48.0 and room_l < 2.0 and not l_grab:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="SELL",
                reason=f"Resting Bid Liquidity Wall at {room_l:.1f} pts Underneath (Score={l_liq:.0f})"
            )

        # 2. INSTANT ACTION / BIAS LEAN: Heavy Order Book Imbalance in Favor of Trend
        if has_l2 and (l2_mean >= 1.15 or l2_max >= 2.0) and room_h >= 3.5:
            return AgentPacket(
                agent_name=self.name,
                state="BIAS_LEAN",
                direction="BUY",
                reason=f"L2 Bid Book Depth Imbalance ({l2_mean:.2f}:1, Peak={l2_max:.1f})"
            )

        if has_l2 and (l2_mean <= 0.88 or l2_max <= 0.5) and room_l >= 3.5:
            return AgentPacket(
                agent_name=self.name,
                state="BIAS_LEAN",
                direction="SELL",
                reason=f"L2 Ask Book Depth Imbalance ({l2_mean:.2f}:1)"
            )

        # 3. Liquidity Magnet Pull
        if u_liq >= 45.0 and room_h >= 4.0:
            return AgentPacket(
                agent_name=self.name,
                state="BIAS_LEAN",
                direction="BUY",
                reason=f"Upper Liquidity Magnet Target (+{room_h:.1f} pts room, Score={u_liq:.0f})"
            )
        if l_liq >= 45.0 and room_l >= 4.0:
            return AgentPacket(
                agent_name=self.name,
                state="BIAS_LEAN",
                direction="SELL",
                reason=f"Lower Liquidity Magnet Target (+{room_l:.1f} pts room, Score={l_liq:.0f})"
            )

        # 4. Neutral Abstention
        return AgentPacket(
            agent_name=self.name,
            state="WAITING_NO_VISION",
            reason="Balanced Level-2 Order Book / Moderate Liquidity"
        )
