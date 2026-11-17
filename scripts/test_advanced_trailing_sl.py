import pandas as pd
import numpy as np

# Load the exact executed trades of MERGE_1 to get their exact entry signals
trades_df = pd.read_csv('data/processed/trades_DELTA_GOLD_MERGED_SUPER_CHAMPIONS.csv')
m1_trades = trades_df[trades_df['profile_id'] == 'MERGE_1_SUPER_CONFLUENCE_OR_15M'].copy()

# Load 1m bars
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

def simulate_advanced_variant(cand, mode="baseline"):
    idx = cand['entry_idx']
    entry_px = cand['entry_price']
    sl_dist = cand['sl_dist']
    is_long = cand['direction'] == 'LONG'
    qty_oz = round(5.0 / sl_dist, 4)
    fee_rate = 0.0001
    regime = cand['regime']
    
    init_sl = round(entry_px - sl_dist if is_long else entry_px + sl_dist, 2)
    cur_sl = init_sl
    
    peak_fav = 0.0
    peak_k = idx
    exit_px = None
    exit_k = None
    exit_reason = None
    stage = 0
    max_hold = 240
    end_k = min(n, idx + max_hold + 1)
    
    banked_pts = 0.0
    rem_qty_frac = 1.0 # 100% position
    
    for k in range(idx + 1, end_k):
        bars_held = k - idx
        if is_long:
            fav = h[k] - entry_px
            if fav > peak_fav:
                peak_fav = fav
                peak_k = k
            cur_mfe_r = peak_fav / sl_dist
            
            # Check SL hit
            if l[k] <= cur_sl:
                exit_px = cur_sl
                exit_k = k
                exit_reason = "STOP_LOSS" if stage == 0 else "TRAILING_OR_BE"
                break
                
            if mode == "baseline":
                if stage == 0 and cur_mfe_r >= 0.54 and (k - peak_k >= 6):
                    lock = round(entry_px + 0.33 * sl_dist, 2)
                    if lock > cur_sl and c[k] >= lock:
                        cur_sl = lock
                        stage = 1
                elif stage <= 1 and cur_mfe_r >= 1.05:
                    cur_sl = max(cur_sl, round(entry_px + 0.45 * sl_dist, 2))
                    stage = 2
                elif cur_mfe_r >= 2.10:
                    stage = 3
                    trail = round(entry_px + (cur_mfe_r - 0.85) * sl_dist, 2)
                    if trail > cur_sl and trail < c[k]:
                        cur_sl = trail
                        
            elif mode == "dual_tranche_50_50":
                # Bank 50% at +0.40R (free trade!), then let remaining 50% run with wide 1.25R trail
                if stage == 0 and cur_mfe_r >= 0.45 and rem_qty_frac == 1.0:
                    tp_half = round(entry_px + 0.40 * sl_dist, 2)
                    banked_pts += 0.50 * 0.40 * sl_dist
                    rem_qty_frac = 0.50
                    cur_sl = round(entry_px + 0.10 * sl_dist, 2) # move rest to breakeven + fee
                    stage = 1
                elif stage >= 1 and cur_mfe_r >= 1.20:
                    # Wide trailing stop for the runner half
                    trail = round(entry_px + (cur_mfe_r - 0.80) * sl_dist, 2)
                    if trail > cur_sl and trail < c[k]:
                        cur_sl = trail
                        stage = 2

            elif mode == "regime_adaptive":
                # In TRENDING: give wide space (1.20R trail, no tight stall lock)
                # In SIDEWAYS: tight stall lock (bank +0.33R fast before reversal)
                if regime == "TRENDING":
                    if stage == 0 and cur_mfe_r >= 1.10:
                        cur_sl = max(cur_sl, round(entry_px + 0.30 * sl_dist, 2))
                        stage = 1
                    elif cur_mfe_r >= 1.60:
                        stage = 2
                        trail = round(entry_px + (cur_mfe_r - 0.95) * sl_dist, 2)
                        if trail > cur_sl and trail < c[k]:
                            cur_sl = trail
                else: # SIDEWAYS
                    if stage == 0 and cur_mfe_r >= 0.54 and (k - peak_k >= 6):
                        lock = round(entry_px + 0.33 * sl_dist, 2)
                        if lock > cur_sl and c[k] >= lock:
                            cur_sl = lock
                            stage = 1
                    elif stage <= 1 and cur_mfe_r >= 1.05:
                        cur_sl = max(cur_sl, round(entry_px + 0.45 * sl_dist, 2))
                        stage = 2

            elif mode == "progressive_milestone":
                # Milestone 1: at +0.70R -> move SL to Breakeven (+0.15R)
                # Milestone 2: at +1.20R -> trail by 0.60R
                # Milestone 3: at +2.00R -> trail by 0.50R
                if stage == 0 and cur_mfe_r >= 0.70:
                    cur_sl = max(cur_sl, round(entry_px + 0.15 * sl_dist, 2))
                    stage = 1
                elif stage >= 1 and cur_mfe_r >= 1.20 and cur_mfe_r < 2.00:
                    trail = round(entry_px + (cur_mfe_r - 0.60) * sl_dist, 2)
                    if trail > cur_sl and trail < c[k]:
                        cur_sl = trail
                        stage = 2
                elif cur_mfe_r >= 2.00:
                    trail = round(entry_px + (cur_mfe_r - 0.50) * sl_dist, 2)
                    if trail > cur_sl and trail < c[k]:
                        cur_sl = trail
                        stage = 3

        else: # SHORT
            fav = entry_px - l[k]
            if fav > peak_fav:
                peak_fav = fav
                peak_k = k
            cur_mfe_r = peak_fav / sl_dist
            
            if h[k] >= cur_sl:
                exit_px = cur_sl
                exit_k = k
                exit_reason = "STOP_LOSS" if stage == 0 else "TRAILING_OR_BE"
                break
                
            if mode == "baseline":
                if stage == 0 and cur_mfe_r >= 0.54 and (k - peak_k >= 6):
                    lock = round(entry_px - 0.33 * sl_dist, 2)
                    if lock < cur_sl and c[k] <= lock:
                        cur_sl = lock
                        stage = 1
                elif stage <= 1 and cur_mfe_r >= 1.05:
                    cur_sl = min(cur_sl, round(entry_px - 0.45 * sl_dist, 2))
                    stage = 2
                elif cur_mfe_r >= 2.10:
                    stage = 3
                    trail = round(entry_px - (cur_mfe_r - 0.85) * sl_dist, 2)
                    if trail < cur_sl and trail > c[k]:
                        cur_sl = trail
                        
            elif mode == "dual_tranche_50_50":
                if stage == 0 and cur_mfe_r >= 0.45 and rem_qty_frac == 1.0:
                    tp_half = round(entry_px - 0.40 * sl_dist, 2)
                    banked_pts += 0.50 * 0.40 * sl_dist
                    rem_qty_frac = 0.50
                    cur_sl = round(entry_px - 0.10 * sl_dist, 2)
                    stage = 1
                elif stage >= 1 and cur_mfe_r >= 1.20:
                    trail = round(entry_px - (cur_mfe_r - 0.80) * sl_dist, 2)
                    if trail < cur_sl and trail > c[k]:
                        cur_sl = trail
                        stage = 2

            elif mode == "regime_adaptive":
                if regime == "TRENDING":
                    if stage == 0 and cur_mfe_r >= 1.10:
                        cur_sl = min(cur_sl, round(entry_px - 0.30 * sl_dist, 2))
                        stage = 1
                    elif cur_mfe_r >= 1.60:
                        stage = 2
                        trail = round(entry_px - (cur_mfe_r - 0.95) * sl_dist, 2)
                        if trail < cur_sl and trail > c[k]:
                            cur_sl = trail
                else: # SIDEWAYS
                    if stage == 0 and cur_mfe_r >= 0.54 and (k - peak_k >= 6):
                        lock = round(entry_px - 0.33 * sl_dist, 2)
                        if lock < cur_sl and c[k] <= lock:
                            cur_sl = lock
                            stage = 1
                    elif stage <= 1 and cur_mfe_r >= 1.05:
                        cur_sl = min(cur_sl, round(entry_px - 0.45 * sl_dist, 2))
                        stage = 2

            elif mode == "progressive_milestone":
                if stage == 0 and cur_mfe_r >= 0.70:
                    cur_sl = min(cur_sl, round(entry_px - 0.15 * sl_dist, 2))
                    stage = 1
                elif stage >= 1 and cur_mfe_r >= 1.20 and cur_mfe_r < 2.00:
                    trail = round(entry_px - (cur_mfe_r - 0.60) * sl_dist, 2)
                    if trail < cur_sl and trail > c[k]:
                        cur_sl = trail
                        stage = 2
                elif cur_mfe_r >= 2.00:
                    trail = round(entry_px - (cur_mfe_r - 0.50) * sl_dist, 2)
                    if trail < cur_sl and trail > c[k]:
                        cur_sl = trail
                        stage = 3

    if exit_px is None:
        exit_px = float(c[end_k - 1])
        exit_k = end_k - 1
        exit_reason = "TIME_EXIT"
        
    pnl_pts = (exit_px - entry_px) if is_long else (entry_px - exit_px)
    total_pts = banked_pts + rem_qty_frac * pnl_pts
    r_mult = round(total_pts / sl_dist, 2)
    gross_pnl = round(total_pts * qty_oz, 2)
    fees = round(fee_rate * qty_oz * (entry_px + exit_px), 2)
    net_pnl = round(gross_pnl - fees, 2)
    
    return {
        'id': cand['id'],
        'exit_px': exit_px,
        'exit_k': exit_k,
        'exit_time': str(times[exit_k]),
        'r_mult': r_mult,
        'net_pnl': net_pnl,
        'exit_reason': exit_reason,
        'mfe_r': round(peak_fav / sl_dist, 2)
    }

modes = {
    "1. Baseline Strict (+0.33R Stall Lock)": "baseline",
    "2. Dual-Tranche 50/50 (Lock 50% @ +0.4R, 50% Runner 0.8R Trail)": "dual_tranche_50_50",
    "3. Regime-Adaptive (Wide Trail in Trending, Tight Lock in Sideways)": "regime_adaptive",
    "4. Progressive Milestone (BE @ +0.7R, Dynamic Trail)": "progressive_milestone"
}

summary = []
for name, m_key in modes.items():
    sim_trades = []
    last_exit_k = -1
    for cand in trade_candidates:
        if cand['entry_idx'] <= last_exit_k:
            continue
        res = simulate_advanced_variant(cand, mode=m_key)
        sim_trades.append(res)
        last_exit_k = res['exit_k']
        
    df_res = pd.DataFrame(sim_trades)
    n_t = len(df_res)
    wins = (df_res['net_pnl'] > 0).sum()
    wr = (wins / n_t) * 100.0 if n_t else 0.0
    tot_net = df_res['net_pnl'].sum()
    gw = df_res[df_res['net_pnl'] > 0]['net_pnl'].sum()
    gl = abs(df_res[df_res['net_pnl'] <= 0]['net_pnl'].sum())
    pf = (gw / gl) if gl > 0 else 9.99
    
    eq = 100.0 + df_res['net_pnl'].cumsum()
    peak = eq.cummax()
    dd = (peak - eq) / peak * 100.0
    max_dd = dd.max()
    
    t108_row = df_res[df_res['id'] == 108]
    t108_info = "N/A"
    if len(t108_row):
        r108 = t108_row.iloc[0]
        t108_info = f"Net: ${r108['net_pnl']:+.2f} ({r108['r_mult']:+.2f}R)"
        
    summary.append({
        'Strategy Mode': name,
        'Trades': n_t,
        'Win Rate': f"{wr:.2f}%",
        'Net Profit': f"${tot_net:+.2f}",
        'PF': f"{pf:.2f}",
        'Max DD': f"-{max_dd:.2f}%",
        'Trade #108': t108_info
    })

print("\n" + pd.DataFrame(summary).to_string(index=False))
