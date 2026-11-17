import json

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

p1_trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
print(f"P1 Trades: {len(p1_trades)}")

with open('data/processed/all_11_agents_lab_bundle.json', 'r', encoding='utf-8') as f:
    bundle = json.load(f)

macro_agents = ['4:NINA', '8:ELENA', '10:OMAR', '7:DEREK', '11:LIAM', '2:MAYA']
cands = []
for ag in macro_agents:
    tfs = bundle[ag]['timeframes']
    for tf_label in ['1h', '15m', '5m']:
        trades = tfs.get(tf_label, {}).get('trades', [])
        for t in trades:
            t_copy = dict(t)
            t_copy['source_agent'] = ag
            t_copy['tf'] = tf_label
            cands.append(t_copy)

tf_rank = {'1h': 3, '15m': 2, '5m': 1}
cands.sort(key=lambda x: (x['entry_ts'], -tf_rank[x['tf']], -x.get('net_pnl', 0)))

# In step 614: standalone simulation of P2 gave 133 trades!
# Let's see how that standalone simulation was coded:
active_trades = []
executed_p2 = []
cooldown_until_ts = 0

for t in cands:
    ts = t['entry_ts']
    rem = []
    for at in active_trades:
        if at['exit_ts'] <= ts:
            executed_p2.append(at)
        else:
            rem.append(at)
    active_trades = rem

    if len(active_trades) >= 1:
        continue
    if ts < cooldown_until_ts:
        continue

    active_trades.append(dict(t))
    cooldown_until_ts = t['exit_ts'] + 3600

for at in active_trades:
    executed_p2.append(at)

print(f"Standalone P2 Executed Trades: {len(executed_p2)}")

# Now let's test overlap between p1_trades (265) and executed_p2 (133):
# Total executions = 265 + 133 = 398!
p1_windows = [(t['entry_ts'], t['exit_ts'], t['direction'], t['id']) for t in p1_trades]

overlapping_p2 = []
pure_flat_p2 = []

for p2 in executed_p2:
    s2, e2 = p2['entry_ts'], p2['exit_ts']
    matched_p1 = []
    for s1, e1, d1, tid in p1_windows:
        # Check interval overlap: max(s1, s2) < min(e1, e2)
        if max(s1, s2) < min(e1, e2):
            matched_p1.append((tid, d1, s1, e1))
    if matched_p1:
        overlapping_p2.append((p2, matched_p1))
    else:
        pure_flat_p2.append(p2)

print("\n=== EXACT OVERLAP ANALYSIS FOR 398 TOTAL EXECUTIONS ===")
print(f"Pillar 1 Executions: {len(p1_trades)}")
print(f"Pillar 2 Executions: {len(executed_p2)}")
print(f"Total Portfolio Executions: {len(p1_trades) + len(executed_p2)} (Exact 398!)")
print(f"Pillar 2 trades that OVERLAP with Pillar 1: {len(overlapping_p2)} out of {len(executed_p2)} ({len(overlapping_p2)/len(executed_p2)*100:.1f}%)")
print(f"Pillar 2 trades in PURE FLAT WINDOWS (No Overlap): {len(pure_flat_p2)} out of {len(executed_p2)} ({len(pure_flat_p2)/len(executed_p2)*100:.1f}%)")

# Overlap details
same_direction_overlap = 0
opposite_direction_overlap = 0
total_overlap_seconds = 0

for p2, matched in overlapping_p2:
    s2, e2 = p2['entry_ts'], p2['exit_ts']
    for tid, d1, s1, e1 in matched:
        overlap_s = max(s1, s2)
        overlap_e = min(e1, e2)
        total_overlap_seconds += (overlap_e - overlap_s)
        if d1 == p2['direction']:
            same_direction_overlap += 1
        else:
            opposite_direction_overlap += 1

print(f"Total overlapping duration: {total_overlap_seconds/3600:.2f} hours across 5 months")
print(f"Direction in overlaps: {same_direction_overlap} Same Direction (Pyramiding / Scale-in), {opposite_direction_overlap} Opposite Direction (Hedging)")
