"""
Syndicate Alpha — Live 3-State Consensus Historical Replay Engine
-----------------------------------------------------------------
Replays institutional Gold Futures bars through the 16-agent floor:
1. Each agent outputs an AgentPacket (INSTANT_ACTION, PENDING_SETUP, BIAS_LEAN, WAITING_NO_VISION, HARD_VETO)
2. VictorBlackboardConsensus resolves floor consensus with 2.5x initiator boost, 0.5x pending lean, and veto shield
3. Approved EXECUTE_BUY / EXECUTE_SELL decisions pass directly to:
   - ethan_math.py (for $5.00 fee-adjusted sizing)
   - ryan_exec.py (for dynamic in-trade execution & 5-phase lifecycle)
4. Emits real-time state to blackboard/live_state.json
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from trading_desk.command.victor_boss import AgentPacket, VictorBlackboardConsensus
from trading_desk.agents.kai_smc import KaiFibSMC
from trading_desk.agents.arthur_vet import ArthurRegimeVet
from trading_desk.agents.leo_sweep import LeoKillzoneSweep
from trading_desk.agents.nina_range import NinaSMCHunter
from trading_desk.agents.max_trend import MaxTrapSpecialist
from trading_desk.agents.sam_l2 import SamOrderBookDOM
from trading_desk.agents.jack_vsa import JackVSASpecialist
from trading_desk.agents.ben_news import BenNewsSentinel
from trading_desk.agents.elena_price_action import ElenaPriceAction
from trading_desk.agents.omar_flow import OmarOrderFlow
from trading_desk.agents.marcus_breakout import MarcusBreakoutSpecialist
from trading_desk.agents.sarah_psych import SarahPsychologist
from trading_desk.agents.david_veteran import DavidVeteranTrader
from trading_desk.execution.ethan_math import EthanRiskMath
from trading_desk.execution.ryan_exec import RyanExecutionLifecycle
from src.agents.syndicate_agents import precompute_features
from backtest_runner import load_config, CONFIG_PATH, load_dataset


def run_replay(days_window: int = 155):
    cfg = load_config(CONFIG_PATH)
    raw_df = load_dataset()
    if days_window > 0:
        cutoff = raw_df.index[-1] - pd.Timedelta(days=days_window)
        raw_df = raw_df[raw_df.index >= cutoff].copy()

    print(f"\n[REPLAY ENGINE] Precomputing features across {len(raw_df):,} bars ({raw_df.index[0]} -> {raw_df.index[-1]})...")
    df = precompute_features(raw_df, cfg)

    # Load Dynamic Historical Edge Matrix
    edge_matrix_path = os.path.join(BASE_DIR, "trading_desk", "agent_edge_matrix.json")
    edge_matrix = {}
    if os.path.exists(edge_matrix_path):
        with open(edge_matrix_path, "r", encoding="utf-8") as f:
            edge_matrix = json.load(f)

    # Initialize all 13 active floor setup & filter specialists
    agents = {
        "1:BEN": BenNewsSentinel("1:BEN"),
        "2:ARTHUR": ArthurRegimeVet("2:ARTHUR"),
        "3:MARCUS": MarcusBreakoutSpecialist("3:MARCUS"),
        "4:NINA": NinaSMCHunter("4:NINA"),
        "5:MAX": MaxTrapSpecialist("5:MAX"),
        "6:LEO": LeoKillzoneSweep("6:LEO"),
        "7:KAI": KaiFibSMC("7:KAI"),
        "8:ELENA": ElenaPriceAction("8:ELENA"),
        "9:SAM": SamOrderBookDOM("9:SAM"),
        "10:OMAR": OmarOrderFlow("10:OMAR"),
        "11:JACK": JackVSASpecialist("11:JACK"),
        "12:SARAH": SarahPsychologist("12:SARAH"),
        "13:DAVID": DavidVeteranTrader("13:DAVID"),
    }

    # Floor Command and Execution
    bb_path = os.path.join(BASE_DIR, "blackboard", "live_state.json")
    victor = VictorBlackboardConsensus(initiator_boost=2.5, pending_lean_mult=0.5, blackboard_path=bb_path)
    ethan = EthanRiskMath(fixed_risk_usd=5.0, fee_rate=0.0001)
    ryan = RyanExecutionLifecycle(be_trigger_r=0.95, be_lock_r=0.25, trail_trigger_r=1.95, max_hold_mins=240)

    timestamps = df.index.to_pydatetime()
    closes = df["close"].to_numpy()
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    opens = df["open"].to_numpy()
    atrs = df["atr_5m"].to_numpy()

    # Pre-extract numpy dicts for fast looping
    df_dict = df.to_dict(orient="records")

    equity = 100.0
    start_equity = 100.0
    daily_loss_r = 0.0
    current_day = None
    trades_log = []
    daily_trades = 0

    print(f"[REPLAY ENGINE] Starting Live 3-State Consensus Simulation on ${start_equity:.2f} Account ($5.00 Risk)...")

    # Keep a rolling 5m close cache
    last_5m_close = closes[0]

    for i in range(100, len(df)):
        ts = timestamps[i]
        day_key = ts.date()
        if day_key != current_day:
            current_day = day_key
            daily_loss_r = 0.0
            daily_trades = 0

        bar = df_dict[i]
        bar["timestamp"] = ts
        bar["daily_loss_r"] = daily_loss_r

        if i % 5 == 0:
            last_5m_close = closes[i]

        bar_1m = {"close": closes[i], "open": opens[i], "high": highs[i], "low": lows[i], "timestamp": ts}
        bar_5m = {"close": last_5m_close}

        # 1. Update In-Trade Lifecycle if an order is active
        if ryan.is_in_trade():
            exit_log = ryan.update_lifecycle(bar, i)
            if exit_log is not None:
                net_pnl = exit_log["net_pnl_usd"]
                equity += net_pnl
                r_mult = exit_log["r_multiple"]
                if r_mult < 0:
                    daily_loss_r += r_mult
                exit_log["equity_after"] = round(equity, 2)
                trades_log.append(exit_log)
            continue

        # Determine current session and regime for edge weights lookup
        est_hr = (ts.hour - 5) % 24
        sess = "ASIA" if est_hr in (18, 19, 20, 21, 22, 23, 0, 1) else ("LONDON" if est_hr in (2, 3, 4, 5, 6, 7) else "NEW_YORK")
        reg = "TRENDING" if (bar.get("chop_index", 50.0) < 52.5 and bar.get("adx", 20.0) >= 20.0) else "SIDEWAYS"
        curr_edge_weights = edge_matrix.get(sess, {}).get(reg, {})

        # 2. Collect AgentPackets from all floor specialists
        packets = {}
        for ag_name, ag_inst in agents.items():
            packets[ag_name] = ag_inst.evaluate(bar)

        # 3. VictorBoss Consensus & Veto Resolution
        decision = victor.update_and_evaluate(packets, bar_1m, bar_5m, curr_edge_weights)

        # 4. If approved trade, pass to Ethan for sizing & Ryan for execution
        if decision["decision"] in ("EXECUTE_BUY", "EXECUTE_SELL"):
            direction = decision["side"]
            sized_order = ethan.size_trade(
                entry_price=closes[i],
                stop_loss=decision.get("stop_loss"),
                tp1=decision.get("tp1"),
                tp2=decision.get("tp2"),
                direction=direction,
                atr=atrs[i]
            )
            ryan.open_trade(decision, sized_order, i, ts)
            daily_trades += 1

    trades_df = pd.DataFrame(trades_log)
    out_csv = os.path.join(BASE_DIR, "data", "processed", "replay_trades.csv")
    trades_df.to_csv(out_csv, index=False)

    # Performance Reporting
    n = len(trades_df)
    if n > 0:
        wins = trades_df[trades_df["net_pnl_usd"] > 0]
        losses = trades_df[trades_df["net_pnl_usd"] < 0]
        wr = len(wins) / n * 100.0
        gross_pnl = trades_df["gross_pnl_usd"].sum()
        fees = trades_df["delta_fee_usd"].sum()
        net_pnl = trades_df["net_pnl_usd"].sum()
        gw = wins["gross_pnl_usd"].sum()
        gl = abs(losses["gross_pnl_usd"].sum())
        pf = round(gw / max(gl, 0.01), 2)
        avg_r = trades_df["r_multiple"].mean()

        cum_equity = start_equity + trades_df["net_pnl_usd"].cumsum()
        peak = cum_equity.cummax()
        dd = (cum_equity - peak) / peak * 100.0
        max_dd = dd.min()

        print("\n" + "=" * 110)
        print("   SYNDICATE ALPHA — LIVE 3-STATE CONSENSUS & VETO REPLAY RESULTS")
        print("=" * 110)
        print(f"Total Trades   : {n} trades across {days_window} days (avg {n/max(1, len(set(trades_df['entry_time'].str[:10]))):.2f}/active day)")
        print(f"Win Rate       : {wr:.2f}% ({len(wins)}W / {len(losses)}L)")
        print(f"Profit Factor  : {pf}")
        print(f"Avg R-Multiple : {avg_r:+.2f}R")
        print(f"Gross PnL      : ${gross_pnl:+.2f}")
        print(f"Delta 0.01% Fee: -${fees:.2f}")
        print(f"Net PnL        : ${net_pnl:+.2f}")
        print(f"Ending Equity  : ${equity:.2f} (Start: ${start_equity:.2f})")
        print(f"Max Drawdown   : {max_dd:.2f}%")
        print("=" * 110)

        print("\nBreakdown by Initiating Specialist:")
        for ag, group in trades_df.groupby(trades_df["initiators"].apply(lambda x: x[0] if len(x)>0 else "UNKNOWN")):
            g_wins = group[group["net_pnl_usd"] > 0]
            g_wr = len(g_wins) / len(group) * 100.0
            g_pnl = group["net_pnl_usd"].sum()
            print(f"  * {ag:12} | Trades: {len(group):3} | Win Rate: {g_wr:5.1f}% | Net PnL: ${g_pnl:+6.2f}")

        print("\nBreakdown by Exit Reason:")
        for rsn, group in trades_df.groupby("exit_reason"):
            print(f"  * {rsn:36} | Trades: {len(group):3} | Avg R: {group['r_multiple'].mean():+5.2f}R | Net PnL: ${group['net_pnl_usd'].sum():+6.2f}")
        print("=" * 110)
    else:
        print("\n[REPLAY ENGINE] Zero trades triggered under current consensus constraints.")

    return trades_df


if __name__ == "__main__":
    run_replay(days_window=155)
