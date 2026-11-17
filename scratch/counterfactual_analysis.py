import json, base64, struct, datetime
import numpy as np

print("[1/4] Loading payload and decoding continuous 1m bars...")
with open('data/processed/dashboard_payload.json', 'r') as f:
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

print(f"Decoded {n} 1m bars successfully.")

p = data['profiles']['MUX_085SL_40R_CONTINUOUS_TRAIL']
trades = p['trades']

# =========================================================================
# PART 1: INSTANT PRE-SL CUT FORENSICS
# =========================================================================
print("\n" + "="*80)
print("PART 1: INSTANT PRE-SL CUT FORENSICS (14 TRADES)")
print("="*80)

instant_cuts = [t for t in trades if 'INSTANT' in t['exit_reason']]

hit_full_sl = []
reversed_to_win = []
reversed_to_be = []

for t in instant_cuts:
    t_id = t['id']
    ent_idx = t['entry_idx']
    exit_idx = t['exit_idx']
    direction = t['direction']
    ent_px = t['entry_price']
    sl_px = t['sl_price']
    init_risk = t['init_risk_pts']
    exit_px = t['exit_price']
    actual_r = t['r_multiple']
    actual_net = t['net_pnl_usd']
    
    # Check subsequent bars (up to max hold of 120-270 bars or end of day)
    # What happens between exit_idx and exit_idx + 150?
    end_check = min(n, exit_idx + 180)
    
    sl_hit_sub = False
    tp1_hit_sub = False
    be_hit_sub = False
    first_event = None
    first_event_idx = None
    
    tp1_px = t.get('tp1_price', ent_px + 1.8 * init_risk if direction == 'LONG' else ent_px - 1.8 * init_risk)
    
    for k in range(exit_idx, end_check):
        if direction == 'LONG':
            if lows[k] <= sl_px:
                sl_hit_sub = True
                first_event = 'SL'
                first_event_idx = k
                break
            if highs[k] >= tp1_px:
                tp1_hit_sub = True
                first_event = 'TP1'
                first_event_idx = k
                break
            if highs[k] >= ent_px and not be_hit_sub:
                be_hit_sub = True
        else: # SHORT
            if highs[k] >= sl_px:
                sl_hit_sub = True
                first_event = 'SL'
                first_event_idx = k
                break
            if lows[k] <= tp1_px:
                tp1_hit_sub = True
                first_event = 'TP1'
                first_event_idx = k
                break
            if lows[k] <= ent_px and not be_hit_sub:
                be_hit_sub = True
                
    post_info = {
        'id': t_id,
        'date': t['date_str'],
        'dir': direction,
        'entry': ent_px,
        'exit': exit_px,
        'sl': sl_px,
        'actual_r': actual_r,
        'actual_net': actual_net,
        'first_event': first_event,
        'bars_to_event': (first_event_idx - exit_idx) if first_event_idx else None,
        'be_touched': be_hit_sub
    }
    
    if first_event == 'SL':
        hit_full_sl.append(post_info)
    elif first_event == 'TP1':
        reversed_to_win.append(post_info)
    elif be_hit_sub:
        reversed_to_be.append(post_info)
    else:
        hit_full_sl.append(post_info)

print(f"Total Instant Pre-SL Cuts: {len(instant_cuts)}")
print(f"1. Trades that would have hit FULL STOP LOSS (-1.0R) if not cut: {len(hit_full_sl)} ({len(hit_full_sl)/len(instant_cuts)*100:.1f}%)")
print(f"2. Trades that reversed to reach TP1 (+1.8R): {len(reversed_to_win)} ({len(reversed_to_win)/len(instant_cuts)*100:.1f}%)")
print(f"3. Trades that reversed back to Breakeven/Entry but didn't reach TP1: {len(reversed_to_be)} ({len(reversed_to_be)/len(instant_cuts)*100:.1f}%)")

print("\nDetail of each Instant Pre-SL Cut:")
for item in hit_full_sl + reversed_to_win + reversed_to_be:
    res = item['first_event'] or ('BE_TOUCH' if item['be_touched'] else 'DRIFT_TO_SL')
    print(f"Trade #{item['id']:3} ({item['date']}) {item['dir']:5} | Cut at {item['actual_r']:+.2f}R (${item['actual_net']:+.2f}) | Subseq: {res:10} (in {item['bars_to_event']} bars)")

# =========================================================================
# PART 2: REVERSAL CUT FORENSICS
# =========================================================================
print("\n" + "="*80)
print("PART 2: REVERSAL CUT FORENSICS (12 TRADES)")
print("="*80)

reversals = [t for t in trades if 'REVERSAL' in t['exit_reason']]

rev_sl_hits = []
rev_tp_hits = []
rev_be_hits = []

for t in reversals:
    t_id = t['id']
    ent_idx = t['entry_idx']
    exit_idx = t['exit_idx']
    direction = t['direction']
    ent_px = t['entry_price']
    sl_px = t['sl_price']
    init_risk = t['init_risk_pts']
    exit_px = t['exit_price']
    actual_r = t['r_multiple']
    actual_net = t['net_pnl_usd']
    tp1_px = t.get('tp1_price', ent_px + 1.8 * init_risk if direction == 'LONG' else ent_px - 1.8 * init_risk)
    tp2_px = t.get('tp2_price', ent_px + 4.5 * init_risk if direction == 'LONG' else ent_px - 4.5 * init_risk)
    
    end_check = min(n, exit_idx + 180)
    first_event = None
    first_event_idx = None
    
    for k in range(exit_idx, end_check):
        if direction == 'LONG':
            if lows[k] <= sl_px:
                first_event = 'SL'
                first_event_idx = k
                break
            if highs[k] >= tp2_px:
                first_event = 'TP2'
                first_event_idx = k
                break
            if highs[k] >= tp1_px:
                first_event = 'TP1'
                first_event_idx = k
                break
        else:
            if highs[k] >= sl_px:
                first_event = 'SL'
                first_event_idx = k
                break
            if lows[k] <= tp2_px:
                first_event = 'TP2'
                first_event_idx = k
                break
            if lows[k] <= tp1_px:
                first_event = 'TP1'
                first_event_idx = k
                break
                
    post_info = {
        'id': t_id,
        'date': t['date_str'],
        'dir': direction,
        'entry': ent_px,
        'exit': exit_px,
        'actual_r': actual_r,
        'actual_net': actual_net,
        'first_event': first_event or 'TIME_EXPIRE',
        'bars_to_event': (first_event_idx - exit_idx) if first_event_idx else None
    }
    if first_event == 'SL':
        rev_sl_hits.append(post_info)
    elif first_event in ('TP1', 'TP2'):
        rev_tp_hits.append(post_info)
    else:
        rev_be_hits.append(post_info)

print(f"Total Reversal Cuts: {len(reversals)}")
print(f"1. Trades that would have hit STOP LOSS (-1.0R) if not cut: {len(rev_sl_hits)} ({len(rev_sl_hits)/len(reversals)*100:.1f}%)")
print(f"2. Trades that would have hit TP1 / TP2: {len(rev_tp_hits)} ({len(rev_tp_hits)/len(reversals)*100:.1f}%)")
print(f"3. Trades that would have expired or chopped: {len(rev_be_hits)} ({len(rev_be_hits)/len(reversals)*100:.1f}%)")

print("\nDetail of each Reversal Cut:")
for item in rev_sl_hits + rev_tp_hits + rev_be_hits:
    print(f"Trade #{item['id']:3} ({item['date']}) {item['dir']:5} | Cut at {item['actual_r']:+.2f}R (${item['actual_net']:+.2f}) | If held: {item['first_event']:10} (in {item['bars_to_event']} bars)")

# =========================================================================
# PART 3: TRAILING SL HIT & POST-TRAILING CONTINUATION ANALYSIS
# =========================================================================
print("\n" + "="*80)
print("PART 3: TRAILING SL EXITS & POST-EXIT CONTINUATION (86 TRADES)")
print("="*80)

trails = [t for t in trades if any(k in t['exit_reason'] for k in ['40R', 'TRAIL', 'RUNNER'])]

continuation_records = []

for t in trails:
    t_id = t['id']
    ent_idx = t['entry_idx']
    exit_idx = t['exit_idx']
    direction = t['direction']
    ent_px = t['entry_price']
    exit_px = t['exit_price']
    sl_dist = t['init_risk_pts']
    actual_r = t['r_multiple']
    
    # Check next 60 bars (1 hour) and next 120 bars (2 hours)
    end_60 = min(n, exit_idx + 60)
    end_120 = min(n, exit_idx + 120)
    
    if direction == 'LONG':
        sub_highs_60 = highs[exit_idx:end_60]
        max_favorable_60 = np.max(sub_highs_60) - exit_px if len(sub_highs_60) > 0 else 0.0
        sub_highs_120 = highs[exit_idx:end_120]
        max_favorable_120 = np.max(sub_highs_120) - exit_px if len(sub_highs_120) > 0 else 0.0
    else: # SHORT
        sub_lows_60 = lows[exit_idx:end_60]
        max_favorable_60 = exit_px - np.min(sub_lows_60) if len(sub_lows_60) > 0 else 0.0
        sub_lows_120 = lows[exit_idx:end_120]
        max_favorable_120 = exit_px - np.min(sub_lows_120) if len(sub_lows_120) > 0 else 0.0
        
    mfe_60_r = round(max(0.0, float(max_favorable_60 / sl_dist)), 2)
    mfe_120_r = round(max(0.0, float(max_favorable_120 / sl_dist)), 2)
    
    continuation_records.append({
        'id': t_id,
        'date': t['date_str'],
        'actual_r': actual_r,
        'mfe_60_r': mfe_60_r,
        'mfe_120_r': mfe_120_r,
        'mfe_60_pts': round(max_favorable_60, 2),
        'mfe_120_pts': round(max_favorable_120, 2)
    })

c_60_05 = sum(1 for r in continuation_records if r['mfe_60_r'] >= 0.5)
c_60_10 = sum(1 for r in continuation_records if r['mfe_60_r'] >= 1.0)
c_60_20 = sum(1 for r in continuation_records if r['mfe_60_r'] >= 2.0)
c_60_30 = sum(1 for r in continuation_records if r['mfe_60_r'] >= 3.0)

c_120_05 = sum(1 for r in continuation_records if r['mfe_120_r'] >= 0.5)
c_120_10 = sum(1 for r in continuation_records if r['mfe_120_r'] >= 1.0)
c_120_20 = sum(1 for r in continuation_records if r['mfe_120_r'] >= 2.0)
c_120_30 = sum(1 for r in continuation_records if r['mfe_120_r'] >= 3.0)

ideal_exits = sum(1 for r in continuation_records if r['mfe_60_r'] < 0.3)

print(f"Total Trailing SL Exits: {len(trails)}")
print(f"Average Actual Captured R: {np.mean([r['actual_r'] for r in continuation_records]):.2f}R")
print(f"1. Optimal Exits (Price reversed within <0.3R of trail exit): {ideal_exits} ({ideal_exits/len(trails)*100:.1f}%)")
print(f"2. Within 60 minutes after Trailing Exit:")
print(f"   - Extended >= 0.5R further: {c_60_05} ({c_60_05/len(trails)*100:.1f}%)")
print(f"   - Extended >= 1.0R further: {c_60_10} ({c_60_10/len(trails)*100:.1f}%)")
print(f"   - Extended >= 2.0R further: {c_60_20} ({c_60_20/len(trails)*100:.1f}%)")
print(f"   - Extended >= 3.0R further: {c_60_30} ({c_60_30/len(trails)*100:.1f}%)")
print(f"3. Within 120 minutes after Trailing Exit:")
print(f"   - Extended >= 0.5R further: {c_120_05} ({c_120_05/len(trails)*100:.1f}%)")
print(f"   - Extended >= 1.0R further: {c_120_10} ({c_120_10/len(trails)*100:.1f}%)")
print(f"   - Extended >= 2.0R further: {c_120_20} ({c_120_20/len(trails)*100:.1f}%)")
print(f"   - Extended >= 3.0R further: {c_120_30} ({c_120_30/len(trails)*100:.1f}%)")

top_continuation = sorted(continuation_records, key=lambda x: -x['mfe_120_r'])[:10]
print("\nTop 10 Trades with Biggest Subsequent Move Left on the Table:")
for r in top_continuation:
    print(f"Trade #{r['id']:3} ({r['date']}) | Captured: {r['actual_r']:+5.2f}R | Post-Exit Continuation in 2h: +{r['mfe_120_r']:.2f}R (+{r['mfe_120_pts']:.1f} pts)")
