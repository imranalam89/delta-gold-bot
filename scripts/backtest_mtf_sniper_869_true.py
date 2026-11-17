"""
MTF Low-DD Sniper (Combo 869) - TRUE bar-by-bar backtest.

The original 869 numbers (integrate_mtf_champion.py) derive exits from each candidate's
realised peak_r (hindsight) and rank signals by realised net_pnl. This script keeps the
same ruleset (agents, TFs 5m/15m/1h, 2 slots, 8m cooldown, EST 12-16 blackout, SL sizing,
BE lock, 40% bank at 1.8R, runner trail after 2.8R @0.85R, loss dampener) but resolves
every trade by stepping 1-minute bars. Stop is checked BEFORE favourable moves in each bar
(conservative). No use of future information or realised PnL for selection.

Modes:
  SIGNAL : enter at bundle entry_price, scan bars after entry_ts
  REALISTIC: enter at open of first 1m bar after the signal bar closes (entry_ts + tf),
             with slippage each side
"""
import json, os, sys
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(BASE, "data", "processed")

SNIPER = {'2:MAYA', '8:ELENA', '9:SAM', '11:LIAM', '4:NINA'}
NEG = {'1:ALEX', '3:MARCUS', '6:SOPHIA'}
TF_RANK = {'1h': 4, '15m': 3, '5m': 2, '1m': 1}
TF_MIN = {'1h': 60, '15m': 15, '5m': 5, '1m': 1}

P = dict(max_slots=2, sniper_sl=2.0, struct_mult=1.15, be_trig=1.05, be_lock=0.38,
         bank_at=1.80, bank_frac=0.40, trail_trig=2.80, trail_dist=0.85,
         cooldown_min=8, max_hold_min=480, fee_rate=0.0001, blackout=(12, 13, 14, 15, 16),
         dampen=True, risk=5.0)


def load_bars():
    df = pd.read_parquet(os.path.join(D, "GC_v0_2Year_L2_OrderFlow_Master.parquet"))
    idx = df.index.tz_convert('UTC') if df.index.tz else df.index.tz_localize('UTC')
    ts = (idx.astype('int64') // 10**9).to_numpy()
    return ts, df['open'].to_numpy(float), df['high'].to_numpy(float), df['low'].to_numpy(float), df['close'].to_numpy(float)


def load_signals(bundle_file, tfs):
    b = json.load(open(os.path.join(D, bundle_file), encoding='utf-8'))
    out = []
    for ag, d in b.items():
        if ag in NEG:
            continue
        for tf, v in d['timeframes'].items():
            if tf not in tfs:
                continue
            for t in v.get('trades', []):
                out.append(dict(ag=ag, tf=tf, ts=int(t['entry_ts']), dir=t['direction'],
                                px=float(t['entry_price']), sl=float(t['sl_dist'])))
    out.sort(key=lambda x: (x['ts'], -TF_RANK[x['tf']], x['ag']))
    return out


def simulate(sig, bars, mode, slip, p):
    ts, o, h, l, c = bars
    risk_pts = min(p['sniper_sl'], sig['sl']) if sig['ag'] in SNIPER else min(p['struct_mult'] * sig['sl'] / 1.35, 8.5)
    risk_pts = max(risk_pts, 1.8)
    d = 1 if sig['dir'] == 'LONG' else -1
    if mode == 'SIGNAL':
        i0 = int(np.searchsorted(ts, sig['ts'], side='right'))
        entry = sig['px']
    else:
        t_start = sig['ts'] + TF_MIN[sig['tf']] * 60
        i0 = int(np.searchsorted(ts, t_start, side='left'))
        if i0 >= len(ts):
            return None
        entry = o[i0] + d * slip
    if i0 >= len(ts):
        return None
    stop = entry - d * risk_pts
    r_unit = risk_pts
    banked = False
    be_on = False
    peak = 0.0  # best favourable excursion in R
    realised_r = 0.0
    remain = 1.0
    n = min(len(ts), i0 + p['max_hold_min'])
    exit_i, exit_px, reason = n - 1, c[n - 1], 'TIME'
    for i in range(i0, n):
        # stop first (conservative)
        hit = (l[i] <= stop) if d == 1 else (h[i] >= stop)
        if hit:
            exit_i, exit_px = i, stop
            reason = 'STOP' if not be_on else ('TRAIL' if peak >= p['trail_trig'] else 'BE_LOCK')
            break
        fav = ((h[i] - entry) if d == 1 else (entry - l[i])) / r_unit
        peak = max(peak, fav)
        if not banked and peak >= p['bank_at']:
            banked = True
            realised_r += p['bank_frac'] * p['bank_at']
            remain -= p['bank_frac']
            be_on = True
            stop = entry + d * p['be_lock'] * r_unit if d * (stop - entry) < p['be_lock'] * r_unit else stop
        if not be_on and peak >= p['be_trig']:
            be_on = True
            stop = entry + d * p['be_lock'] * r_unit
        if peak >= p['trail_trig']:
            t_stop = entry + d * (peak - p['trail_dist']) * r_unit
            if d * (t_stop - stop) > 0:
                stop = t_stop
    else:
        pass
    if reason == 'TIME':
        exit_px = c[exit_i]
    exit_px_adj = exit_px - d * (slip if mode != 'SIGNAL' else 0.0)
    rem_r = d * (exit_px_adj - entry) / r_unit
    r_total = realised_r + remain * rem_r
    return dict(i0=i0, entry=entry, exit_i=exit_i, exit_ts=int(ts[exit_i]), entry_ts=int(ts[i0]),
                risk_pts=risk_pts, r=r_total, reason=reason, peak=peak, d=d, exit_px=exit_px_adj)


def run(sigs, bars, mode, slip=0.10, p=P, label=''):
    cooldown_until = 0
    active = []        # (exit_ts, trade)
    done = []
    consec = 0
    equity = 100.0
    for s in sigs:
        t = s['ts']
        # close finished trades
        still = []
        for ex, tr in sorted(active, key=lambda x: x[0]):
            if ex <= t:
                done.append(tr)
                consec = consec + 1 if tr['net'] < 0 else 0
            else:
                still.append((ex, tr))
        active = still
        if len(active) >= p['max_slots'] or t < cooldown_until:
            continue
        est_hr = (pd.Timestamp(t, unit='s', tz='UTC').hour - 5) % 24
        if est_hr in p['blackout']:
            continue
        r = simulate(s, bars, mode, slip, p)
        if r is None:
            continue
        risk_usd = p['risk'] * (0.5 if (p['dampen'] and consec >= 2) else 1.0)
        qty = risk_usd / r['risk_pts']
        gross = r['r'] * r['risk_pts'] * qty
        fees = p['fee_rate'] * qty * (r['entry'] + r['exit_px'])
        r['net'] = gross - fees
        r['fees'] = fees
        r['ag'] = s['ag']; r['tf'] = s['tf']
        active.append((r['exit_ts'], r))
        cooldown_until = t + p['cooldown_min'] * 60
    done.extend(tr for _, tr in active)
    done.sort(key=lambda x: x['exit_ts'])
    return done


def stats(trades, name):
    if not trades:
        print(f"{name}: no trades"); return None
    df = pd.DataFrame(trades)
    pnl = df['net']
    eq = 100 + pnl.cumsum()
    dd = ((eq.cummax() - eq) / eq.cummax() * 100).max()
    pf = pnl[pnl > 0].sum() / max(1e-9, -pnl[pnl < 0].sum())
    print(f"{name:42s} n={len(df):4d} WR={100*(pnl>0).mean():5.1f}% net={pnl.sum():9.2f} PF={pf:5.2f} maxDD={dd:5.1f}% avgR={df['r'].mean():.2f}")
    return df


def main():
    bars = load_bars()
    ts = bars[0]
    res = {}
    for name, bundle, start in [("5-MONTH (Jun-Oct 2026)", "all_11_agents_lab_bundle.json", None),
                                ("2-YEAR (Nov 2024-Oct 2026)", "all_11_agents_2year_bundle.json", None)]:
        sigs = load_signals(bundle, ('5m', '15m', '1h'))
        print("=" * 100)
        print(f"{name}: {len(sigs)} candidate signals")
        for mode, slip in [('SIGNAL', 0.0), ('REALISTIC', 0.10), ('REALISTIC', 0.30)]:
            tr = run(sigs, bars, mode, slip)
            df = stats(tr, f"{mode} slip={slip}")
            res[(name, mode, slip)] = df
    # detail on the realistic 2-year run
    df = res[("2-YEAR (Nov 2024-Oct 2026)", 'REALISTIC', 0.10)]
    if df is not None:
        df['when'] = pd.to_datetime(df['entry_ts'], unit='s', utc=True)
        print("\n--- 2-YEAR REALISTIC (slip 0.10) by half-year ---")
        df['half'] = df['when'].dt.year.astype(str) + 'H' + ((df['when'].dt.month > 6) + 1).astype(str)
        for k, g in df.groupby('half'):
            pnl = g['net']; pf = pnl[pnl > 0].sum() / max(1e-9, -pnl[pnl < 0].sum())
            print(f"{k}  n={len(g):4d} WR={100*(pnl>0).mean():5.1f}% net={pnl.sum():8.2f} PF={pf:4.2f}")
        print("\nby timeframe:"); print(df.groupby('tf')['net'].agg(['count', 'sum']).round(2))
        print("\nby agent:"); print(df.groupby('ag')['net'].agg(['count', 'sum']).round(2))
        print("\nexit reasons:"); print(df['reason'].value_counts())
        out = os.path.join(D, "trades_MTF_869_TRUE_BARBYBAR_2Y.csv")
        df.drop(columns=['when']).to_csv(out, index=False)
        print("saved", out)


if __name__ == "__main__":
    main()
