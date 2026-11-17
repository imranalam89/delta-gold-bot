import pandas as pd
import numpy as np

# Load the exact executed trades of MERGE_1 to get their exact entry signals
trades_df = pd.read_csv('data/processed/trades_DELTA_GOLD_MERGED_SUPER_CHAMPIONS.csv')
m1_trades = trades_df[trades_df['profile_id'] == 'MERGE_1_SUPER_CONFLUENCE_OR_15M'].copy()
print(f"Loaded {len(m1_trades)} trades from MERGE_1")

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

# Match each trade to its exact entry bar index
trade_candidates = []
for idx, tr in m1_trades.iterrows():
    ent_time = pd.to_datetime(tr['entry_time'].replace(' UTC', ''))
    if ent_time.tzinfo is None:
        ent_time = ent_time.tz_localize('UTC')
    
    # find bar index
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

print(f"Mapped {len(trade_candidates)} trade candidates to 1m bars.")

def simulate_lifecycle(cand, stall_trig_r, stall_bars, stall_lock_r, be_trig_r, be_lock_r, trail_trig_r, trail_dist_r, max_hold=180):
    idx = cand['entry_idx']
    entry_px = cand['entry_price']
    sl_dist = cand['sl_dist']
    is_long = cand['direction'] == 'LONG'
    qty_oz = round(5.0 / sl_dist, 4)
    fee_rate = 0.0001
    
    init_sl = round(entry_px - sl_dist if is_long else entry_px + sl_dist, 2)
    cur_sl = init_sl
    
    peak_fav = 0.0
    peak_k = idx
    exit_px = None
    exit_k = None
    exit_reason = None
    stage = 0 # 0=ARMED, 1=STALL_OR_BREATH, 2=BE, 3=TRAIL
    
    end_k = min(n, idx + max_hold + 1)
    
    for k in range(idx + 1, end_k):
        bars_held = k - idx
        if is_long:
            fav = h[k] - entry_px
            if fav > peak_fav:
                peak_fav = fav
                peak_k = k
            cur_mfe_r = peak_fav / sl_dist
            
            # 1. Stop hit check
            if l[k] <= cur_sl:
                exit_px = cur_sl
                exit_k = k
                if stage == 0:
                    exit_reason = "STOP_LOSS"
                elif stage == 1:
                    exit_reason = "STALL_LOCK"
                elif stage == 2:
                    exit_reason = "BREAKEVEN_LOCK"
                else:
                    exit_reason = "TRAILING_SL_HIT"
                break
                
            # 2. Stall lock (if enabled)
            if stall_trig_r is not None and stage <= 1 and cur_mfe_r >= stall_trig_r:
                if (k - peak_k >= stall_bars):
                    lock_px = round(entry_px + stall_lock_r * sl_dist, 2)
                    if lock_px > cur_sl and c[k] >= lock_px:
                        cur_sl = lock_px
                        stage = max(stage, 1)
                        
            # 3. Breakeven lock
            if be_trig_r is not None and stage <= 1 and cur_mfe_r >= be_trig_r:
                be_px = round(entry_px + be_lock_r * sl_dist, 2)
                if be_px > cur_sl:
                    cur_sl = be_px
                    stage = 2
                    
            # 4. Trailing Stop
            if trail_trig_r is not None and cur_mfe_r >= trail_trig_r:
                stage = 3
                # Trail by trail_dist_r behind peak
                trail_px = round(entry_px + (cur_mfe_r - trail_dist_r) * sl_dist, 2)
                if trail_px > cur_sl and trail_px < c[k]:
                    cur_sl = trail_px
        else: # SHORT
            fav = entry_px - l[k]
            if fav > peak_fav:
                peak_fav = fav
                peak_k = k
            cur_mfe_r = peak_fav / sl_dist
            
            # 1. Stop hit check
            if h[k] >= cur_sl:
                exit_px = cur_sl
                exit_k = k
                if stage == 0:
                    exit_reason = "STOP_LOSS"
                elif stage == 1:
                    exit_reason = "STALL_LOCK"
                elif stage == 2:
                    exit_reason = "BREAKEVEN_LOCK"
                else:
                    exit_reason = "TRAILING_SL_HIT"
                break
                
            # 2. Stall lock (if enabled)
            if stall_trig_r is not None and stage <= 1 and cur_mfe_r >= stall_trig_r:
                if (k - peak_k >= stall_bars):
                    lock_px = round(entry_px - stall_lock_r * sl_dist, 2)
                    if lock_px < cur_sl and c[k] <= lock_px:
                        cur_sl = lock_px
                        stage = max(stage, 1)
                        
            # 3. Breakeven lock
            if be_trig_r is not None and stage <= 1 and cur_mfe_r >= be_trig_r:
                be_px = round(entry_px - be_lock_r * sl_dist, 2)
                if be_px < cur_sl:
                    cur_sl = be_px
                    stage = 2
                    
            # 4. Trailing Stop
            if trail_trig_r is not None and cur_mfe_r >= trail_trig_r:
                stage = 3
                # Trail by trail_dist_r behind peak
                trail_px = round(entry_px - (cur_mfe_r - trail_dist_r) * sl_dist, 2)
                if trail_px < cur_sl and trail_px > c[k]:
                    cur_sl = trail_px

    if exit_px is None:
        exit_px = float(c[end_k - 1])
        exit_k = end_k - 1
        exit_reason = "TIME_EXIT"
        
    pnl_pts = (exit_px - entry_px) if is_long else (entry_px - exit_px)
    r_mult = round(pnl_pts / sl_dist, 2)
    gross_pnl = round(pnl_pts * qty_oz, 2)
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

# Test different Trailing SL Configurations:
configs = {
    "1. Baseline Strict (Tight +0.33R Stall)": {
        "stall_trig_r": 0.54, "stall_bars": 6, "stall_lock_r": 0.33,
        "be_trig_r": 1.05, "be_lock_r": 0.45,
        "trail_trig_r": 2.10, "trail_dist_r": 0.85,
        "max_hold": 180
    },
    "2. Moderate Space (Stall @ +0.80R, 1.10R Trail)": {
        "stall_trig_r": 0.80, "stall_bars": 10, "stall_lock_r": 0.35,
        "be_trig_r": 1.20, "be_lock_r": 0.35,
        "trail_trig_r": 1.60, "trail_dist_r": 1.10,
        "max_hold": 240
    },
    "3. Wide Space (No Premature Stall, 1.25R Trail Floor)": {
        "stall_trig_r": None, "stall_bars": 0, "stall_lock_r": 0,
        "be_trig_r": 1.25, "be_lock_r": 0.25,
        "trail_trig_r": 1.50, "trail_dist_r": 1.25,
        "max_hold": 270
    },
    "4. Deep Breathing Room (BE @ +1.50R, 1.50R Volatility Trail)": {
        "stall_trig_r": None, "stall_bars": 0, "stall_lock_r": 0,
        "be_trig_r": 1.50, "be_lock_r": 0.30,
        "trail_trig_r": 1.80, "trail_dist_r": 1.50,
        "max_hold": 360
    },
    "5. Ultra-Runner (BE @ +1.75R, 1.75R Loose Chandelier)": {
        "stall_trig_r": None, "stall_bars": 0, "stall_lock_r": 0,
        "be_trig_r": 1.75, "be_lock_r": 0.50,
        "trail_trig_r": 2.00, "trail_dist_r": 1.75,
        "max_hold": 420
    },
    "6. Hybrid Stepped Trail (+0.50R Lock @ +1.0R, 0.90R Trail @ +1.8R)": {
        "stall_trig_r": None, "stall_bars": 0, "stall_lock_r": 0,
        "be_trig_r": 1.00, "be_lock_r": 0.50,
        "trail_trig_r": 1.80, "trail_dist_r": 0.90,
        "max_hold": 240
    }
}

print("\n================ TRAILING SL PARAMETER BACKTEST ================")
results_summary = []

for name, cfg in configs.items():
    sim_trades = []
    # enforce non-overlap
    last_exit_k = -1
    for cand in trade_candidates:
        if cand['entry_idx'] <= last_exit_k:
            continue
        res = simulate_lifecycle(cand, **cfg)
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
    
    # drawdown
    eq = 100.0 + df_res['net_pnl'].cumsum()
    peak = eq.cummax()
    dd = (peak - eq) / peak * 100.0
    max_dd = dd.max()
    
    # Check trade #108 specifically
    t108_row = df_res[df_res['id'] == 108]
    t108_info = "N/A"
    if len(t108_row):
        r108 = t108_row.iloc[0]
        t108_info = f"Net: ${r108['net_pnl']:+.2f} ({r108['r_mult']:+.2f}R | {r108['exit_reason']})"
        
    results_summary.append({
        'Config Name': name,
        'Trades': n_t,
        'Win Rate': f"{wr:.2f}%",
        'Net Profit': f"${tot_net:+.2f}",
        'End Equity': f"${100.0 + tot_net:.2f}",
        'PF': f"{pf:.2f}",
        'Max DD': f"-{max_dd:.2f}%",
        'Trade #108 Result': t108_info
    })

res_table = pd.DataFrame(results_summary)
print(res_table.to_string(index=False))
