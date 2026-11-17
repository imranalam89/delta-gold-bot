"""
Syndicate Alpha — Backtest of Reverse-Engineered Strategy Settings
------------------------------------------------------------------
Settings derived directly from the 728 Big Moves Forensic Report:
- SL: $6.80 pts (matching 85th percentile pre-takeoff adverse pullback)
- BE Lock: Trigger @ 1.10R, Lock @ +0.38R
- Partial TP1: @ 1.80R ($12.24 pts)
- Full TP2 / Trail: Trigger @ 2.50R ($17.00 pts), Trail Dist 0.85R
- Max Hold: 270 minutes (4.5 hours, matching the 4.4h median duration)
- Sessions: Asian Open (18-23 EST) + London Open (02-07 EST) + NY Morning (08-11 EST)
- Agents: Pre-move DNA Specialists (Elena, Derek, Maya, Nina, Omar, Liam)
"""

import json
import os
import sys
import csv
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print("[INIT] Loading Master Parquet dataset...")
df = pd.read_parquet(os.path.join(BASE_DIR, 'data', 'processed', 'GC_v0_2Year_L2_OrderFlow_Master.parquet'))
if not df.index.tz:
    df.index = df.index.tz_localize('UTC')
else:
    df.index = df.index.tz_convert('UTC')

start_dt = pd.to_datetime('2026-05-28 22:00:00', utc=True)
df_5m = df.loc[start_dt:].copy()

times = df_5m.index.to_numpy()
closes = df_5m['close'].to_numpy(dtype=np.float64)
highs = df_5m['high'].to_numpy(dtype=np.float64)
lows = df_5m['low'].to_numpy(dtype=np.float64)
opens = df_5m['open'].to_numpy(dtype=np.float64)
est_hours = ((df_5m.index.hour - 5) % 24).to_numpy(dtype=np.int32)
n_bars = len(closes)

time_to_idx = {ts: idx for idx, ts in enumerate(times)}

with open(os.path.join(BASE_DIR, 'data', 'processed', 'all_11_agents_lab_bundle.json'), 'r', encoding='utf-8') as f:
    bundle = json.load(f)

# Collect signals matching pre-move DNA agents
DNA_AGENTS = {'8:ELENA', '7:DEREK', '2:MAYA', '4:NINA', '10:OMAR', '11:LIAM'}

signals = []
for ag in DNA_AGENTS:
    tf_data = bundle.get(ag, {}).get('timeframes', {})
    for tf_label in ['1m', '5m', '15m', '1h']:
        trades = tf_data.get(tf_label, {}).get('trades', [])
        for t in trades:
            dt_ts = pd.to_datetime(t['entry_time'], utc=True)
            if dt_ts in time_to_idx:
                idx = time_to_idx[dt_ts]
                signals.append({
                    'idx': idx,
                    'ts': int(t['entry_ts']),
                    'entry_time': t['entry_time'],
                    'agent': ag,
                    'direction': t['direction'],
                    'tf': tf_label,
                    'tf_rank': {'1h': 4, '15m': 3, '5m': 2, '1m': 1}[tf_label],
                    'orig_sl_dist': float(t['sl_dist'])
                })

signals.sort(key=lambda x: (x['ts'], -x['tf_rank']))
print(f"[REVERSE STRATEGY] Filtered to {len(signals)} signals matching DNA Specialists.")

def run_reverse_engineered_backtest(
    sl_fixed_pts=6.80,       # from 85th percentile adverse pullback
    be_trig_r=1.10,
    be_lock_r=0.38,
    tp1_r=1.80,
    tp2_r=3.50,              # from median $33 move
    trail_trig_r=2.50,
    trail_dist_r=0.85,
    max_hold_bars=270,        # 4.5 hours from median move duration
    max_slots=2,
    cooldown_bars=15,
    fixed_risk_usd=5.0,
    fee_rate=0.0001
):
    equity = 100.0
    peak_equity = 100.0
    max_dd_pct = 0.0

    active_trades = []
    executed_trades = []
    cooldown_until_idx = -999
    consec_losses = 0

    for sig in signals:
        idx = sig['idx']

        # Update active trades
        rem_active = []
        for at in active_trades:
            if at['exit_idx'] <= idx:
                net_p = at['net_pnl_usd']
                equity += net_p
                peak_equity = max(peak_equity, equity)
                cur_dd = (peak_equity - equity) / peak_equity * 100.0 if peak_equity > 0 else 0.0
                max_dd_pct = max(max_dd_pct, cur_dd)
                at['equity_after'] = round(equity, 2)
                executed_trades.append(at)

                if net_p < 0:
                    consec_losses += 1
                else:
                    consec_losses = 0
            else:
                rem_active.append(at)
        active_trades = rem_active

        if len(active_trades) >= max_slots:
            continue
        if idx < cooldown_until_idx:
            continue

        # Active Session Filter (Asian Open + London + NY Morning)
        hr = est_hours[idx]
        if 12 <= hr <= 17: # Skip low-probability afternoon chop
            continue

        direction = sig['direction']
        entry_px = closes[idx]
        sl_dist = sl_fixed_pts

        # Sizing
        risk_usd = fixed_risk_usd
        if consec_losses >= 2:
            risk_usd = round(fixed_risk_usd * 0.50, 2)

        qty = round(risk_usd / sl_dist, 4)

        if direction == 'LONG':
            init_sl = round(entry_px - sl_dist, 2)
            cur_sl = init_sl
            be_target = round(entry_px + be_trig_r * sl_dist, 2)
            tp1_target = round(entry_px + tp1_r * sl_dist, 2)
            tp2_target = round(entry_px + tp2_r * sl_dist, 2)
        else:
            init_sl = round(entry_px + sl_dist, 2)
            cur_sl = init_sl
            be_target = round(entry_px - be_trig_r * sl_dist, 2)
            tp1_target = round(entry_px - tp1_r * sl_dist, 2)
            tp2_target = round(entry_px - tp2_r * sl_dist, 2)

        stage = 0
        banked_pts = 0.0
        rem_weight = 1.0
        peak_r = 0.0
        exit_px = None
        exit_idx = None
        exit_reason = None

        end_k = min(n_bars, idx + max_hold_bars + 1)
        for k in range(idx + 1, end_k):
            if direction == 'LONG':
                cur_mfe = (highs[k] - entry_px) / sl_dist
                if cur_mfe > peak_r:
                    peak_r = cur_mfe

                if lows[k] <= cur_sl:
                    exit_px = cur_sl
                    exit_idx = k
                    exit_reason = 'SL' if stage == 0 else ('BE_LOCK' if stage == 1 else 'TRAIL_EXIT')
                    break

                if stage == 0 and highs[k] >= be_target:
                    cur_sl = max(cur_sl, round(entry_px + be_lock_r * sl_dist, 2))
                    stage = 1

                if stage <= 1 and highs[k] >= tp1_target:
                    banked_pts += 0.50 * (tp1_target - entry_px)
                    rem_weight = 0.50
                    cur_sl = max(cur_sl, round(entry_px + 0.45 * sl_dist, 2))
                    stage = 2

                if stage >= 2 and highs[k] >= tp2_target:
                    exit_px = tp2_target
                    exit_idx = k
                    exit_reason = 'TP2_HIT'
                    break
                elif stage == 2 and cur_mfe >= trail_trig_r:
                    trail_px = round(highs[k] - trail_dist_r * sl_dist, 2)
                    if trail_px > cur_sl:
                        cur_sl = trail_px
                        stage = 3
                elif stage == 3:
                    trail_px = round(highs[k] - trail_dist_r * sl_dist, 2)
                    if trail_px > cur_sl:
                        cur_sl = trail_px
            else: # SHORT
                cur_mfe = (entry_px - lows[k]) / sl_dist
                if cur_mfe > peak_r:
                    peak_r = cur_mfe

                if highs[k] >= cur_sl:
                    exit_px = cur_sl
                    exit_idx = k
                    exit_reason = 'SL' if stage == 0 else ('BE_LOCK' if stage == 1 else 'TRAIL_EXIT')
                    break

                if stage == 0 and lows[k] <= be_target:
                    cur_sl = min(cur_sl, round(entry_px - be_lock_r * sl_dist, 2))
                    stage = 1

                if stage <= 1 and lows[k] <= tp1_target:
                    banked_pts += 0.50 * (entry_px - tp1_target)
                    rem_weight = 0.50
                    cur_sl = min(cur_sl, round(entry_px - 0.45 * sl_dist, 2))
                    stage = 2

                if stage >= 2 and lows[k] <= tp2_target:
                    exit_px = tp2_target
                    exit_idx = k
                    exit_reason = 'TP2_HIT'
                    break
                elif stage == 2 and cur_mfe >= trail_trig_r:
                    trail_px = round(lows[k] + trail_dist_r * sl_dist, 2)
                    if trail_px < cur_sl:
                        cur_sl = trail_px
                        stage = 3
                elif stage == 3:
                    trail_px = round(lows[k] + trail_dist_r * sl_dist, 2)
                    if trail_px < cur_sl:
                        cur_sl = trail_px

        if exit_px is None:
            exit_idx = end_k - 1
            exit_px = round(float(closes[exit_idx]), 2)
            exit_reason = f'TIME_{max_hold_bars}M'

        pts = (exit_px - entry_px) if direction == 'LONG' else (entry_px - exit_px)
        tot_pts = round(banked_pts + rem_weight * pts, 2)
        r_mult = round(tot_pts / sl_dist, 2)
        gross_usd = round(tot_pts * qty, 2)
        fees = round(fee_rate * (qty * entry_px + qty * exit_px), 2)
        net_usd = round(gross_usd - fees, 2)

        trade_item = {
            'entry_idx': idx,
            'exit_idx': exit_idx,
            'net_pnl_usd': net_usd,
            'gross_pnl_usd': gross_usd,
            'delta_fee_usd': fees,
            'pnl_pts': tot_pts,
            'r_multiple': r_mult,
            'qty_oz': qty,
            'notional_usd': round(qty * entry_px, 2),
            'entry_price': round(entry_px, 2),
            'exit_price': round(exit_px, 2),
            'sl_price': init_sl,
            'init_risk_pts': sl_dist,
            'direction': direction,
            'setup_agent': sig['agent'],
            'tf': sig['tf'],
            'exit_reason': exit_reason,
            'entry_time': str(pd.to_datetime(times[idx])),
            'exit_time': str(pd.to_datetime(times[exit_idx])),
            'equity_after': 0.0
        }
        active_trades.append(trade_item)
        cooldown_until_idx = idx + cooldown_bars

    for at in active_trades:
        net_p = at['net_pnl_usd']
        equity += net_p
        peak_equity = max(peak_equity, equity)
        cur_dd = (peak_equity - equity) / peak_equity * 100.0 if peak_equity > 0 else 0.0
        max_dd_pct = max(max_dd_pct, cur_dd)
        at['equity_after'] = round(equity, 2)
        executed_trades.append(at)

    wins = [t for t in executed_trades if t['net_pnl_usd'] > 0]
    losses = [t for t in executed_trades if t['net_pnl_usd'] <= 0]
    tot_net = sum(t['net_pnl_usd'] for t in executed_trades)
    wr = len(wins) / len(executed_trades) * 100.0 if executed_trades else 0.0
    gw = sum(t['net_pnl_usd'] for t in wins)
    gl = abs(sum(t['net_pnl_usd'] for t in losses))
    pf = gw / gl if gl > 0 else 99.0
    calmar = (tot_net / 100.0) / (max_dd_pct / 100.0) if max_dd_pct > 0 else 0.0

    return executed_trades, tot_net, wr, pf, max_dd_pct, equity, calmar

# Run variations around the reverse-engineered parameters
print("\n--- Testing Reverse-Engineered DNA Strategy Variations ---")
variations = [
    ("RE-1: Strict 85th% SL ($6.80) | 4.5h Hold", 6.80, 270),
    ("RE-2: Golden Pocket SL ($7.50) | 4.5h Hold", 7.50, 270),
    ("RE-3: Tightened SL ($6.00) | 4.0h Hold", 6.00, 240),
    ("RE-4: Extended Swing SL ($8.00) | 5.0h Hold", 8.00, 300),
    ("RE-5: Balanced SL ($6.50) | 4.5h Hold", 6.50, 270),
]

best_res = None
best_trades = None
best_name = None
best_net = -999

for name, sl, hold in variations:
    tr, net, wr, pf, dd, eq, cal = run_reverse_engineered_backtest(sl_fixed_pts=sl, max_hold_bars=hold)
    print(f"{name:<45} | Trades: {len(tr):<4} | WR: {wr:<5.2f}% | PF: {pf:<4.2f} | Net: ${net:<8.2f} | Max DD: -{dd:<5.2f}% | Calmar: {cal:<5.2f}")
    if net > best_net:
        best_net = net
        best_res = (net, wr, pf, dd, eq, cal)
        best_trades = tr
        best_name = name

# Save Best Reverse-Engineered Trade Journal
re_csv = os.path.join(BASE_DIR, 'data', 'processed', 'trades_REVERSE_ENGINEERED_CHAMPION.csv')
fieldnames = [
    'entry_time', 'exit_time', 'direction', 'setup_agent', 'tf', 'entry_price',
    'exit_price', 'sl_price', 'init_risk_pts', 'pnl_pts', 'r_multiple', 'qty_oz',
    'notional_usd', 'gross_pnl_usd', 'delta_fee_usd', 'net_pnl_usd', 'equity_after', 'exit_reason'
]
with open(re_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for tr in best_trades:
        writer.writerow(tr)

print(f"\n[OUTPUT] Saved Best Reverse-Engineered Journal to {re_csv} ({len(best_trades)} trades)")
