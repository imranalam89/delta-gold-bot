import json
import itertools
from datetime import datetime, timezone
import numpy as np

# Load the bundle
with open('data/processed/all_11_agents_lab_bundle.json', 'r', encoding='utf-8') as f:
    bundle = json.load(f)

SNIPER_AGENTS = {'2:MAYA', '8:ELENA', '9:SAM', '11:LIAM', '4:NINA'}
NEGATIVE_EXPECTANCY_AGENTS = {'1:ALEX', '3:MARCUS', '6:SOPHIA'}

# Build unified candidate trade database with timeframe tags
all_trades_pool = []
for ag, data in bundle.items():
    tf_data = data.get('timeframes', {})
    for tf_label in ['1m', '5m', '15m', '1h']:
        tf_obj = tf_data.get(tf_label, {})
        trades = tf_obj.get('trades', [])
        for t in trades:
            t_copy = dict(t)
            t_copy['source_agent'] = ag
            t_copy['is_sniper'] = (ag in SNIPER_AGENTS)
            t_copy['tf'] = tf_label
            # Assign TF priority rank (1h=4, 15m=3, 5m=2, 1m=1)
            t_copy['tf_rank'] = {'1h': 4, '15m': 3, '5m': 2, '1m': 1}[tf_label]
            all_trades_pool.append(t_copy)

print(f"Loaded {len(all_trades_pool)} candidate trades across all 4 timeframes.")

def evaluate_portfolio(
    agent_filter_mode="ELITE_PLUS_MTF", # "ALL_11", "ELITE_ONLY", "ELITE_PLUS_MTF"
    allowed_tfs=("1m", "5m", "15m", "1h"),
    max_slots=2,
    sniper_sl=2.50,
    struct_sl_mult=1.25,
    be_trig_r=1.05,
    be_lock_r=0.38,
    trail_trig_r=2.30,
    trail_dist_r=0.95,
    cooldown_mins=8,
    use_loss_dampener=True,
    session_filter=True,
    tf_priority=True
):
    # 1. Filter candidate trades according to strategy rules
    filtered_cands = []
    for t in all_trades_pool:
        if t['tf'] not in allowed_tfs:
            continue
        ag = t['source_agent']
        if agent_filter_mode == "ELITE_ONLY":
            if ag in NEGATIVE_EXPECTANCY_AGENTS:
                continue
        elif agent_filter_mode == "ELITE_PLUS_MTF":
            # Allow negative expectancy agents ONLY on higher timeframes (15m, 1h) where their WR is >68%
            if ag in NEGATIVE_EXPECTANCY_AGENTS and t['tf'] in ("1m", "5m"):
                continue
        filtered_cands.append(t)

    # Sort candidates
    if tf_priority:
        # Prioritize higher timeframe signals and higher pnl at the same timestamp
        filtered_cands.sort(key=lambda x: (x['entry_ts'], -x['tf_rank'], -x.get('net_pnl', 0)))
    else:
        filtered_cands.sort(key=lambda x: (x['entry_ts'], -x.get('net_pnl', 0)))

    equity = 100.0
    peak_equity = 100.0
    max_dd_pct = 0.0
    fee_rate = 0.0001
    cooldown_seconds = cooldown_mins * 60

    active_trades = []
    executed_trades = []
    cooldown_ts = 0
    consec_losses = 0

    for cand in filtered_cands:
        ts = cand['entry_ts']
        dt_ent = datetime.fromtimestamp(ts, tz=timezone.utc)
        est_hr = (dt_ent.hour - 5) % 24

        # Update active trades
        remaining_active = []
        for at in active_trades:
            if at['exit_ts'] <= ts:
                net_p = at['net_pnl']
                equity += net_p
                peak_equity = max(peak_equity, equity)
                cur_dd = (peak_equity - equity) / peak_equity * 100.0
                max_dd_pct = max(max_dd_pct, cur_dd)
                executed_trades.append(at)

                if net_p < 0:
                    consec_losses += 1
                else:
                    consec_losses = 0
            else:
                remaining_active.append(at)

        active_trades = remaining_active

        if len(active_trades) >= max_slots:
            continue
        if ts < cooldown_ts:
            continue
        if session_filter and est_hr in (12, 13, 14, 15, 16):
            continue

        is_sniper = cand['is_sniper']
        orig_sl = cand['sl_dist']
        entry_px = cand['entry_price']

        if is_sniper:
            init_sl = min(sniper_sl, orig_sl)
        else:
            init_sl = min(struct_sl_mult * (orig_sl / 1.35), 8.5)
        init_sl = max(init_sl, 1.8)

        risk_usd = 5.0
        if use_loss_dampener and consec_losses >= 2:
            risk_usd = 2.50

        qty = round(risk_usd / init_sl, 4)
        peak_mfe = cand['peak_r'] * orig_sl
        peak_r_new = peak_mfe / init_sl
        direction = cand['direction']

        if direction == 'LONG':
            sl_px = round(entry_px - init_sl, 2)
        else:
            sl_px = round(entry_px + init_sl, 2)

        if cand['exit_reason'] == 'SL':
            r_mult = -1.0
            exit_px = sl_px
            exit_reason = 'SL'
        else:
            if peak_r_new >= be_trig_r:
                r_mult = be_lock_r
                exit_reason = 'BE_LOCK'
            if peak_r_new >= 1.80:
                banked_r = 0.40 * 1.80
                if peak_r_new >= trail_trig_r:
                    runner_r = 0.60 * (peak_r_new - trail_dist_r)
                    r_mult = banked_r + runner_r
                    exit_reason = 'CONSENSUS_RUNNER'
                    exit_px = round(entry_px + (r_mult * init_sl) if direction == 'LONG' else entry_px - (r_mult * init_sl), 2)
                else:
                    tp2_cap = min(peak_r_new, 3.35)
                    r_mult = banked_r + 0.60 * (tp2_cap - 0.40)
                    exit_reason = 'TP'
                    exit_px = round(entry_px + (r_mult * init_sl) if direction == 'LONG' else entry_px - (r_mult * init_sl), 2)
            else:
                r_mult = max(cand['r_multiple'], -1.0)
                exit_px = cand['exit_price']

        total_pts = round(r_mult * init_sl, 2)
        gross_usd = round(total_pts * qty, 2)
        fees = round(fee_rate * (qty * entry_px + qty * exit_px), 2)
        net_usd = round(gross_usd - fees, 2)

        active_trades.append({
            'entry_ts': ts,
            'exit_ts': cand['exit_ts'],
            'net_pnl': net_usd,
            'source_agent': cand['source_agent'],
            'tf': cand['tf'],
            'direction': direction,
            'exit_reason': exit_reason
        })
        cooldown_ts = ts + cooldown_seconds

    # Flush remaining
    for at in active_trades:
        net_p = at['net_pnl']
        equity += net_p
        peak_equity = max(peak_equity, equity)
        cur_dd = (peak_equity - equity) / peak_equity * 100.0
        max_dd_pct = max(max_dd_pct, cur_dd)
        executed_trades.append(at)

    wins = [t for t in executed_trades if t['net_pnl'] > 0]
    losses = [t for t in executed_trades if t['net_pnl'] <= 0]
    gross_win = sum(t['net_pnl'] for t in wins)
    gross_loss = abs(sum(t['net_pnl'] for t in losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else 99.0
    wr = (len(wins) / len(executed_trades) * 100.0) if executed_trades else 0.0
    tot_net = sum(t['net_pnl'] for t in executed_trades)
    calmar = (tot_net / 100.0) / (max_dd_pct / 100.0) if max_dd_pct > 0 else 0.0

    score = tot_net * (wr / 50.0) / (max_dd_pct + 1.0)

    return {
        'trades': len(executed_trades),
        'wr': wr,
        'net_pnl': tot_net,
        'end_equity': equity,
        'pf': pf,
        'max_dd': max_dd_pct,
        'calmar': calmar,
        'score': score
    }

# Parameter grid
agent_modes = ["ELITE_PLUS_MTF", "ELITE_ONLY", "ALL_11"]
tf_sets = [
    ("1m", "5m", "15m", "1h"),
    ("5m", "15m", "1h"),
    ("15m", "1h"),
    ("1m", "15m", "1h")
]
slots_list = [1, 2, 3]
sniper_sls = [2.0, 2.50, 3.0]
struct_mults = [1.15, 1.25, 1.45]
trail_trigs = [2.10, 2.40, 2.80]
trail_dists = [0.85, 1.05]
cooldowns = [4, 8, 12]
loss_dampeners = [True, False]
session_filters = [True, False]

total_combos = (
    len(agent_modes) * len(tf_sets) * len(slots_list) * len(sniper_sls) *
    len(struct_mults) * len(trail_trigs) * len(trail_dists) * len(cooldowns) *
    len(loss_dampeners) * len(session_filters)
)
print(f"Total potential combinations in grid: {total_combos}")

# Generate a balanced sample of 250 diverse combinations
np.random.seed(42)
sampled_combos = []

for a_mode in agent_modes:
    for t_set in tf_sets:
        for s in slots_list:
            for sl in sniper_sls:
                for sm in struct_mults:
                    for tt in trail_trigs:
                        for td in trail_dists:
                            sampled_combos.append({
                                'agent_filter_mode': a_mode,
                                'allowed_tfs': t_set,
                                'max_slots': s,
                                'sniper_sl': sl,
                                'struct_sl_mult': sm,
                                'be_trig_r': 1.05,
                                'be_lock_r': 0.38,
                                'trail_trig_r': tt,
                                'trail_dist_r': td,
                                'cooldown_mins': 8,
                                'use_loss_dampener': True,
                                'session_filter': True,
                                'tf_priority': True
                            })

print(f"Evaluating {len(sampled_combos)} combinations across 4 timeframes...")
results = []
for i, params in enumerate(sampled_combos):
    res = evaluate_portfolio(**params)
    res_entry = dict(params)
    res_entry.update(res)
    res_entry['combo_id'] = i + 1
    results.append(res_entry)

# Sort by institutional quality score
results.sort(key=lambda x: -x['score'])

print("\n" + "=" * 135)
print(f"{'Rank':<4} | {'Mode':<14} | {'TFs':<16} | {'Slots':<5} | {'Trades':<6} | {'WR %':<6} | {'PF':<5} | {'Net PnL':<10} | {'Max DD':<7} | {'Calmar':<6} | {'Score':<7}")
print("=" * 135)

for rank, r in enumerate(results[:25], 1):
    tf_str = "+".join(r['allowed_tfs'])
    print(f"{rank:<4} | {r['agent_filter_mode']:<14} | {tf_str:<16} | {r['max_slots']:<5} | {r['trades']:<6} | {r['wr']:<6.2f}% | {r['pf']:<5.2f} | ${r['net_pnl']:<9.2f} | -{r['max_dd']:<6.2f}% | {r['calmar']:<6.2f} | {r['score']:<7.2f}")

# Save results to CSV
import csv
with open('data/processed/mtf_100s_combinations_results.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    writer.writeheader()
    for r in results:
        writer.writerow(r)

print(f"\nSaved full {len(results)} combo results to data/processed/mtf_100s_combinations_results.csv")
