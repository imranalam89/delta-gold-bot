"""
OWEN — Macro & Tick Multi-Timeframe Divergence Filter (`owen_corr.py`)
----------------------------------------------------------------------
Tracks multi-timeframe momentum alignment (1M/5M/15M/1H ROC & CVD correlation)
and detects bullish/bearish exhaustion or continuation alignment.
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class OwenMomentumCorr:
    def __init__(self, name: str = "4:OWEN"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        roc_5m = float(bar.get("roc_5m", 0.0))
        roc_15m = float(bar.get("roc_15m", 0.0))
        roc_60m = float(bar.get("roc_60m", 0.0))
        cvd_div_bull = bool(bar.get("cvd_div_bull", False))
        cvd_div_bear = bool(bar.get("cvd_div_bear", False))
        vol_delta_z = float(bar.get("vol_delta_z", 0.0))

        # 1. Bullish MTF Alignment or Tick/CVD Bull Divergence
        if cvd_div_bull or (roc_5m > 0 and roc_15m > 0 and vol_delta_z >= 0.4):
            return AgentPacket(
                agent_name=self.name,
                state="BIAS_LEAN",
                direction="BUY",
                reason="Bullish MTF Momentum & Tick/CVD Alignment"
            )

        # 2. Bearish MTF Alignment or Tick/CVD Bear Divergence
        if cvd_div_bear or (roc_5m < 0 and roc_15m < 0 and vol_delta_z <= -0.4):
            return AgentPacket(
                agent_name=self.name,
                state="BIAS_LEAN",
                direction="SELL",
                reason="Bearish MTF Momentum & Tick/CVD Alignment"
            )

        return AgentPacket(
            agent_name=self.name,
            state="WAITING_NO_VISION",
            reason="Neutral Cross-Timeframe Divergence"
        )
