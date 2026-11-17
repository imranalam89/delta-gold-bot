import pandas as pd, numpy as np

tr = pd.read_csv('data/processed/trades_DELTA_GOLD_MERGED_SUPER_CHAMPIONS.csv')
m1 = tr[tr.profile_id == 'MERGE_1_SUPER_CONFLUENCE_OR_15M'].copy().reset_index(drop=True)
bars = pd.read_parquet('data/processed/xautusd_delta_oct1_to_now_1m.parquet')
if 'timestamp' in bars.columns: bars = bars.set_index('timestamp')
bars = bars.sort_index()
h = bars.high.to_numpy(); l = bars.low.to_numpy(); c = bars.close.to_numpy()

def ix(s):
    t = pd.to_datetime(s.replace(' UTC', ''))
    if t.tzinfo is None: t = t.tz_localize('UTC')
    return bars.index.get_indexer([t], method='nearest')[0]

rows = []
for _, t in m1.iterrows():
    e, x = ix(t.entry_time), ix(t.exit_time)
    sd = t.init_risk_pts; L = t.direction == 'LONG'
    # post-exit continuation in the trade's favour, next 180 bars
    end = min(len(c), x + 181)
    if L:
        post = (h[x+1:end].max() - t.entry_price) / sd if end > x+1 else 0
        post_adv = (t.entry_price - l[x+1:end].min()) / sd if end > x+1 else 0
    else:
        post = (t.entry_price - l[x+1:end].min()) / sd if end > x+1 else 0
        post_adv = (h[x+1:end].max() - t.entry_price) / sd if end > x+1 else 0
    rows.append(dict(id=t.id, dir=t.direction, reason=t.exit_reason, tf=t.tf, regime=t.regime,
                     hold=t.hold_mins, r=t.r_multiple, mfe=t.mfe_r, mae=t.mae_r,
                     post_mfe_180=round(post, 2), post_adv_180=round(post_adv, 2),
                     net=t.net_pnl_usd))
d = pd.DataFrame(rows)
d['left'] = (d.mfe - d.r).clip(lower=0)
d['capture'] = np.where(d.mfe > 0.05, d.r / d.mfe, np.nan)

print('=== OVERALL ===')
print(f"trades {len(d)} | net ${d.net.sum():.2f} | avg R {d.r.mean():.2f} | avg MFE {d.mfe.mean():.2f} | avg left-on-table {d.left.mean():.2f}R")
print(f"median capture ratio (r/mfe) {d.capture.median():.2f}")
print('\n=== BY EXIT REASON ===')
g = d.groupby('reason').agg(n=('id', 'count'), avg_r=('r', 'mean'), avg_mfe=('mfe', 'mean'),
                            avg_left=('left', 'mean'), post_mfe=('post_mfe_180', 'mean'),
                            net=('net', 'sum'), hold=('hold', 'mean')).round(2)
print(g.sort_values('net', ascending=False).to_string())

print('\n=== EARLY EXITS THAT LATER RAN (post-exit MFE >= 1.5R within 180m) ===')
big = d[(d.post_mfe_180 >= 1.5) & (d.r < 1.0)]
print(f"{len(big)} trades; they banked {big.r.sum():.2f}R total but price went avg {big.post_mfe_180.mean():.2f}R in favour afterwards")
print(big[['id', 'dir', 'reason', 'r', 'mfe', 'post_mfe_180', 'hold']].to_string(index=False))

print('\n=== MFE BUCKETS: how much of the run is kept ===')
d['b'] = pd.cut(d.mfe, [-1, 0.5, 1.0, 2.0, 3.0, 10])
print(d.groupby('b', observed=True).agg(n=('id', 'count'), avg_r=('r', 'mean'), avg_mfe=('mfe', 'mean'),
                                       cap=('capture', 'median')).round(2).to_string())

print('\n=== SESSION / DIRECTION / TF ===')
for k in ['regime', 'tf', 'dir']:
    print(d.groupby(k).agg(n=('id', 'count'), avg_r=('r', 'mean'), avg_mfe=('mfe', 'mean'), net=('net', 'sum')).round(2).to_string())
d.to_csv('data/processed/exit_audit_108.csv', index=False)
