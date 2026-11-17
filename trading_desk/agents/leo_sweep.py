"""
LEO — ICT London/NY Killzone & Silver Bullet Timing Specialist
"""

from typing import Dict, Any
from trading_desk.command.victor_boss import AgentPacket


class LeoKillzoneSweep:
    def __init__(self, name: str = "6:LEO"):
        self.name = name

    def evaluate(self, bar: Dict[str, Any]) -> AgentPacket:
        in_kz = bool(bar.get("in_killzone", False)) or bool(bar.get("in_asia_kz", False))
        sb = bool(bar.get("silver_bullet", False)) or bool(bar.get("silver_bullet_asia", False))
        close = float(bar.get("close", 0.0))
        atr = float(bar.get("atr_5m", bar.get("atr_14", 3.5)))
        l_grab = bool(bar.get("lower_liq_grabbed", False))
        u_grab = bool(bar.get("upper_liq_grabbed", False))
        b_mss = bool(bar.get("bull_mss_1m", False))
        s_mss = bool(bar.get("bear_mss_1m", False))

        # 1. INSTANT ACTION: Active Killzone / Silver Bullet + Confirmed Liquidity Grab & Reclaim
        if (in_kz or sb) and l_grab and b_mss:
            sl = round(close - 1.65 * atr, 2)
            tp1 = round(close + 1.85 * (close - sl), 2)
            tp2 = round(close + 4.25 * (close - sl), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="BUY",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"Killzone/SilverBullet Bullish Sweep Reversal (MSS Confirmed)"
            )

        if (in_kz or sb) and u_grab and s_mss:
            sl = round(close + 1.65 * atr, 2)
            tp1 = round(close - 1.85 * (sl - close), 2)
            tp2 = round(close - 4.25 * (sl - close), 2)
            return AgentPacket(
                agent_name=self.name,
                state="INSTANT_ACTION",
                direction="SELL",
                stop_loss=sl,
                tp1=tp1,
                tp2=tp2,
                reason=f"Killzone/SilverBullet Bearish Sweep Reversal (MSS Confirmed)"
            )

        # 2. PENDING SETUP: Stalking high-impact sweep level
        rl60 = float(bar.get("range_low_60", close - 5.0))
        rh60 = float(bar.get("range_high_60", close + 5.0))
        if in_kz and (close - rl60) <= 1.5 and not l_grab:
            return AgentPacket(
                agent_name=self.name,
                state="PENDING_SETUP",
                direction="BUY",
                trigger_price=rl60,
                condition="1M_CLOSE_ABOVE",
                ttl_bars=6,
                stop_loss=round(rl60 - 1.20 * atr, 2),
                tp1=round(close + 1.80 * atr, 2),
                tp2=round(close + 3.50 * atr, 2),
                reason="Stalking Asian/London Low Liquidity Sweep"
            )

        if in_kz and (rh60 - close) <= 1.5 and not u_grab:
            return AgentPacket(
                agent_name=self.name,
                state="PENDING_SETUP",
                direction="SELL",
                trigger_price=rh60,
                condition="1M_CLOSE_BELOW",
                ttl_bars=6,
                stop_loss=round(rh60 + 1.20 * atr, 2),
                tp1=round(close - 1.80 * atr, 2),
                tp2=round(close - 3.50 * atr, 2),
                reason="Stalking Asian/London High Liquidity Sweep"
            )

        # 3. BIAS LEAN: In active high-volume window
        if sb or in_kz:
            dir_bias = "BUY" if close > float(bar.get("ema_50", close)) else "SELL"
            return AgentPacket(
                agent_name=self.name,
                state="BIAS_LEAN",
                direction=dir_bias,
                reason=f"Active Killzone/Silver Bullet Window ({dir_bias} Momentum)"
            )

        # 4. Neutral Abstention
        return AgentPacket(
            agent_name=self.name,
            state="WAITING_NO_VISION",
            reason="Off-Killzone Session / Low Volatility"
        )
