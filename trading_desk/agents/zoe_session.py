"""
ZOE — Session & Time-of-Day Volatility Profiler (`zoe_session.py`)
------------------------------------------------------------------
Profiles `ASIA`, `LONDON_OPEN`, `NY_OPEN`, `LONDON_CLOSE`, and vetoes low-liquidity
dead rollover windows (`16:00 - 17:59 EST`).
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class ZoeSessionProfiler:
    def __init__(self, name: str = "10:ZOE"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        est_hr = int(bar.get("est_hour", 9))
        session_name = str(bar.get("session_name", "NY_OPEN"))
        roc_15m = float(bar.get("roc_15m", 0.0))

        # 1. HARD VETO: CME Globex Maintenance / Post-Close Dead Window (16:00 - 17:59 EST)
        if 16 <= est_hr <= 17:
            return AgentPacket(
                agent_name=self.name,
                state="HARD_VETO",
                veto_target="ALL",
                reason=f"CME Globex Rollover / Illiquid Dead Window ({est_hr}:00 EST)"
            )

        # 2. High-Velocity Killzone Bias Lean
        if session_name in ("LONDON_OPEN", "NY_OPEN", "LONDON_CLOSE", "ASIA"):
            if abs(roc_15m) >= 0.8:
                d = "BUY" if roc_15m > 0 else "SELL"
                return AgentPacket(
                    agent_name=self.name,
                    state="BIAS_LEAN",
                    direction=d,
                    reason=f"Active {session_name} Killzone Flow ({d})"
                )

        return AgentPacket(
            agent_name=self.name,
            state="WAITING_NO_VISION",
            reason=f"Session {session_name} ({est_hr}:00 EST) Normal Volatility"
        )
