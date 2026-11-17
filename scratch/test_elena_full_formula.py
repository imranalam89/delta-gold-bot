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
df_raw = pd.read_parquet(parquet_path)
if not df_raw.index.tz:
    df_raw.index = df_raw.index.tz_localize('UTC')
else:
    df_raw.index = df_raw.index.tz_convert('UTC')

cfg = load_config(CONFIG_PATH)
df = precompute_features(df_raw, cfg)
A = compute_maya_indicators(df)

c, h, l, o = A["c"], A["h"], A["l"], A["o"]
ema9, ema15, ema50, ema200, emad, emam = A["ema9"], A["ema15"], A["ema50"], A["ema200"], A["emad"], A["emam"]
rsi5, vz, lw, uw, b_mss, s_mss = A["rsi5"], A["vz"], A["lw"], A["uw"], A["b_mss"], A["s_mss"]
fib240_l, fib240_s, chop, adx, atr, d5 = A["fib240_l"], A["fib240_s"], A["chop"], A["adx"], A["atr"], A["d5"]
fib60_l = df["fib_retracement_long"].to_numpy()
fib60_s = df["fib_retracement_short"].to_numpy()
in_session, news_lock, spread = A["in_session"], A["news_lock"], A["spread"]
room_h60, room_l60 = A["room_h60"], A["room_l60"]
room_h240, room_l240 = A["room_h240"], A["room_l240"]
sess_arr = A["sess"]
is_london = sess_arr == "LONDON"
est_hr = (df.index.hour - 5) % 24
mins = df.index.minute.to_numpy()
hrs_utc = df.index.hour.to_numpy()

prime_hrs = np.isin(est_hr, [2, 3, 4, 5, 8, 10, 11, 12, 18, 20, 21])
# Model 2 News Whipsaw Shield: hrs_utc != 13
base_gate = (~news_lock) & prime_hrs & (spread <= 0.65) & (hrs_utc != 13)

rk_base = np.clip(1.25 * atr, 3.8, 11.0)
rm_l = (room_h240 >= 1.10 * rk_base) | (room_h60 >= 1.00 * rk_base)
rm_s = (room_l240 >= 1.10 * rk_base) | (room_l60 >= 1.00 * rk_base)

htf_bull = ((c > emam) & (ema200 > emad)) | ((c > emad) & (ema50 > ema200) & (chop < 52.5)) | ((c > ema200) & (ema15 > ema50) & (chop < 50.0) & (d5 > 0))
htf_bear = ((c < emam) & (ema50 < ema200)) | ((c < emad) & (ema50 < ema200) & (chop < 53.5)) | ((c < ema200) & (ema15 < ema50) & (chop < 51.0) & (d5 < 0))

sarah_l = (~is_london) & (chop < 53.5) & (rsi5 >= 35) & (rsi5 <= 66) & rm_l
sarah_s = (rsi5 <= 66) & (rsi5 >= 32) & rm_s

htf_disc_l = (fib240_l >= 0.57) | (fib60_l >= 0.61)
htf_prem_s = (fib240_s >= 0.57) | (fib60_s >= 0.61)

is_5m = (mins % 5) == 0

# Test Elena on 5m with full institutional formula:
tl = (c > ema9) & (b_mss | (lw >= 1.12)) & (vz >= 0.32)
ts = (c < ema9) & (s_mss | (uw >= 1.12)) & (vz >= 0.32)

m5_l = is_5m & base_gate & htf_bull & sarah_l & (c > ema15) & htf_disc_l & tl
m5_s = is_5m & base_gate & htf_bear & sarah_s & (c < ema15) & htf_prem_s & ts

# Test with Model 2 parameters: 0.85x SL, 40R Chandelier Trail, Smart Stall Lock
res = simulate_specialist_fast(
    A, m5_l, m5_s, tf_mod=5, sl_mult=0.85, tp1_r=1.80, tp2_r=4.50, max_hold=240,
    be_trig_r=1.05, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=0.45,
    stall_trig_r=0.54, stall_bars=6, cooldown=12, record_trades=True,
    agent_id="8:ELENA", agent_focus="Institutional VSA Scalper", tf_label="5m"
)

print("8:ELENA (5m Full Institutional Setup) across 2 FULL YEARS:")
print(f"  Trades: {res['trades_count']}")
print(f"  Win Rate: {res['win_rate']}% ({res['wins']} / {res['trades_count']})")
print(f"  Net PnL: ${res['net_pnl']:.2f}")
print(f"  Profit Factor: {res['profit_factor']} PF")
print(f"  Max Drawdown: {res['max_dd_pct']}%")
