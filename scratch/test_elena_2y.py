"""
Syndicate Alpha — 2-Year Specialist Signal Generator
Runs all 11 Field Specialists across 699,702 1m bars for 2 full years (Nov 2024 - Oct 2026).
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backtest_runner import load_config, CONFIG_PATH
from src.agents.syndicate_agents import precompute_features
from scripts.backtest_agent_2_maya_lab import compute_maya_indicators
from scripts.backtest_all_11_agents_lab import simulate_specialist_fast

parquet_path = os.path.join(BASE_DIR, "data", "processed", "GC_v0_2Year_L2_OrderFlow_Master.parquet")
print(f"Loading full 2-year parquet: {parquet_path}...")
df_raw = pd.read_parquet(parquet_path)
if not df_raw.index.tz:
    df_raw.index = df_raw.index.tz_localize('UTC')
else:
    df_raw.index = df_raw.index.tz_convert('UTC')

cfg = load_config(CONFIG_PATH)
print(f"Precomputing features across {len(df_raw):,} bars...")
t0 = time.time()
df = precompute_features(df_raw, cfg)
A = compute_maya_indicators(df)
print(f"Features ready in {time.time() - t0:.2f}s.")

# Let's inspect specialist execution for 1 specialist (e.g. 8:ELENA on 5m)
c = A["c"]
b_mss = A["b_mss"]
s_mss = A["s_mss"]
lw = A["lw"]
uw = A["uw"]
vz = A["vz"]
ema9 = A["ema9"]
news_lock = A["news_lock"]
in_session = A["in_session"]
spread = A["spread"]
hrs = df.index.hour.to_numpy()

gate = (~news_lock) & in_session & (spread <= 0.65) & (hrs != 13)

elena_l = gate & (c > ema9) & (b_mss | (lw >= 1.12)) & (vz >= 0.32)
elena_s = gate & (c < ema9) & (s_mss | (uw >= 1.12)) & (vz >= 0.32)

res = simulate_specialist_fast(
    A=A,
    m_l=elena_l,
    m_s=elena_s,
    tf_mod=5,
    sl_mult=0.85,
    tp1_r=1.80,
    tp2_r=4.50,
    max_hold=240,
    be_trig_r=1.05,
    be_lock_r=0.38,
    trail_trig_r=2.10,
    trail_dist_r=0.45,
    stall_trig_r=0.54,
    stall_bars=6,
    cooldown=12,
    record_trades=True,
    agent_id="8:ELENA",
    agent_focus="1m/5m Fast Scalper",
    tf_label="5m"
)

print("\n8:ELENA (5m) 2-Year Results:")
print(f"  Trades: {res['trades_count']}")
print(f"  Win Rate: {res['win_rate']}% ({res['wins']} / {res['trades_count']})")
print(f"  Net PnL: ${res['net_pnl']:.2f}")
print(f"  Profit Factor: {res['profit_factor']} PF")
print(f"  Max Drawdown: {res['max_dd_pct']}%")
