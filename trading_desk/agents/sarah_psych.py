"""
SARAH — Trading Floor Senior Psychologist (Anti-FOMO, Emotional Discipline & Veto Shield)
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class SarahPsychologist:
    def __init__(self, name: str = "12:SARAH"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        rsi5 = float(bar.get("rsi_5m", 50.0))
        daily_loss_r = float(bar.get("daily_loss_r", 0.0))

        # 1. HARD VETO: Daily Mental State / Drawdown Circuit Breaker (-3R limit)
        if daily_loss_r <= -3.0:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="ALL",
                reason=f"Psychologist Circuit Breaker: Daily Drawdown Limit Reached ({daily_loss_r:.1f}R)"
            )

        # 2. HARD VETO: Buying Extreme Overbought FOMO Spike
        if rsi5 >= 78.0:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="BUY",
                reason=f"Psychologist Anti-FOMO Veto: Crowd Euphoria Spike (5m RSI = {rsi5:.1f} >= 78)"
            )

        # 3. HARD VETO: Shorting Extreme Oversold Panic Exhaustion
        if rsi5 <= 22.0:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="SELL",
                reason=f"Psychologist Anti-FOMO Veto: Crowd Panic Flush Bottom (5m RSI = {rsi5:.1f} <= 22)"
            )

        # 4. Neutral Abstention (Discipline intact, floor psychology healthy)
        return AgentPacket(
            agent_name=self.name,
            state="WAITING_NO_VISION",
            reason=f"Desk Psychology Clear (5m RSI={rsi5:.1f}, No FOMO/Tilt)"
        )
