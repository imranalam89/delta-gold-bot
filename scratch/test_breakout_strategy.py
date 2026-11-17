import json
import numpy as np
import struct, base64
import pandas as pd
from datetime import datetime, timezone

print("[1/3] Loading parquet dataset & continuous 1m bars...")
with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

c = data['continuous_1m']
n = c['n']
dt = struct.unpack(f'<{n}H', base64.b64decode(c['dt']))
do = struct.unpack(f'<{n}h', base64.b64decode(c['do']))
dh = struct.unpack(f'<{n}H', base64.b64decode(c['dh']))
dl = struct.unpack(f'<{n}H', base64.b64decode(c['dl']))
dc = struct.unpack(f'<{n}h', base64.b64decode(c['dc']))

cur_min = c['start_ts_min']
cur_open = c['start_open_d']
times = np.zeros(n, dtype=np.int64)
highs = np.zeros(n, dtype=np.float32)
lows  = np.zeros(n, dtype=np.float32)
closes= np.zeros(n, dtype=np.float32)

for i in range(n):
    if i > 0:
        cur_min += dt[i]
        cur_open += do[i]
    times[i] = cur_min * 60
    highs[i] = round((cur_open + dh[i]) * 0.1, 2)
    lows[i]  = round((cur_open - dl[i]) * 0.1, 2)
    closes[i]= round((cur_open + dc[i]) * 0.1, 2)

mux_trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']

# Mark active MUX bars
mux_mask = np.zeros(n, dtype=bool)
for t in mux_trades:
    s = max(0, t['entry_idx'])
    e = min(n - 1, t['exit_idx'])
    mux_mask[s:e+1] = True

# Aggregate into 15m bars to compute Donchian Channels & ATR
# 15m = 15 bars of 1m
n_15 = n // 15
h_15 = np.zeros(n_15, dtype=np.float32)
l_15 = np.zeros(n_15, dtype=np.float32)
c_15 = np.zeros(n_15, dtype=np.float32)

for j in range(n_15):
    s_idx = j * 15
    e_idx = s_idx + 15
    h_15[j] = np.max(highs[s_idx:e_idx])
    l_15[j] = np.min(lows[s_idx:e_idx])
    c_15[j] = closes[e_idx - 1]

# 20-period 15m Donchian Channel
# 20 periods of 15m = 5 hours
donch_h = np.zeros(n_15, dtype=np.float32)
donch_l = np.zeros(n_15, dtype=np.float32)
atr_15  = np.zeros(n_15, dtype=np.float32)

for j in range(20, n_15):
    donch_h[j] = np.max(h_15[j-20:j])
    donch_l[j] = np.min(l_15[j-20:j])
    # Approximate ATR
    tr = np.maximum(h_15[j-14:j] - l_15[j-14:j], 1.0)
    atr_15[j] = np.mean(tr)

print(f"Computed 15m indicators across {n_15} bars.")

# Check how many breakout signals occur while MUX is FLAT
breakout_signals = []
for j in range(25, n_15):
    idx_1m = j * 15
    # If MUX is flat at this bar:
    if not mux_mask[idx_1m]:
        atr = atr_15[j]
        if atr < 2.0: continue
        
        # Bullish Breakout
        if c_15[j] > donch_h[j] and c_15[j-1] <= donch_h[j-1]:
            breakout_signals.append({
                'idx_1m': idx_1m,
                'j_15': j,
                'direction': 'LONG',
                'entry_px': c_15[j],
                'sl_dist': round(max(5.0, min(12.0, 1.35 * atr)), 2),
                'ts': times[idx_1m],
                'time_str': datetime.fromtimestamp(times[idx_1m], tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
            })
        # Bearish Breakdown
        elif c_15[j] < donch_l[j] and c_15[j-1] >= donch_l[j-1]:
            breakout_signals.append({
                'idx_1m': idx_1m,
                'j_15': j,
                'direction': 'SHORT',
                'entry_px': c_15[j],
                'sl_dist': round(max(5.0, min(12.0, 1.35 * atr)), 2),
                'ts': times[idx_1m],
                'time_str': datetime.fromtimestamp(times[idx_1m], tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
            })

print(f"Found {len(breakout_signals)} non-overlapping Breakout signals during MUX flat time.")
print("Sample breakout signals:")
for s in breakout_signals[:8]:
    print(f"  {s['time_str']} UTC | {s['direction']} @ {s['entry_px']} (SL: {s['sl_dist']} pts)")
