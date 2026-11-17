"""
ELENA — Price Action Wick Rejection, 1M MSS & Conditional Level Specialist
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class ElenaPriceAction:
    def __init__(self, name: str = "8:ELENA"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        close = float(bar.get("close", 0.0))
        open_px = float(bar.get("open", close))
        high = float(bar.get("high", close))
        low = float(bar.get("low", close))
        l_wick = float(bar.get("lower_wick_ratio", 0.0))
        u_wick = float(bar.get("upper_wick_ratio", 0.0))
        b_mss = bool(bar.get("bull_mss_1m", False))
        s_mss = bool(bar.get("bear_mss_1m", False))
        b_engulf = bool(bar.get("bull_engulf", False))
        s_engulf = bool(bar.get("bear_engulf", False))
        atr = float(bar.get("atr_5m", bar.get("atr_14", 3.5)))
        ema15 = float(bar.get("ema_15", close))

        # 1. INSTANT ACTION: Institutional Rejection Wick / Engulfing + Structural Reclaim
        if (l_wick >= 1.8 and close > open_px) or (b_engulf and close > ema15) or (l_wick >= 1.5 and b_mss and close > ema15):
            sl = round(min(low - 0.5, close - 1.65 * atr), 2)
            tp1 = round(close + 1.85 * (close - sl), 2)
            tp2 = round(close + 3.85 * (close - sl), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="BUY",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"Price Action {'Engulfing' if b_engulf else f'{l_wick:.1f}x Wick'} Reversal + MSS Reclaim"
            )

        if (u_wick >= 1.8 and close < open_px) or (s_engulf and close < ema15) or (u_wick >= 1.5 and s_mss and close < ema15):
            sl = round(max(high + 0.5, close + 1.65 * atr), 2)
            tp1 = round(close - 1.85 * (sl - close), 2)
            tp2 = round(close - 3.85 * (sl - close), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="SELL",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"Price Action {'Engulfing' if s_engulf else f'{u_wick:.1f}x Wick'} Reversal + MSS Breakdown"
            )

        # 2. PENDING SETUP: Announcing upcoming structural trigger level ahead of time
        sh20 = float(bar.get("swing_high_20", close + 3.0))
        sl20 = float(bar.get("swing_low_20", close - 3.0))

        if (sh20 - close) <= 1.2 and close < sh20:
            return AgentPacket(
                agent_name=self.name,
                state="PENDING_SETUP",
                direction="BUY",
                trigger_price=sh20,
                condition="5M_CLOSE_ABOVE",
                ttl_bars=6,
                stop_loss=round(sh20 - 1.25 * atr, 2),
                tp1=round(close + 2.0 * atr, 2),
                tp2=round(close + 3.8 * atr, 2),
                reason=f"Price Action: If 5m candle closes above {sh20:.2f}, trigger BUY"
            )

        if (close - sl20) <= 1.2 and close > sl20:
            return AgentPacket(
                agent_name=self.name,
                state="PENDING_SETUP",
                direction="SELL",
                trigger_price=sl20,
                condition="5M_CLOSE_BELOW",
                ttl_bars=6,
                stop_loss=round(sl20 + 1.25 * atr, 2),
                tp1=round(close - 2.0 * atr, 2),
                tp2=round(close - 3.8 * atr, 2),
                reason=f"Price Action: If 5m candle closes below {sl20:.2f}, trigger SELL"
            )

        # 3. BIAS LEAN: Microstructure lean
        if b_mss or (close > open_px and l_wick >= 1.3):
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="BUY", reason="Bullish Micro Wick Lean")
        if s_mss or (close < open_px and u_wick >= 1.3):
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="SELL", reason="Bearish Micro Wick Lean")

        # 4. Neutral Abstention
        return AgentPacket(agent_name=self.name, state="WAITING_NO_VISION", reason="Doji / No Clear Wick Vision")
