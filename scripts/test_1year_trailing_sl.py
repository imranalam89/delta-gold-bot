import pandas as pd
import numpy as np

# Load 1-Year MERGE_1 trades
trades_df = pd.read_csv('data/processed/trades_DELTA_GOLD_1YEAR_MERGED_SUPER_CHAMPIONS.csv')
m1_trades = trades_df[trades_df['profile_id'] == 'MERGE_1_SUPER_CONFLUENCE_OR_15M'].copy()
print(f"Loaded {len(m1_trades)} trades from 1-Year MERGE_1")

# Load 1-Year bars
bars = pd.read_parquet('data/processed/xautusd_delta_1year_1m.parquet')
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
    })

def simulate_1y_cfg(be_trig, be_lock, tr_trig, tr_dist, tr_trig2=2.0, tr_dist2=0.45, max_hold=240, stall_trig=None, stall_lock=None):
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
        peak_k = idx
        exit_px = None
        exit_k = None
        stage = 0
        end_k = min(n, idx + max_hold + 1)
        
        for k in range(idx + 1, end_k):
            if is_long:
                fav = h[k] - entry_px
                if fav > peak_fav:
                    peak_fav = fav
                    peak_k = k
                cur_mfe_r = peak_fav / sl_dist
                
                if l[k] <= cur_sl:
                    exit_px = cur_sl
                    exit_k = k
                    break
                    
                if stall_trig and stage == 0 and cur_mfe_r >= stall_trig and (k - peak_k >= 6):
                    cur_sl = max(cur_sl, round(entry_px + stall_lock * sl_dist, 2))
                    stage = 1
                elif stage <= 1 and cur_mfe_r >= be_trig:
                    cur_sl = max(cur_sl, round(entry_px + be_lock * sl_dist, 2))
                    stage = 2
                elif stage >= 2 and cur_mfe_r >= tr_trig and cur_mfe_r < tr_trig2:
                    trail = round(entry_px + (cur_mfe_r - tr_dist) * sl_dist, 2)
                    if trail > cur_sl and trail < c[k]:
                        cur_sl = trail
                        stage = 3
                elif cur_mfe_r >= tr_trig2:
                    trail = round(entry_px + (cur_mfe_r - tr_dist2) * sl_dist, 2)
                    if trail > cur_sl and trail < c[k]:
                        cur_sl = trail
                        stage = 4
            else: # SHORT
                fav = entry_px - l[k]
                if fav > peak_fav:
                    peak_fav = fav
                    peak_k = k
                cur_mfe_r = peak_fav / sl_dist
                
                if h[k] >= cur_sl:
                    exit_px = cur_sl
                    exit_k = k
                    break
                    
                if stall_trig and stage == 0 and cur_mfe_r >= stall_trig and (k - peak_k >= 6):
                    cur_sl = min(cur_sl, round(entry_px - stall_lock * sl_dist, 2))
                    stage = 1
                elif stage <= 1 and cur_mfe_r >= be_trig:
                    cur_sl = min(cur_sl, round(entry_px - be_lock * sl_dist, 2))
                    stage = 2
                elif stage >= 2 and cur_mfe_r >= tr_trig and cur_mfe_r < tr_trig2:
                    trail = round(entry_px - (cur_mfe_r - tr_dist) * sl_dist, 2)
                    if trail < cur_sl and trail > c[k]:
                        cur_sl = trail
                        stage = 3
                elif cur_mfe_r >= tr_trig2:
                    trail = round(entry_px - (cur_mfe_r - tr_dist2) * sl_dist, 2)
                    if trail < cur_sl and trail > c[k]:
                        cur_sl = trail
                        stage = 4
                        
        if exit_px is None:
            exit_px = float(c[end_k - 1])
            exit_k = end_k - 1
            
        pnl_pts = (exit_px - entry_px) if is_long else (entry_px - exit_px)
        r_mult = round(pnl_pts / sl_dist, 2)
        gross_pnl = round(pnl_pts * qty_oz, 2)
        fees = round(fee_rate * qty_oz * (entry_px + exit_px), 2)
        net_pnl = round(gross_pnl - fees, 2)
        
        sim_trades.append({'net_pnl': net_pnl, 'r_mult': r_mult, 'id': cand['id']})
        last_exit_k = exit_k
        
    df = pd.DataFrame(sim_trades)
    n_t = len(df)
    wins = (df['net_pnl'] > 0).sum()
    wr = (wins / n_t) * 100.0 if n_t else 0.0
    tot_net = df['net_pnl'].sum()
    gw = df[df['net_pnl'] > 0]['net_pnl'].sum()
    gl = abs(df[df['net_pnl'] <= 0]['net_pnl'].sum())
    pf = (gw / gl) if gl > 0 else 9.99
    eq = 100.0 + df['net_pnl'].cumsum()
    dd = ((eq.cummax() - eq) / eq.cummax() * 100.0).max()
    
    return {'trades': n_t, 'wr': wr, 'net_pnl': tot_net, 'pf': pf, 'dd': dd}

print("\n=== 1-YEAR (12-MONTH) FULL BACKTEST COMPARISON ===")
c1 = simulate_1y_cfg(be_trig=1.05, be_lock=0.45, tr_trig=2.10, tr_dist=0.85, stall_trig=0.54, stall_lock=0.33)
print(f"1. Baseline Strict (Tight Stall +0.33R): Trades={c1['trades']}, WR={c1['wr']:.2f}%, Net=${c1['net_pnl']:+.2f}, PF={c1['pf']:.2f}, MaxDD=-{c1['dd']:.2f}%")

c2 = simulate_1y_cfg(be_trig=0.80, be_lock=0.20, tr_trig=1.20, tr_dist=0.75, tr_dist2=0.45, stall_trig=None)
print(f"2. Progressive Breathing Room (BE @ 0.8R, 0.75R Space): Trades={c2['trades']}, WR={c2['wr']:.2f}%, Net=${c2['net_pnl']:+.2f}, PF={c2['pf']:.2f}, MaxDD=-{c2['dd']:.2f}%")

c3 = simulate_1y_cfg(be_trig=1.50, be_lock=0.30, tr_trig=1.80, tr_dist=1.50, stall_trig=None)
print(f"3. Deep Space / Ultra Loose (1.50R Trail): Trades={c3['trades']}, WR={c3['wr']:.2f}%, Net=${c3['net_pnl']:+.2f}, PF={c3['pf']:.2f}, MaxDD=-{c3['dd']:.2f}%")
