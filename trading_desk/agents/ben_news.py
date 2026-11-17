"""
BEN / CLARA — Red-Folder News Lockout Sentinel (CPI/NFP/FOMC Pre-News Shield)
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class BenNewsSentinel:
    def __init__(self, name: str = "1:BEN"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        news_lock = bool(bar.get("news_lockout", False))
        event_desc = str(bar.get("news_desc", "CLEAR"))

        # 1. HARD VETO: Within 5-Minute High-Impact News Window
        if news_lock or event_desc not in ("CLEAR", "NONE", ""):
            if news_lock:
                return AgentPacket(
                    agent_name=self.name,
                    state="HARD_VETO",
                    veto_target="ALL",
                    reason=f"High-Impact Red-Folder Economic Event Shield (CPI/NFP/FOMC)"
                )

        # 2. Neutral Abstention (News is clear, allow specialized floor setups to proceed)
        return AgentPacket(
            agent_name=self.name,
            state="WAITING_NO_VISION",
            reason="Macro Economic Schedule Clear"
        )
