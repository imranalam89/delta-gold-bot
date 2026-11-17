import pandas as pd
import numpy as np

bars = pd.read_parquet('data/processed/xautusd_delta_oct1_to_now_1m.parquet')
if 'timestamp' in bars.columns:
    bars.set_index('timestamp', inplace=True)
elif 'time' in bars.columns:
    bars.set_index('time', inplace=True)

# Find index of entry
entry_time = pd.to_datetime('2026-11-15 09:16:00+00:00')
entry_idx = bars.index.get_loc(entry_time)

entry = 3829.36
sl_init = 3835.60
rk = 6.24
tp1 = 3818.13
tp2 = 3801.28
stall_trig_r = 0.48
stall_bars = 5

c = bars['close'].to_numpy()
h = bars['high'].to_numpy()
l = bars['low'].to_numpy()
ts = bars.index

cur_sl = sl_init
peak_r = 0.0
peak_k = entry_idx
stage = 0
stall_locked = False

print(f"=== BAR BY BAR REPLAY OF TRADE #108 (Entry index: {entry_idx}) ===")

for k in range(entry_idx + 1, entry_idx + 150):
    cur_mfe_r = (entry - l[k]) / rk
    cur_r = (entry - c[k]) / rk
    if cur_mfe_r > peak_r:
        peak_r = cur_mfe_r
        peak_k = k
        print(f"[{ts[k]}] Peak MFE updated to +{peak_r:.2f}R (Low={l[k]:.2f})")

    # Check SL
    if h[k] >= cur_sl:
        print(f"\n>>> EXIT TRIGGERED AT [{ts[k]}]! High={h[k]:.2f} >= cur_sl={cur_sl:.2f}")
        print(f"    Exit Price: {cur_sl:.2f}, Stage: {stage}, Stall_locked: {stall_locked}")
        break

    # Stall Lock logic
    if stage == 0 and stall_trig_r > 0 and peak_r >= stall_trig_r and (k - peak_k >= stall_bars):
        if c[k] <= entry - 0.28 * rk:
            cur_sl = min(cur_sl, entry - 0.28 * rk)
            stage = 1
            stall_locked = True
            print(f"[{ts[k]}] STALL LOCK ACTIVATED! cur_sl moved to {cur_sl:.2f} (c[k]={c[k]:.2f})")

    if k >= entry_idx + 110:
        break
