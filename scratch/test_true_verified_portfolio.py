import json
import os
import sys
import numpy as np
import pandas as pd

print("[ENGINE] Loading Master CME Globex Parquet dataset...")
df = pd.read_parquet('data/processed/GC_v0_2Year_L2_OrderFlow_Master.parquet')
if not df.index.tz:
    df.index = df.index.tz_localize('UTC')
else:
    df.index = df.index.tz_convert('UTC')

start_dt = pd.to_datetime('2026-05-28 22:00:00', utc=True)
df_5m = df.loc[start_dt:].copy()

with open('data/processed/all_11_agents_lab_bundle.json', 'r', encoding='utf-8') as f:
    bundle = json.load(f)

# Collect all trades from the bundle
all_trades = []
for ag, data in bundle.items():
    tf_data = data.get('timeframes', {})
    for tf_label in ['1m', '5m', '15m', '1h']:
        trades = tf_data.get(tf_label, {}).get('trades', [])
        for t in trades:
            t_copy = dict(t)
            t_copy['source_agent'] = ag
            t_copy['tf'] = tf_label
            t_copy['tf_rank'] = {'1h': 4, '15m': 3, '5m': 2, '1m': 1}[tf_label]
            all_trades.append(t_copy)

print(f"Total candidate trades in bundle: {len(all_trades)}")

# Sort by entry timestamp, then TF priority
all_trades.sort(key=lambda x: (x['entry_ts'], -x['tf_rank'], -x.get('net_pnl', 0)))

# Test what happens when we use each trade's exact bar-by-bar verified outcome
# but filter by agent edge and apply slot management!
ELITE_AGENTS = {'8:ELENA', '7:DEREK', '2:MAYA', '4:NINA', '10:OMAR', '5:MAX', '11:LIAM', '9:SAM'}

def run_portfolio_verified(allowed_agents=ELITE_AGENTS, allowed_tfs=('1m', '5m', '15m', '1h'), max_slots=2, cooldown_secs=480, use_dampener=True):
    equity = 100.0
    peak_equity = 100.0
    max_dd_pct = 0.0
    active = []
    executed = []
    cooldown_ts = 0
    consec_losses = 0

    for t in all_trades:
        if t['source_agent'] not in allowed_agents:
            continue
        if t['tf'] not in allowed_tfs:
            continue
        ts = t['entry_ts']

        # Update active trades
        rem = []
        for at in active:
            if at['exit_ts'] <= ts:
                net_p = at['net_pnl']
                equity += net_p
                peak_equity = max(peak_equity, equity)
                cur_dd = (peak_equity - equity) / peak_equity * 100.0
                max_dd_pct = max(max_dd_pct, cur_dd)
                at['equity_after'] = round(equity, 2)
                executed.append(at)

                if net_p < 0:
                    consec_losses += 1
                else:
                    consec_losses = 0
            else:
                rem.append(at)
        active = rem

        if len(active) >= max_slots:
            continue
        if ts < cooldown_ts:
            continue

        # Skip midday churn
        dt_ent = pd.to_datetime(t['entry_time'], utc=True)
        est_hr = (dt_ent.hour - 5) % 24
        if 12 <= est_hr <= 16:
            continue

        # Calculate exact trade with its verified R-multiple from the bar-by-bar engine
        orig_rk = float(t['sl_dist'])
        orig_r_mult = float(t['r_multiple'])
        orig_net = float(t['net_pnl'])
        orig_entry_px = float(t['entry_price'])
        orig_exit_px = float(t['exit_price'])

        # Risk sizing
        risk_usd = 5.0
        if use_dampener and consec_losses >= 2:
            risk_usd = 2.50

        qty = round(risk_usd / orig_rk, 4)
        gross_usd = round(orig_r_mult * risk_usd, 2)
        fees = round(0.0001 * (qty * orig_entry_px + qty * orig_exit_px), 2)
        net_usd = round(gross_usd - fees, 2)

        t_exec = dict(t)
        t_exec['qty'] = qty
        t_exec['gross_pnl'] = gross_usd
        t_exec['fee_usd'] = fees
        t_exec['net_pnl'] = net_usd
        active.append(t_exec)
        cooldown_ts = ts + cooldown_secs

    for at in active:
        net_p = at['net_pnl']
        equity += net_p
        peak_equity = max(peak_equity, equity)
        cur_dd = (peak_equity - equity) / peak_equity * 100.0
        max_dd_pct = max(max_dd_pct, cur_dd)
        at['equity_after'] = round(equity, 2)
        executed.append(at)

    wins = [x for x in executed if x['net_pnl'] > 0]
    losses = [x for x in executed if x['net_pnl'] <= 0]
    tot_net = sum(x['net_pnl'] for x in executed)
    wr = len(wins) / len(executed) * 100.0 if executed else 0.0
    gw = sum(x['net_pnl'] for x in wins)
    gl = abs(sum(x['net_pnl'] for x in losses))
    pf = gw / gl if gl > 0 else 99.0

    return executed, tot_net, wr, pf, max_dd_pct, equity

print("\n--- Testing True Bar-By-Bar Replay Across Configurations ---")
configs = [
    ("Elite Specialists (All 4 TFs: 1m+5m+15m+1h)", ELITE_AGENTS, ('1m', '5m', '15m', '1h'), 2),
    ("Elite Specialists (Higher TFs: 5m+15m+1h)", ELITE_AGENTS, ('5m', '15m', '1h'), 2),
    ("All 11 Specialists (All 4 TFs: 1m+5m+15m+1h)", set(bundle.keys()), ('1m', '5m', '15m', '1h'), 2),
    ("Elite Specialists (1m only)", ELITE_AGENTS, ('1m',), 2),
]

for name, ags, tfs, slots in configs:
    ex, net, wr, pf, dd, eq = run_portfolio_verified(ags, tfs, slots)
    print(f"{name:<45} | Trades: {len(ex):<4} | WR: {wr:<5.2f}% | PF: {pf:<4.2f} | Net: ${net:<8.2f} | Max DD: -{dd:<5.2f}% | End Eq: ${eq:<8.2f}")
