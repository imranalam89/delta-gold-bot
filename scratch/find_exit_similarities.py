import json
import numpy as np
import struct, base64
from collections import defaultdict

with open('data/processed/dashboard_payload.json', 'r') as f:
    data = json.load(f)

p = data['profiles']['MUX_085SL_40R_CONTINUOUS_TRAIL']
trades = p['trades']

c = data['continuous_1m']
n = c['n']
dt = struct.unpack(f'<{n}H', base64.b64decode(c['dt']))
do = struct.unpack(f'<{n}h', base64.b64decode(c['do']))
dh = struct.unpack(f'<{n}H', base64.b64decode(c['dh']))
dl = struct.unpack(f'<{n}H', base64.b64decode(c['dl']))
dc = struct.unpack(f'<{n}h', base64.b64decode(c['dc']))

cur_min = c['start_ts_min']
cur_open = c['start_open_d']
highs = np.zeros(n, dtype=np.float32)
lows  = np.zeros(n, dtype=np.float32)
closes= np.zeros(n, dtype=np.float32)

for i in range(n):
    if i > 0:
        cur_min += dt[i]
        cur_open += do[i]
    highs[i] = round((cur_open + dh[i]) * 0.1, 2)
    lows[i]  = round((cur_open - dl[i]) * 0.1, 2)
    closes[i]= round((cur_open + dc[i]) * 0.1, 2)

trail_trades = [t for t in trades if any(k in t['exit_reason'] for k in ['40R', 'TRAIL', 'RUNNER'])]

results = []
for t in trail_trades:
    exit_idx = t['exit_idx']
    direction = t['direction']
    exit_px = t['exit_price']
    sl_dist = t['init_risk_pts']
    end_120 = min(n, exit_idx + 120)
    
    if direction == 'LONG':
        sub_h = highs[exit_idx:end_120]
        favorable_120 = np.max(sub_h) - exit_px if len(sub_h) > 0 else 0.0
    else:
        sub_l = lows[exit_idx:end_120]
        favorable_120 = exit_px - np.min(sub_l) if len(sub_l) > 0 else 0.0
    
    cont_r = float(favorable_120 / sl_dist)
    t_copy = dict(t)
    t_copy['cont_r'] = cont_r
    t_copy['cont_pts'] = favorable_120
    results.append(t_copy)

big_cont = [t for t in results if t['cont_r'] >= 1.5]
clean_exit = [t for t in results if t['cont_r'] < 0.5]
med_cont = [t for t in results if 0.5 <= t['cont_r'] < 1.5]

print(f"Total Trailing Exits: {len(results)}")
print(f"1. Big Continuation (Premature Shakeout >= 1.5R left on table): {len(big_cont)} trades")
print(f"2. Moderate Continuation (0.5R to 1.5R): {len(med_cont)} trades")
print(f"3. Clean Peak Exits (< 0.5R left on table): {len(clean_exit)} trades")

def analyze_group(name, grp):
    print(f"\n" + "="*70)
    print(f"METRICS FOR: {name} ({len(grp)} trades)")
    print("="*70)
    print(f"Average Captured R:        {np.mean([t['r_multiple'] for t in grp]):+5.2f}R")
    print(f"Average Missed Continuation:{np.mean([t['cont_r'] for t in grp]):+5.2f}R ({np.mean([t['cont_pts'] for t in grp]):.1f} pts)")
    print(f"Average 15m ATR:           {np.mean([t.get('atr_15m', 0) for t in grp]):5.2f} pts")
    print(f"Average 15m ADX (Trend):   {np.mean([t.get('adx_15m', 0) for t in grp]):5.2f}")
    print(f"Average Volatility Z-Score:{np.mean([t.get('vol_z', 0) for t in grp]):+5.2f} sigma")
    print(f"Average 15m Chop Index:    {np.mean([t.get('chop_15m', 0) for t in grp]):5.2f}")
    print(f"Average Multi-Agent Confluence:{np.mean([t.get('confirming_count', 0) for t in grp]):.1f} / 16 specialists")
    print(f"Average Consensus Score:   {np.mean([t.get('consensus_score', 0) for t in grp]):5.2f}")
    print(f"Average Hold Duration:     {np.mean([t.get('hold_mins', 0) for t in grp]):5.1f} mins")
    print(f"Average Risk Distance:     {np.mean([t.get('init_risk_pts', 0) for t in grp]):5.2f} pts")

    # Direction breakdown
    longs = sum(1 for t in grp if t['direction'] == 'LONG')
    shorts = sum(1 for t in grp if t['direction'] == 'SHORT')
    print(f"Direction Split:           LONG: {longs} ({longs/len(grp)*100:.1f}%) | SHORT: {shorts} ({shorts/len(grp)*100:.1f}%)")

    # Sessions
    sessions = defaultdict(int)
    for t in grp: sessions[t.get('session', 'UNK')] += 1
    print(f"Session Distribution:      {dict(sessions)}")

    # Timeframe
    tfs = defaultdict(int)
    for t in grp: tfs[t.get('tf', 'UNK')] += 1
    print(f"Timeframe Distribution:    {dict(tfs)}")

analyze_group("GROUP A: PREMATURE SHAKEOUT (>= 1.5R Left on Table)", big_cont)
analyze_group("GROUP B: CLEAN OPTIMAL EXITS (< 0.5R Left on Table)", clean_exit)
