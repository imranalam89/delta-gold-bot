import json
import numpy as np
import struct, base64
from datetime import datetime, timezone
from collections import defaultdict

print("[1/4] Loading payload and continuous 1m bars...")
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
opens = np.zeros(n, dtype=np.float32)
highs = np.zeros(n, dtype=np.float32)
lows  = np.zeros(n, dtype=np.float32)
closes= np.zeros(n, dtype=np.float32)

for i in range(n):
    if i > 0:
        cur_min += dt[i]
        cur_open += do[i]
    times[i] = cur_min * 60
    opens[i] = round(cur_open * 0.1, 2)
    highs[i] = round((cur_open + dh[i]) * 0.1, 2)
    lows[i]  = round((cur_open - dl[i]) * 0.1, 2)
    closes[i]= round((cur_open + dc[i]) * 0.1, 2)

print(f"Decoded {n} continuous bars.")

profile_name = 'MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL'
trades = data['profiles'][profile_name]['trades']
print(f"Loaded {profile_name} with {len(trades)} trades.")

# Mark all bars that have an active trade
active_mask = np.zeros(n, dtype=bool)
for t in trades:
    s = max(0, t['entry_idx'])
    e = min(n - 1, t['exit_idx'])
    active_mask[s:e+1] = True

flat_bars = np.sum(~active_mask)
active_bars = np.sum(active_mask)
print(f"Active Market Exposure: {active_bars} bars ({active_bars/n*100:.2f}%)")
print(f"Flat (Untraded) Time:  {flat_bars} bars ({flat_bars/n*100:.2f}%)")

# Find contiguous flat periods (where strategy was NOT in a trade)
flat_periods = []
in_flat = False
flat_start = 0

for i in range(n):
    if not active_mask[i]:
        if not in_flat:
            in_flat = True
            flat_start = i
    else:
        if in_flat:
            in_flat = False
            flat_periods.append((flat_start, i - 1))
if in_flat:
    flat_periods.append((flat_start, n - 1))

print(f"Found {len(flat_periods)} contiguous flat periods.")

# For each flat period of significant length (e.g. >= 30 mins), find the maximum price swing (expansion)
untraded_moves = []

for s, e in flat_periods:
    duration_mins = e - s + 1
    if duration_mins < 15:
        continue
    
    sub_h = highs[s:e+1]
    sub_l = lows[s:e+1]
    sub_c = closes[s:e+1]
    
    max_h = float(np.max(sub_h))
    min_l = float(np.min(sub_l))
    max_idx = s + int(np.argmax(sub_h))
    min_idx = s + int(np.argmin(sub_l))
    
    total_range = max_h - min_l
    
    # Determine dominant direction: Bull run vs Bear plunge
    if max_idx > min_idx: # Plunged then rallied, or rallied from low to high
        move_type = "BULL_EXPANSION"
        move_pts = max_h - min_l
        move_start_idx = min_idx
        move_end_idx = max_idx
    else:
        move_type = "BEAR_EXPANSION"
        move_pts = max_h - min_l
        move_start_idx = max_idx
        move_end_idx = min_idx
        
    start_ts = int(times[move_start_idx])
    end_ts = int(times[move_end_idx])
    
    dt_start = datetime.fromtimestamp(start_ts, tz=timezone.utc)
    dt_end = datetime.fromtimestamp(end_ts, tz=timezone.utc)
    
    untraded_moves.append({
        'flat_start_idx': s,
        'flat_end_idx': e,
        'duration_mins': duration_mins,
        'move_type': move_type,
        'move_pts': round(move_pts, 2),
        'start_px': round(float(opens[move_start_idx]), 2),
        'end_px': round(float(closes[move_end_idx]), 2),
        'low_px': round(min_l, 2),
        'high_px': round(max_h, 2),
        'start_time': dt_start.strftime('%Y-%m-%d %H:%M UTC'),
        'end_time': dt_end.strftime('%Y-%m-%d %H:%M UTC'),
        'day': dt_start.strftime('%A'),
        'hour_utc': dt_start.hour,
        'date_str': dt_start.strftime('%Y-%m-%d')
    })

# Sort untraded moves by points size
untraded_moves.sort(key=lambda x: -x['move_pts'])

print("\n" + "="*85)
print("TOP 20 LARGEST UNTRADED MARKET EXPANSIONS (WHERE MUX WAS FLAT)")
print("="*85)

for i, m in enumerate(untraded_moves[:20], 1):
    est_hour = (m['hour_utc'] - 5) % 24
    session = "LONDON" if 7 <= m['hour_utc'] < 13 else ("NEW_YORK" if 13 <= m['hour_utc'] < 20 else "ASIA")
    print(f"#{i:2} | {m['date_str']} ({m['day'][:3]}) {m['move_type']:14} | Range: {m['move_pts']:6.2f} pts | Px: {m['start_px']} -> {m['end_px']} | Dur: {m['duration_mins']:4}m | {session} ({m['start_time'][11:16]} - {m['end_time'][11:16]})")

# Statistical distribution of untraded moves >= 30 pts
large_moves = [m for m in untraded_moves if m['move_pts'] >= 30.0]
print(f"\nTotal untraded mega-expansions >= 30 points: {len(large_moves)}")

session_dist = defaultdict(int)
day_dist = defaultdict(int)
type_dist = defaultdict(int)

for m in large_moves:
    sess = "LONDON" if 7 <= m['hour_utc'] < 13 else ("NEW_YORK" if 13 <= m['hour_utc'] < 20 else "ASIA")
    session_dist[sess] += 1
    day_dist[m['day']] += 1
    type_dist[m['move_type']] += 1

print("\nDistribution of Large Missed Moves (>= 30 pts):")
print(f"  Sessions: {dict(session_dist)}")
print(f"  Directions: {dict(type_dist)}")
print(f"  Days: {dict(day_dist)}")
