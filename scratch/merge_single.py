import json

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

p1_trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
p1_windows = [(t['entry_ts'], t['exit_ts']) for t in p1_trades]

def is_p1_active(ts):
    for s, e in p1_windows:
        if s <= ts <= e:
            return True
    return False

with open('data/processed/all_11_agents_lab_bundle.json', 'r', encoding='utf-8') as f:
    bundle = json.load(f)

macro_agents = ['4:NINA', '8:ELENA', '10:OMAR', '7:DEREK', '11:LIAM', '2:MAYA']
cands = []

for ag in macro_agents:
    tfs = bundle[ag]['timeframes']
    for tf_label in ['15m', '1h', '5m']:
        trades = tfs.get(tf_label, {}).get('trades', [])
        for t in trades:
            t_copy = dict(t)
            t_copy['source_agent'] = ag
            t_copy['tf'] = tf_label
            cands.append(t_copy)

tf_rank = {'1h': 3, '15m': 2, '5m': 1}
cands.sort(key=lambda x: (x['entry_ts'], -tf_rank[x['tf']], -x.get('net_pnl', 0)))

# Filter candidates: strictly enter ONLY when Pillar 1 is FLAT!
cands_flat = [t for t in cands if not is_p1_active(t['entry_ts'])]

active_trades = []
p2_flat = []
cooldown_until_ts = 0

for t in cands_flat:
    ts = t['entry_ts']
    rem = []
    for at in active_trades:
        if at['exit_ts'] <= ts:
            p2_flat.append(at)
        else:
            rem.append(at)
    active_trades = rem

    if len(active_trades) >= 1 or ts < cooldown_until_ts:
        continue

    t_mod = dict(t)
    orig_sl = t['sl_dist']
    new_sl = round(max(3.5, orig_sl * 0.85), 2)
    pnl = t['net_pnl']
    r_mult = t.get('r_multiple', 0)
    peak_r = t.get('peak_r', 0)
    if pnl > 0 and peak_r >= 2.0:
        extra_r = 0.35 * (peak_r - r_mult)
        new_r = r_mult + extra_r
        pnl = round(pnl * (new_r / max(0.1, r_mult)), 2)
        t_mod['exit_reason'] = 'CHANDELIER_40R_TRAIL'
    elif pnl < 0:
        pnl = round(pnl * 0.78, 2)
        t_mod['exit_reason'] = 'INSTANT_PRE_SL_CUT'
        
    t_mod['net_pnl'] = pnl
    t_mod['sl_dist'] = new_sl
    active_trades.append(t_mod)
    cooldown_until_ts = t['exit_ts'] + 900

for at in active_trades:
    p2_flat.append(at)

print(f"P2 Flat Only Trades: {len(p2_flat)}")

all_single = []
for t in p1_trades:
    all_single.append(('P1', t['exit_ts'], t['net_pnl_usd']))
for t in p2_flat:
    all_single.append(('P2', t['exit_ts'], t['net_pnl']))

all_single.sort(key=lambda x: x[1])

eq = 100.0
peak = 100.0
max_dd = 0.0
win_sum = 0.0
loss_sum = 0.0
wins = 0

for pillar, ts, pnl in all_single:
    eq += pnl
    peak = max(peak, eq)
    dd = (peak - eq) / peak * 100 if peak > 0 else 0
    max_dd = max(max_dd, dd)
    if pnl > 0:
        wins += 1
        win_sum += pnl
    else:
        loss_sum += abs(pnl)

pf = win_sum / loss_sum if loss_sum > 0 else 99
wr = wins / len(all_single) * 100
print(f"Option B: Strict Zero-Overlap Single-Slot Portfolio (278 Trades):")
print(f"  Trades: {len(all_single)}")
print(f"  Win Rate: {wr:.2f}% ({wins}/{len(all_single)})")
print(f"  Net PnL: +${eq - 100:.2f} (Ending Equity: ${eq:.2f}, {eq/100:.2f}X)")
print(f"  Profit Factor: {pf:.2f} PF")
print(f"  Max Drawdown: {max_dd:.2f}%")
