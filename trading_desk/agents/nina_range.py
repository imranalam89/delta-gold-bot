"""
NINA — Smart Money Concepts (SMC) Liquidity Sweep (EQH/EQL) & FVG Hunter
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class NinaSMCHunter:
    def __init__(self, name: str = "4:NINA"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        close = float(bar.get("close", 0.0))
        low = float(bar.get("low", close))
        high = float(bar.get("high", close))
        rl240 = float(bar.get("range_low_240", close - 10.0))
        rh240 = float(bar.get("range_high_240", close + 10.0))
        sl20 = float(bar.get("swing_low_20", close - 5.0))
        sh20 = float(bar.get("swing_high_20", close + 5.0))
        b_fvg = bool(bar.get("bull_fvg", False))
        s_fvg = bool(bar.get("bear_fvg", False))
        l_wick = float(bar.get("lower_wick_ratio", 0.0))
        u_wick = float(bar.get("upper_wick_ratio", 0.0))
        atr = float(bar.get("atr_5m", bar.get("atr_14", 3.5)))

        macro_bull = close > float(bar.get("ema_macro", close))
        vz = float(bar.get("vol_z_score", 0.0))

        # 1. INSTANT ACTION: Swept 4H/20-bar Equal Lows (EQL) + Reclaim with FVG / Wick in Macro Trend
        if macro_bull and (low <= rl240 or low <= sl20) and close > min(rl240, sl20) and (b_fvg or l_wick >= 1.5) and vz >= 1.05:
            sl = round(min(low, close - 1.15 * atr), 2)
            tp1 = round(close + 1.75 * (close - sl), 2)
            tp2 = round(close + 3.25 * (close - sl), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="BUY",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason="SMC EQL 4H/20M Sweep Reclaim + Bull FVG"
            )

        if (not macro_bull) and (high >= rh240 or high >= sh20) and close < max(rh240, sh20) and (s_fvg or u_wick >= 1.5) and vz >= 1.05:
            sl = round(max(high, close + 1.15 * atr), 2)
            tp1 = round(close - 1.75 * (sl - close), 2)
            tp2 = round(close - 3.25 * (sl - close), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="SELL",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason="SMC EQH 4H/20M Sweep Reclaim + Bear FVG"
            )

        # 2. PENDING SETUP: Pre-broadcasting upcoming sweep level
        if (close - sl20) <= 1.8 and close > sl20:
            return AgentPacket(
                agent_name=self.name,
                state="PENDING_SETUP",
                direction="BUY",
                trigger_price=sl20,
                condition="5M_CLOSE_ABOVE",
                ttl_bars=6,
                stop_loss=round(sl20 - 1.20 * atr, 2),
                tp1=round(close + 2.0 * atr, 2),
                tp2=round(close + 3.5 * atr, 2),
                reason=f"Stalking EQL Sweep at {sl20:.2f} (5m close back above)"
            )

        if (sh20 - close) <= 1.8 and close < sh20:
            return AgentPacket(
                agent_name=self.name,
                state="PENDING_SETUP",
                direction="SELL",
                trigger_price=sh20,
                condition="5M_CLOSE_BELOW",
                ttl_bars=6,
                stop_loss=round(sh20 + 1.20 * atr, 2),
                tp1=round(close - 2.0 * atr, 2),
                tp2=round(close - 3.5 * atr, 2),
                reason=f"Stalking EQH Sweep at {sh20:.2f} (5m close back below)"
            )

        # 3. Directional Lean if FVG active
        if b_fvg:
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="BUY", reason="Bullish 3-Bar FVG Support")
        if s_fvg:
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="SELL", reason="Bearish 3-Bar FVG Resistance")

        # 4. Neutral Abstention
        return AgentPacket(agent_name=self.name, state="WAITING_NO_VISION", reason="No Active Liquidity Pool / No FVG")
