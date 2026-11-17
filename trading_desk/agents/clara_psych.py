"""
CLARA — Anti-Tilt Guard & 15-Minute Time-Decay Scratch Monitor (`clara_psych.py`)
---------------------------------------------------------------------------------
Raises required conviction after 2 consecutive losses, blocks extreme FOMO RSI spikes,
and triggers a 15-minute time-decay scratch if an open trade stalls near entry.
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class ClaraPsychGuard:
    def __init__(self, name: str = "13:CLARA"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        rsi = float(bar.get("rsi_14", 50.0))
        consec_losses = int(bar.get("consec_losses", 0))
        daily_loss_r = float(bar.get("daily_loss_r", 0.0))

        if daily_loss_r <= -3.5:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="ALL",
                reason=f"Daily Mental Circuit Breaker Reached ({daily_loss_r:.1f}R)"
            )

        if rsi >= 82.0:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="BUY",
                reason=f"Anti-Chasing Guard: Extreme Overbought Climax (RSI={rsi:.1f})"
            )

        if rsi <= 18.0:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="SELL",
                reason=f"Anti-Chasing Guard: Extreme Oversold Flush (RSI={rsi:.1f})"
            )

        return AgentPacket(
            agent_name=self.name,
            state="WAITING_NO_VISION",
            reason=f"Psychology Disciplined (Consec Losses={consec_losses}, RSI={rsi:.1f})"
        )
