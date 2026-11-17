import pandas as pd
import numpy as np

# Load MERGE_1 trades
trades_df = pd.read_csv('data/processed/trades_DELTA_GOLD_MERGED_SUPER_CHAMPIONS.csv')
m1_trades = trades_df[trades_df['profile_id'] == 'MERGE_1_SUPER_CONFLUENCE_OR_15M'].copy()

# Load bars
bars = pd.read_parquet('data/processed/xautusd_delta_oct1_to_now_1m.parquet')
if 'timestamp' in bars.columns:
    bars.set_index('timestamp', inplace=True)
elif 'time' in bars.columns:
    bars.set_index('time', inplace=True)
bars.sort_index(inplace=True)

o = bars['open'].to_numpy()
h = bars['high'].to_numpy()
l = bars['low'].to_numpy()
c = bars['close'].to_numpy()
times = bars.index
n = len(bars)

trade_candidates = []
for idx, tr in m1_trades.iterrows():
    ent_time = pd.to_datetime(tr['entry_time'].replace(' UTC', ''))
    if ent_time.tzinfo is None:
        ent_time = ent_time.tz_localize('UTC')
    bar_idx = bars.index.get_indexer([ent_time], method='nearest')[0]
    trade_candidates.append({
        'id': tr['id'],
        'entry_idx': bar_idx,
        'entry_time': str(times[bar_idx]),
        'direction': tr['direction'],
        'entry_price': tr['entry_price'],
        'sl_dist': tr['init_risk_pts'],
        'orig_exit_reason': tr['exit_reason'],
        'orig_net_pnl': tr['net_pnl_usd'],
        'orig_r': tr['r_multiple'],
        'tf': tr['tf'],
        'regime': tr['regime'],
    })

def run_grid_sim(be_trig, be_lock, tr_trig, tr_dist, tr_trig2, tr_dist2):
    sim_trades = []
    last_exit_k = -1
    fee_rate = 0.0001
    
    for cand in trade_candidates:
        if cand['entry_idx'] <= last_exit_k:
            continue
            
        idx = cand['entry_idx']
        entry_px = cand['entry_price']
        sl_dist = cand['sl_dist']
        is_long = cand['direction'] == 'LONG'
        qty_oz = round(5.0 / sl_dist, 4)
        
        init_sl = round(entry_px - sl_dist if is_long else entry_px + sl_dist, 2)
        cur_sl = init_sl
        peak_fav = 0.0
        exit_px = None
        exit_k = None
        exit_reason = None
        stage = 0
        end_k = min(n, idx + 240 + 1)
        
        for k in range(idx + 1, end_k):
            if is_long:
                fav = h[k] - entry_px
                if fav > peak_fav:
                    peak_fav = fav
                cur_mfe_r = peak_fav / sl_dist
                
                if l[k] <= cur_sl:
                    exit_px = cur_sl
                    exit_k = k
                    exit_reason = "SL" if stage == 0 else "TRAIL"
                    break
                    
                if stage == 0 and cur_mfe_r >= be_trig:
                    cur_sl = max(cur_sl, round(entry_px + be_lock * sl_dist, 2))
                    stage = 1
                elif stage >= 1 and cur_mfe_r >= tr_trig and cur_mfe_r < tr_trig2:
                    trail = round(entry_px + (cur_mfe_r - tr_dist) * sl_dist, 2)
                    if trail > cur_sl and trail < c[k]:
                        cur_sl = trail
                        stage = 2
                elif cur_mfe_r >= tr_trig2:
                    trail = round(entry_px + (cur_mfe_r - tr_dist2) * sl_dist, 2)
                    if trail > cur_sl and trail < c[k]:
                        cur_sl = trail
                        stage = 3
            else: # SHORT
                fav = entry_px - l[k]
                if fav > peak_fav:
                    peak_fav = fav
                cur_mfe_r = peak_fav / sl_dist
                
                if h[k] >= cur_sl:
                    exit_px = cur_sl
                    exit_k = k
                    exit_reason = "SL" if stage == 0 else "TRAIL"
                    break
                    
                if stage == 0 and cur_mfe_r >= be_trig:
                    cur_sl = min(cur_sl, round(entry_px - be_lock * sl_dist, 2))
                    stage = 1
                elif stage >= 1 and cur_mfe_r >= tr_trig and cur_mfe_r < tr_trig2:
                    trail = round(entry_px - (cur_mfe_r - tr_dist) * sl_dist, 2)
                    if trail < cur_sl and trail > c[k]:
                        cur_sl = trail
                        stage = 2
                elif cur_mfe_r >= tr_trig2:
                    trail = round(entry_px - (cur_mfe_r - tr_dist2) * sl_dist, 2)
                    if trail < cur_sl and trail > c[k]:
                        cur_sl = trail
                        stage = 3
                        
        if exit_px is None:
            exit_px = float(c[end_k - 1])
            exit_k = end_k - 1
            exit_reason = "TIME"
            
        pnl_pts = (exit_px - entry_px) if is_long else (entry_px - exit_px)
        r_mult = round(pnl_pts / sl_dist, 2)
        gross_pnl = round(pnl_pts * qty_oz, 2)
        fees = round(fee_rate * qty_oz * (entry_px + exit_px), 2)
        net_pnl = round(gross_pnl - fees, 2)
        
        sim_trades.append({'net_pnl': net_pnl, 'r_mult': r_mult, 'id': cand['id']})
        last_exit_k = exit_k
        
    df = pd.DataFrame(sim_trades)
    n_t = len(df)
    if n_t == 0: return None
    wins = (df['net_pnl'] > 0).sum()
    wr = (wins / n_t) * 100.0
    tot_net = df['net_pnl'].sum()
    gw = df[df['net_pnl'] > 0]['net_pnl'].sum()
    gl = abs(df[df['net_pnl'] <= 0]['net_pnl'].sum())
    pf = (gw / gl) if gl > 0 else 9.99
    eq = 100.0 + df['net_pnl'].cumsum()
    dd = ((eq.cummax() - eq) / eq.cummax() * 100.0).max()
    
    t108 = df[df['id'] == 108]
    p108 = t108.iloc[0]['net_pnl'] if len(t108) else 0.0
    
    return {
        'be_trig': be_trig,
        'be_lock': be_lock,
        'tr_trig': tr_trig,
        'tr_dist': tr_dist,
        'tr_trig2': tr_trig2,
        'tr_dist2': tr_dist2,
        'trades': n_t,
        'wr': wr,
        'net_pnl': tot_net,
        'pf': pf,
        'dd': dd,
        'p108': p108
    }

grid_results = []
for be_trig in [0.60, 0.70, 0.80, 0.90]:
    for be_lock in [0.10, 0.15, 0.20]:
        for tr_trig in [1.10, 1.20, 1.40]:
            for tr_dist in [0.55, 0.65, 0.75]:
                for tr_dist2 in [0.45, 0.55]:
                    res = run_grid_sim(be_trig, be_lock, tr_trig, tr_dist, tr_trig2=2.00, tr_dist2=tr_dist2)
                    if res:
                        grid_results.append(res)

df_grid = pd.DataFrame(grid_results)
df_grid.sort_values(by='net_pnl', ascending=False, inplace=True)

print("=== TOP 8 MOST PROFITABLE TRAILING SL CALIBRATIONS ===")
top8 = df_grid.head(8)
print(top8[['be_trig', 'be_lock', 'tr_trig', 'tr_dist', 'tr_dist2', 'trades', 'wr', 'net_pnl', 'pf', 'dd', 'p108']].to_string(index=False))
