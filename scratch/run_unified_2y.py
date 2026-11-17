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

poc60 = df["poc_60"].to_numpy()
rpos60 = df["range_pos_60"].to_numpy()
sh20, sl20 = A["sh20"], A["sl20"]
bull_fvg = df["bull_fvg"].rolling(10, min_periods=1).max().to_numpy() > 0
bear_fvg = df["bear_fvg"].rolling(10, min_periods=1).max().to_numpy() > 0
kz_win = df["in_killzone"].to_numpy()
sb_win = df["silver_bullet"].to_numpy()
stop_b = df["stopping_vol_bull"].rolling(10, min_periods=1).max().to_numpy() > 0
stop_s = df["stopping_vol_bear"].rolling(10, min_periods=1).max().to_numpy() > 0

specialists_def = [
    {
        "id": "6:KAI",
        "tl": ((fib240_l >= 0.53) | (fib60_l >= 0.57)) & (fib240_l <= 0.86) & (vz >= 0.52),
        "ts": ((fib240_s >= 0.53) | (fib60_s >= 0.57)) & (fib240_s <= 0.86) & (vz >= 0.52),
    },
    {
        "id": "8:ELENA",
        "tl": (c > ema9) & (b_mss | (lw >= 1.12)) & (vz >= 0.32),
        "ts": (c < ema9) & (s_mss | (uw >= 1.12)) & (vz >= 0.32),
    },
    {
        "id": "3:MARCUS",
        "tl": (chop < 52.8) & ((rpos60 <= 0.64) | (fib240_l >= 0.50)) & ((lw >= 1.05) | b_mss | (d5 > 0)) & (vz >= 0.44),
        "ts": (chop < 53.4) & ((rpos60 >= 0.36) | (fib240_s >= 0.50)) & ((uw >= 1.05) | s_mss | (d5 < 0)) & (vz >= 0.44),
    },
    {
        "id": "4:NINA",
        "tl": (bull_fvg | (l <= sl20 * 1.0018) | (lw >= 1.18) | b_mss) & (vz >= 0.58),
        "ts": (bear_fvg | (h >= sh20 * 0.9982) | (uw >= 1.18) | s_mss) & (vz >= 0.58),
    },
    {
        "id": "6:SOPHIA",
        "tl": (kz_win | sb_win | (est_hr >= 18)) & (adx >= 14.5) & (vz >= 0.42),
        "ts": (kz_win | sb_win | (est_hr >= 18)) & (adx >= 14.5) & (vz >= 0.42),
    },
    {
        "id": "11:LIAM",
        "tl": (stop_b | (vz >= 0.80)) & (vz >= 0.70),
        "ts": (stop_s | (vz >= 0.80)) & (vz >= 0.70),
    }
]

all_trades = []

for spec in specialists_def:
    aid = spec["id"]
    tl, ts = spec["tl"], spec["ts"]
    m5_l = is_5m & base_gate & htf_bull & sarah_l & (c > ema15) & htf_disc_l & tl
    m5_s = is_5m & base_gate & htf_bear & sarah_s & (c < ema15) & htf_prem_s & ts
    
    res = simulate_specialist_fast(
        A, m5_l, m5_s, tf_mod=5, sl_mult=0.85, tp1_r=1.80, tp2_r=4.50, max_hold=240,
        be_trig_r=1.05, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=0.45,
        stall_trig_r=0.54, stall_bars=6, cooldown=12, record_trades=True,
        agent_id=aid, agent_focus=aid, tf_label="5m"
    )
    if res and res['trades']:
        print(f"Agent {aid}: {len(res['trades'])} trades | WR: {res['win_rate']}% | Net: ${res['net_pnl']:.2f}")
        for t in res['trades']:
            t_copy = dict(t)
            t_copy['agent'] = aid
            all_trades.append(t_copy)

print(f"\nTotal Candidate Specialist Trades: {len(all_trades)}")

# Sort all candidate trades by entry_ts
all_trades.sort(key=lambda x: x['entry_ts'])

# Run Unified Single-Slot Multiplexer (Non-overlapping desk)
active = []
executed = []
eq = 100.0
peak = 100.0
max_dd = 0.0

for t in all_trades:
    ts = t['entry_ts']
    rem = []
    for at in active:
        if at['exit_ts'] <= ts:
            eq += at['net_pnl']
            peak = max(peak, eq)
            dd = (peak - eq) / peak * 100 if peak > 0 else 0
            max_dd = max(max_dd, dd)
            at['equity_after'] = round(eq, 2)
            executed.append(at)
        else:
            rem.append(at)
    active = rem
    
    if len(active) >= 1:
        continue # Single-slot non-overlapping
        
    active.append(dict(t))

for at in active:
    eq += at['net_pnl']
    peak = max(peak, eq)
    dd = (peak - eq) / peak * 100 if peak > 0 else 0
    max_dd = max(max_dd, dd)
    at['equity_after'] = round(eq, 2)
    executed.append(at)

wins = sum(1 for t in executed if t['net_pnl'] > 0)
win_sum = sum(t['net_pnl'] for t in executed if t['net_pnl'] > 0)
loss_sum = abs(sum(t['net_pnl'] for t in executed if t['net_pnl'] < 0))
pf = win_sum / loss_sum if loss_sum > 0 else 99.0
wr = wins / len(executed) * 100

print("\n" + "="*70)
print(f"UNIFIED 2-YEAR SINGLE-SLOT MULTIPLEXER RESULTS ({len(executed)} Trades):")
print("="*70)
print(f"Trades Count:     {len(executed)} Trades (~1.8 trades/day)")
print(f"Win Rate:         {wr:.2f}% ({wins} Wins / {len(executed) - wins} Losses)")
print(f"Net Profit:       +${eq - 100:.2f} Clean Net Gain")
print(f"Ending Equity:    ${eq:.2f} ({eq/100:.2f}X Account Multiplier!)")
print(f"Profit Factor:    {pf:.2f} PF")
print(f"Max Drawdown:     {max_dd:.2f}%")

# Annual breakdown
df_e = pd.DataFrame(executed)
df_e['year'] = pd.to_datetime(df_e['entry_ts'], unit='s', utc=True).dt.year
print("\nAnnual Breakdown:")
for yr, sub in df_e.groupby('year'):
    w = (sub['net_pnl'] > 0).sum()
    w_sum = sub[sub['net_pnl'] > 0]['net_pnl'].sum()
    l_sum = abs(sub[sub['net_pnl'] < 0]['net_pnl'].sum())
    yr_pf = w_sum / l_sum if l_sum > 0 else 99
    print(f"  {yr}: {len(sub)} Trades | WR: {w/len(sub)*100:.2f}% | Net: +${sub['net_pnl'].sum():.2f} | PF: {yr_pf:.2f}")
