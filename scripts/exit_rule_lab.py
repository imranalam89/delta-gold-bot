import pandas as pd, numpy as np, itertools, sys

FEE = 0.0001

def load(trades_csv, bars_pq):
    tr = pd.read_csv(trades_csv)
    m1 = tr[tr.profile_id == 'MERGE_1_SUPER_CONFLUENCE_OR_15M'].copy().reset_index(drop=True)
    b = pd.read_parquet(bars_pq)
    if 'timestamp' in b.columns: b = b.set_index('timestamp')
    b = b.sort_index()
    ents = []
    for _, t in m1.iterrows():
        ts = pd.to_datetime(t.entry_time.replace(' UTC', ''))
        if ts.tzinfo is None: ts = ts.tz_localize('UTC')
        ents.append(dict(id=t.id, ts=ts, e=b.index.get_indexer([ts], method='nearest')[0],
                         L=t.direction == 'LONG', px=float(t.entry_price), sd=float(t.init_risk_pts),
                         orig_net=float(t.net_pnl_usd)))
    return ents, b.open.to_numpy(), b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy()

def sim_trade(en, O, H, Lo, C, P):
    e, L, px, sd = en['e'], en['L'], en['px'], en['sd']
    qty = 5.0 / sd
    s = 1 if L else -1
    stop = px - s * sd
    peak = 0.0; peak_k = e
    rem = 1.0; exits = []  # (frac, price)
    parts = [dict(p) for p in P.get('partials', [])]
    n = len(C); end = min(n - 1, e + P['max_hold'])
    k = e
    for k in range(e + 1, end + 1):
        # 1. stop (set from prior bars)
        hit = (Lo[k] <= stop) if L else (H[k] >= stop)
        if hit:
            fill = min(stop, O[k]) if L else max(stop, O[k])
            exits.append((rem, fill)); rem = 0; break
        # 2. partial targets
        for p in parts:
            if p.get('done'): continue
            tgt = px + s * p['r'] * sd
            if (H[k] >= tgt) if L else (Lo[k] <= tgt):
                f = min(p['frac'], rem)
                exits.append((f, tgt)); rem -= f; p['done'] = True
                if p.get('stop_r') is not None:
                    ns = px + s * p['stop_r'] * sd
                    stop = max(stop, ns) if L else min(stop, ns)
        if rem <= 1e-9: break
        # 3. update peak, then tighten stop for NEXT bar
        fav = (H[k] - px) if L else (px - Lo[k])
        if fav > peak: peak = fav; peak_k = k
        mr = peak / sd
        cand = []
        st = P.get('stall')
        if st and mr >= st[0] and (k - peak_k) >= st[1]:
            lk = px + s * st[2] * sd
            if (C[k] >= lk) if L else (C[k] <= lk): cand.append(lk)
        be = P.get('be')
        if be and mr >= be[0]: cand.append(px + s * be[1] * sd)
        tm = P.get('trail')
        if tm and mr >= tm[1]:
            if tm[0] == 'pct':      # keep (1-g) of peak
                cand.append(px + s * peak * (1 - tm[2]))
            elif tm[0] == 'r':      # fixed R behind peak
                cand.append(px + s * (peak - tm[2] * sd))
            elif tm[0] == 'struct':  # N-bar swing +/- buffer
                N = tm[2]; a = max(0, k - N + 1)
                cand.append((Lo[a:k + 1].min() - tm[3] * sd) if L else (H[a:k + 1].max() + tm[3] * sd))
        for cs in cand:
            if (cs < C[k] and cs > stop) if L else (cs > C[k] and cs < stop): stop = cs
    if rem > 1e-9:
        exits.append((rem, C[k]))
    pnl = sum(f * s * (x - px) for f, x in exits) * qty
    fee = sum(FEE * qty * f * (px + x) for f, x in exits)
    return pnl - fee, k

def run(ents, O, H, Lo, C, P):
    out = []; last = -1
    for en in ents:
        if en['e'] <= last: continue
        net, k = sim_trade(en, O, H, Lo, C, P)
        out.append((en['ts'], round(net, 2))); last = k
    return out

def stats(res, lo=None, hi=None):
    r = [x for t, x in res if (lo is None or t >= lo) and (hi is None or t < hi)]
    if not r: return None
    a = np.array(r); w = a[a > 0].sum(); l = abs(a[a <= 0].sum())
    eq = 100 + a.cumsum(); dd = ((np.maximum.accumulate(eq) - eq) / np.maximum.accumulate(eq)).max() * 100
    return dict(n=len(a), wr=(a > 0).mean() * 100, net=a.sum(), pf=w / l if l else 9.99, dd=dd)

VARIANTS = {
 'V0 Simplified baseline (stall .54/6->.33, BE 1.05->.45, trail 2.1/.85)':
    dict(max_hold=180, stall=(0.54, 6, 0.33), be=(1.05, 0.45), trail=('r', 2.10, 0.85)),
 'V1 Pct-giveback 50% after 0.8R (no stall)':
    dict(max_hold=240, trail=('pct', 0.8, 0.50)),
 'V2 Pct-giveback 40% after 1.0R + BE .15 @0.7R':
    dict(max_hold=240, be=(0.7, 0.15), trail=('pct', 1.0, 0.40)),
 'V3 Structure trail 20-bar after 1.0R + BE .2 @0.8R':
    dict(max_hold=300, be=(0.8, 0.20), trail=('struct', 1.0, 20, 0.10)),
 'V4 Structure trail 45-bar after 1.5R + BE .2 @0.8R':
    dict(max_hold=360, be=(0.8, 0.20), trail=('struct', 1.5, 45, 0.15)),
 'V5 Scale-out 50% @1.0R, runner pct-giveback 40% after 1.5R':
    dict(max_hold=360, partials=[dict(r=1.0, frac=0.5, stop_r=0.15)], be=(0.7, 0.10), trail=('pct', 1.5, 0.40)),
 'V6 3-tranche 40%@0.6R,30%@1.5R, runner struct 30-bar':
    dict(max_hold=360, partials=[dict(r=0.6, frac=0.4, stop_r=0.05), dict(r=1.5, frac=0.3, stop_r=0.6)],
         trail=('struct', 1.5, 30, 0.10)),
 'V7 Stall kept (.54/6->.33) + runner pct 35% after 1.5R':
    dict(max_hold=360, stall=(0.54, 6, 0.33), be=(1.05, 0.45), trail=('pct', 1.5, 0.35)),
 'V8 Scale 1/3@1.2R + struct 20-bar + pct floor 45%':
    dict(max_hold=360, partials=[dict(r=1.2, frac=0.33, stop_r=0.3)], be=(0.8, 0.15), trail=('struct', 1.2, 20, 0.10)),
}

if __name__ == '__main__':
    sets = {
     '46d (Oct1-Nov15)': load('data/processed/trades_DELTA_GOLD_MERGED_SUPER_CHAMPIONS.csv', 'data/processed/xautusd_delta_oct1_to_now_1m.parquet'),
     '1-YEAR': load('data/processed/trades_DELTA_GOLD_1YEAR_MERGED_SUPER_CHAMPIONS.csv', 'data/processed/xautusd_delta_1year_1m.parquet'),
    }
    split = pd.Timestamp('2026-11-02', tz='UTC')
    for name, (ents, O, H, Lo, C) in sets.items():
        print(f'\n===== {name} | entries {len(ents)} | original-engine net on these entries ${sum(e["orig_net"] for e in ents):.2f} =====')
        print(f'{"variant":78s} {"n":>4s} {"WR%":>6s} {"net$":>8s} {"PF":>5s} {"DD%":>6s}', end='')
        if name.startswith('46d'): print(f' | {"IS net":>8s} {"OOS net":>8s}')
        else: print()
        for vn, P in VARIANTS.items():
            res = run(ents, O, H, Lo, C, P); s = stats(res)
            line = f'{vn:78s} {s["n"]:4d} {s["wr"]:6.1f} {s["net"]:8.2f} {s["pf"]:5.2f} {s["dd"]:6.2f}'
            if name.startswith('46d'):
                a = stats(res, None, split); b = stats(res, split, None)
                line += f' | {a["net"]:8.2f} {b["net"]:8.2f}'
            print(line)
