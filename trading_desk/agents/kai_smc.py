"""
KAI — 4H/1H Fibonacci Golden Pocket (61.8% - 78.6%) & OTE Confluence Specialist
"""

from typing import Dict, Any, Optional
from trading_desk.command.victor_boss import AgentPacket


class KaiFibSMC:
    def __init__(self, name: str = "7:KAI"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        fib_l = float(bar.get("fib_240_long", bar.get("fib_retracement_long", 0.0)))
        fib_s = float(bar.get("fib_240_short", bar.get("fib_retracement_short", 0.0)))
        close = float(bar.get("close", 0.0))
        atr = float(bar.get("atr_5m", bar.get("atr_14", 3.5)))
        l_wick = float(bar.get("lower_wick_ratio", 0.0))
        u_wick = float(bar.get("upper_wick_ratio", 0.0))
        b_mss = bool(bar.get("bull_mss_1m", False))
        s_mss = bool(bar.get("bear_mss_1m", False))
        macro_bull = bool(bar.get("macro_bull", close > float(bar.get("ema_macro", close))))

        # 1. INSTANT ACTION: Deep inside Golden Pocket with wick/MSS confirmation
        if macro_bull and 0.618 <= fib_l <= 0.786 and (l_wick >= 1.3 or b_mss):
            sl = round(close - 1.25 * atr, 2)
            tp1 = round(close + 1.75 * (close - sl), 2)
            tp2 = round(close + 3.25 * (close - sl), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="BUY",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"4H Golden Pocket ({fib_l*100:.1f}% Retracement) + Bull MSS/Wick"
            )

        if (not macro_bull) and 0.618 <= fib_s <= 0.786 and (u_wick >= 1.3 or s_mss):
            sl = round(close + 1.25 * atr, 2)
            tp1 = round(close - 1.75 * (sl - close), 2)
            tp2 = round(close - 3.25 * (sl - close), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="SELL",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"4H Golden Pocket ({fib_s*100:.1f}% Retracement) + Bear MSS/Wick"
            )

        # 2. PENDING SETUP: Approaching Golden Pocket zone (broadcast upcoming level ahead of time)
        if macro_bull and 0.52 <= fib_l < 0.618:
            target_entry = round(close - (0.618 - fib_l) * atr * 1.5, 2)
            return AgentPacket(
                agent_name=self.name,
                state="PENDING_SETUP",
                direction="BUY",
                trigger_price=target_entry,
                condition="1M_CLOSE_ABOVE",
                ttl_bars=8,
                stop_loss=round(target_entry - 1.25 * atr, 2),
                tp1=round(target_entry + 2.0 * atr, 2),
                tp2=round(target_entry + 4.0 * atr, 2),
                reason=f"Approaching 4H OTE Golden Pocket Long (Currently {fib_l*100:.1f}%)"
            )

        if (not macro_bull) and 0.52 <= fib_s < 0.618:
            target_entry = round(close + (0.618 - fib_s) * atr * 1.5, 2)
            return AgentPacket(
                agent_name=self.name,
                state="PENDING_SETUP",
                direction="SELL",
                trigger_price=target_entry,
                condition="1M_CLOSE_BELOW",
                ttl_bars=8,
                stop_loss=round(target_entry + 1.25 * atr, 2),
                tp1=round(target_entry - 2.0 * atr, 2),
                tp2=round(target_entry - 4.0 * atr, 2),
                reason=f"Approaching 4H OTE Golden Pocket Short (Currently {fib_s*100:.1f}%)"
            )

        # 3. Directional lean if in general discount/premium
        if fib_l >= 0.55:
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="BUY", reason="Discount 4H Fibonacci")
        if fib_s >= 0.55:
            return AgentPacket(agent_name=self.name, state="BIAS_LEAN", direction="SELL", reason="Premium 4H Fibonacci")

        # 4. Neutral Abstention
        return AgentPacket(agent_name=self.name, state="WAITING_NO_VISION", reason="No Golden Pocket / Mid-Range")
