import json
import os
import sys
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
df = pd.read_parquet(os.path.join(BASE_DIR, 'data', 'processed', 'GC_v0_2Year_L2_OrderFlow_Master.parquet')).tz_convert('UTC')
start_dt = pd.to_datetime('2026-05-28 22:00:00', utc=True)
df_5m = df.loc[start_dt:].copy()

times = df_5m.index.to_numpy()
closes = df_5m['close'].to_numpy(dtype=np.float64)
highs = df_5m['high'].to_numpy(dtype=np.float64)
lows = df_5m['low'].to_numpy(dtype=np.float64)
opens = df_5m['open'].to_numpy(dtype=np.float64)
est_hours = ((df_5m.index.hour - 5) % 24).to_numpy(dtype=np.int32)
n_bars = len(closes)
time_to_idx = {ts: idx for idx, ts in enumerate(times)}

with open(os.path.join(BASE_DIR, 'data', 'processed', 'all_11_agents_lab_bundle.json'), 'r', encoding='utf-8') as f:
    bundle = json.load(f)

# Test 1: Structural Pivot Stops on 5m+15m+1h
# Test 2: Structural Pivot Stops on 15m+1h only
from scripts.run_100pct_verified_grid import simulate_bar_by_bar_fast, SNIPER_TRIO, ELITE_8

print("=== REVERSE-ENGINEERED STRUCTURAL DISCOVERIES ===")
res1 = simulate_bar_by_bar_fast(allowed_agents=SNIPER_TRIO, allowed_tfs=('5m', '15m', '1h'), max_slots=2, sl_mult=1.0)
print(f"Sniper Trio (5m+15m+1h):  Trades: {res1['trades']:<4} | WR: {res1['wr']:.2f}% | PF: {res1['pf']:.2f} | Net: ${res1['net_pnl']:.2f} | Max DD: -{res1['max_dd']:.2f}%")

res2 = simulate_bar_by_bar_fast(allowed_agents=ELITE_8, allowed_tfs=('5m', '15m', '1h'), max_slots=2, sl_mult=1.0)
print(f"Elite 8 (5m+15m+1h):      Trades: {res2['trades']:<4} | WR: {res2['wr']:.2f}% | PF: {res2['pf']:.2f} | Net: ${res2['net_pnl']:.2f} | Max DD: -{res2['max_dd']:.2f}%")

res3 = simulate_bar_by_bar_fast(allowed_agents=SNIPER_TRIO, allowed_tfs=('15m', '1h'), max_slots=2, sl_mult=1.0)
print(f"Sniper Trio (15m+1h):     Trades: {res3['trades']:<4} | WR: {res3['wr']:.2f}% | PF: {res3['pf']:.2f} | Net: ${res3['net_pnl']:.2f} | Max DD: -{res3['max_dd']:.2f}%")
