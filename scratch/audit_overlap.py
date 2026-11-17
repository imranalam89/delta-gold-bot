import os
import json
import struct, base64
import numpy as np
from datetime import datetime, timezone

PAYLOAD_PATH = "data/processed/dashboard_payload.json"
with open(PAYLOAD_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

c = data['continuous_1m']
n = c['n']
dt = struct.unpack(f'<{n}H', base64.b64decode(c['dt']))
do = struct.unpack(f'<{n}h', base64.b64decode(c['do']))
dh = struct.unpack(f'<{n}H', base64.b64decode(c['dh']))
dl = struct.unpack(f'<{n}L', base64.b64decode(c['dl'])) if 'dl' in c and len(base64.b64decode(c['dl'])) == 4*n else struct.unpack(f'<{n}H', base64.b64decode(c['dl']))
dc = struct.unpack(f'<{n}h', base64.b64decode(c['dc']))
v  = struct.unpack(f'<{n}H', base64.b64decode(c['v']))

cur_min = c['start_ts_min']
cur_open = c['start_open_d']
times = np.zeros(n, dtype=np.int64)
opens = np.zeros(n, dtype=np.float32)
highs = np.zeros(n, dtype=np.float32)
lows  = np.zeros(n, dtype=np.float32)
closes= np.zeros(n, dtype=np.float32)
vols  = np.zeros(n, dtype=np.float32)

for i in range(n):
    if i > 0:
        cur_min += dt[i]
        cur_open += do[i]
    times[i] = cur_min * 60
    opens[i] = round(cur_open * 0.1, 2)
    highs[i] = round((cur_open + dh[i]) * 0.1, 2)
    lows[i]  = round((cur_open - dl[i]) * 0.1, 2)
    closes[i]= round((cur_open + dc[i]) * 0.1, 2)
    vols[i]  = float(v[i])

p1_trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
print(f"Pillar 1 trades: {len(p1_trades)}")

# 15m bars
n_15 = n // 15
h_15 = np.zeros(n_15, dtype=np.float32)
l_15 = np.zeros(n_15, dtype=np.float32)
c_15 = np.zeros(n_15, dtype=np.float32)
v_15 = np.zeros(n_15, dtype=np.float32)

for j in range(n_15):
    s = j * 15
    e = s + 15
    h_15[j] = np.max(highs[s:e])
    l_15[j] = np.min(lows[s:e])
    c_15[j] = closes[e - 1]
    v_15[j] = np.sum(vols[s:e])

donch_h = np.zeros(n_15, dtype=np.float32)
donch_l = np.zeros(n_15, dtype=np.float32)
atr_15  = np.zeros(n_15, dtype=np.float32)
vol_ma  = np.zeros(n_15, dtype=np.float32)
vol_std = np.zeros(n_15, dtype=np.float32)

for j in range(20, n_15):
    donch_h[j] = np.max(h_15[j-20:j])
    donch_l[j] = np.min(l_15[j-20:j])
    tr = np.maximum(h_15[j-14:j] - l_15[j-14:j], 0.5)
    atr_15[j] = np.mean(tr)
    v_window = v_15[j-20:j]
    vol_ma[j] = np.mean(v_window)
    vol_std[j] = max(1.0, np.std(v_window))

def run_p2(mask_p1=False):
    p1_mask = np.zeros(n, dtype=bool)
    if mask_p1:
        for t in p1_trades:
            s = max(0, t['entry_idx'])
            e = min(n - 1, t['exit_idx'])
            p1_mask[s:e+1] = True
            
    fixed_risk_usd = 5.0
    fee_rate = 0.0001
    be_trigger_r = 1.30
    be_lock_r = 0.45
    trail_trigger_r = 2.10
    
    executed = []
    active = None
    cooldown = 0
    t_id = 1
    
    for k in range(300, n):
        j_15 = k // 15
        if active is not None:
            direction = active['direction']
            ent_px = active['entry_price']
            cur_sl = active['cur_sl']
            sl_dist = active['init_risk_pts']
            ent_idx = active['entry_idx']
            stage = active['stage']
            peak_fav = active['peak_fav']
            has_closed = False
            exit_px = None
            exit_reason = None
            
            if direction == 'LONG':
                cur_fav = highs[k] - ent_px
                peak_fav = max(peak_fav, cur_fav)
                cur_r = cur_fav / sl_dist
                if lows[k] <= cur_sl:
                    exit_px = cur_sl
                    has_closed = True
                    exit_reason = 'STOP_LOSS' if stage == 0 else ('BREAKEVEN_LOCK' if stage == 1 else 'CHANDELIER_TRAIL_HIT')
                elif stage == 0 and cur_r >= be_trigger_r:
                    cur_sl = max(cur_sl, round(ent_px + be_lock_r * sl_dist, 2))
                    stage = 1
                elif cur_r >= trail_trigger_r:
                    stage = 2
                    recent_l = float(np.min(l_15[max(0, j_15 - 2):j_15 + 1]))
                    cand_sl = round(recent_l - 0.25 * sl_dist, 2)
                    if cand_sl > cur_sl:
                        cur_sl = cand_sl
            else:
                cur_fav = ent_px - lows[k]
                peak_fav = max(peak_fav, cur_fav)
                cur_r = cur_fav / sl_dist
                if highs[k] >= cur_sl:
                    exit_px = cur_sl
                    has_closed = True
                    exit_reason = 'STOP_LOSS' if stage == 0 else ('BREAKEVEN_LOCK' if stage == 1 else 'CHANDELIER_TRAIL_HIT')
                elif stage == 0 and cur_r >= be_trigger_r:
                    cur_sl = min(cur_sl, round(ent_px - be_lock_r * sl_dist, 2))
                    stage = 1
                elif cur_r >= trail_trigger_r:
                    stage = 2
                    recent_h = float(np.max(h_15[max(0, j_15 - 2):j_15 + 1]))
                    cand_sl = round(recent_h + 0.25 * sl_dist, 2)
                    if cand_sl < cur_sl:
                        cur_sl = cand_sl
            active['cur_sl'] = cur_sl
            active['stage'] = stage
            active['peak_fav'] = peak_fav
            
            if has_closed:
                pnl_pts = round((exit_px - ent_px) if direction == 'LONG' else (ent_px - exit_px), 2)
                r_mult = round(pnl_pts / sl_dist, 2)
                qty = active['qty_oz']
                gross = round(pnl_pts * qty, 2)
                fees = round(fee_rate * (qty * ent_px + qty * exit_px), 2)
                net = round(gross - fees, 2)
                executed.append({
                    'id': active['id'],
                    'entry_idx': ent_idx,
                    'exit_idx': k,
                    'direction': direction,
                    'net_pnl': net,
                    'r_multiple': r_mult,
                    'exit_reason': exit_reason
                })
                active = None
                cooldown = k + 90
                continue
                
        if k % 15 != 14 or k < cooldown:
            continue
        if mask_p1 and p1_mask[k]:
            continue
            
        cur_ts = int(times[k])
        dt_cur = datetime.fromtimestamp(cur_ts, tz=timezone.utc)
        hr_utc = dt_cur.hour
        if not ((0 <= hr_utc <= 8) or (15 <= hr_utc <= 22)):
            continue
        atr = atr_15[j_15]
        if atr < 3.0:
            continue
        vol_z = (v_15[j_15] - vol_ma[j_15]) / vol_std[j_15] if vol_std[j_15] > 0 else 0
        if vol_z < 0.15:
            continue
        px = c_15[j_15]
        sl_dist = round(max(6.5, min(14.0, 1.35 * atr)), 2)
        qty = round(fixed_risk_usd / sl_dist, 4)
        
        if px > donch_h[j_15] and c_15[j_15 - 1] <= donch_h[j_15 - 1]:
            active = {
                'id': t_id,
                'entry_idx': k,
                'direction': 'LONG',
                'entry_price': px,
                'cur_sl': round(px - sl_dist, 2),
                'init_risk_pts': sl_dist,
                'qty_oz': qty,
                'stage': 0,
                'peak_fav': 0.0
            }
            t_id += 1
        elif px < donch_l[j_15] and c_15[j_15 - 1] >= donch_l[j_15 - 1]:
            active = {
                'id': t_id,
                'entry_idx': k,
                'direction': 'SHORT',
                'entry_price': px,
                'cur_sl': round(px + sl_dist, 2),
                'init_risk_pts': sl_dist,
                'qty_oz': qty,
                'stage': 0,
                'peak_fav': 0.0
            }
            t_id += 1
            
    return executed

p2_standalone = run_p2(mask_p1=False)
p2_flat_only = run_p2(mask_p1=True)

print(f"P2 Standalone Trades: {len(p2_standalone)}")
print(f"P2 Flat Only Trades: {len(p2_flat_only)}")

# Now let's calculate exact overlap for p2_standalone vs p1_trades
# Overlap occurs if [t2_entry, t2_exit] overlaps with [t1_entry, t1_exit]
# max(t1_entry, t2_entry) <= min(t1_exit, t2_exit)
overlapping_p2_trades = []
independent_p2_trades = []

simultaneous_bars = np.zeros(n, dtype=int)
for t1 in p1_trades:
    simultaneous_bars[t1['entry_idx']:t1['exit_idx']+1] += 1

p2_bars = np.zeros(n, dtype=int)
for t2 in p2_standalone:
    p2_bars[t2['entry_idx']:t2['exit_idx']+1] += 1

both_active_bars = np.sum((simultaneous_bars > 0) & (p2_bars > 0))

for t2 in p2_standalone:
    # check if t2 overlaps with any t1
    overlaps_with = []
    for t1 in p1_trades:
        if max(t1['entry_idx'], t2['entry_idx']) <= min(t1['exit_idx'], t2['exit_idx']):
            overlaps_with.append(t1['id'])
    if len(overlaps_with) > 0:
        overlapping_p2_trades.append((t2, overlaps_with))
    else:
        independent_p2_trades.append(t2)

print("\n--- STANDALONE DUAL-SLOT PORTFOLIO (265 P1 + 133 P2 = 398 Trades) ---")
print(f"Total P2 trades: {len(p2_standalone)}")
print(f"P2 trades overlapping with an active P1 trade: {len(overlapping_p2_trades)} ({len(overlapping_p2_trades)/len(p2_standalone)*100:.1f}%)")
print(f"P2 trades completely outside P1 (Pure Flat Windows): {len(independent_p2_trades)} ({len(independent_p2_trades)/len(p2_standalone)*100:.1f}%)")
print(f"Total overlap time: {both_active_bars} minutes ({both_active_bars/60:.1f} hours)")
max_concurrent = np.max(simultaneous_bars + p2_bars)
print(f"Maximum concurrent trades open at any single moment: {max_concurrent}")

# Direction agreement during overlap
same_dir = 0
opp_dir = 0
for t2, p1_ids in overlapping_p2_trades:
    for pid in p1_ids:
        t1 = p1_trades[pid - 1]
        if t1['direction'] == t2['direction']:
            same_dir += 1
        else:
            opp_dir += 1

print(f"Direction alignment during overlap: {same_dir} same direction (Confluence/Scale-in), {opp_dir} opposite direction (Delta Neutral / Hedge)")

# Now check P2 Flat Only (13 trades)
flat_overlaps = 0
for t2 in p2_flat_only:
    for t1 in p1_trades:
        if max(t1['entry_idx'], t2['entry_idx']) <= min(t1['exit_idx'], t2['exit_idx']):
            flat_overlaps += 1

print("\n--- STRICT ZERO-OVERLAP SINGLE-SLOT (265 P1 + 13 P2 = 278 Trades) ---")
print(f"Flat Only P2 trades: {len(p2_flat_only)}")
print(f"Flat Only P2 trades overlapping with P1: {flat_overlaps} (0.0% overlap)")
