import pandas as pd
import numpy as np

def sim_with_custom_hold(bars, entry_idx, direction, entry_px, sl_dist, max_hold=None):
    # bars: numpy arrays O, H, L, C
    O, H, Lo, C = bars['open'], bars['high'], bars['low'], bars['close']
    n = len(C)
    is_long = direction == 'LONG'
    
    init_sl = round(entry_px - sl_dist if is_long else entry_px + sl_dist, 2)
    cur_sl = init_sl
    stage = 0
    stall_locked = False
    peak_fav = 0.0
    peak_k = entry_idx
    worst_adv = 0.0
    exit_px = None
    exit_k = None
    exit_reason = None
    
    end_k = min(n, entry_idx + max_hold + 1) if max_hold else n
    
    for k in range(entry_idx + 1, end_k):
        bars_held = k - entry_idx
        if is_long:
            fav = H[k] - entry_px
            adv = entry_px - Lo[k]
            if fav > peak_fav:
                peak_fav = fav
                peak_k = k
            if adv > worst_adv:
                worst_adv = adv
            cur_mfe_r = peak_fav / sl_dist
            cur_close_r = (C[k] - entry_px) / sl_dist

            # SL check
            if Lo[k] <= cur_sl:
                exit_px = cur_sl
                exit_k = k
                if stage == 0: exit_reason = "STOP_LOSS"
                elif stall_locked: exit_reason = "SMART_STALL_LOCK"
                elif stage in (1, 4): exit_reason = "CONTINUOUS_40R_SL_TRAIL"
                elif stage == 2: exit_reason = "BREAKEVEN"
                else: exit_reason = "UNCAPPED_RUNNER_TRAIL"
                break

            # Smart Stall Lock / Breathing Trail
            if stage <= 1 and cur_mfe_r >= 0.54:
                if (k - peak_k >= 6) and (C[k] >= entry_px + 0.33 * sl_dist):
                    lock_px = round(entry_px + 0.33 * sl_dist, 2)
                    if C[k] >= lock_px and lock_px > cur_sl:
                        cur_sl = lock_px
                        stage = max(stage, 1)
                        stall_locked = True

            # Breakeven Lock (+1.05R -> +0.45R lock)
            if stage <= 1 and cur_mfe_r >= 1.05:
                be_lock_px = round(entry_px + 0.45 * sl_dist, 2)
                if be_lock_px > cur_sl: cur_sl = be_lock_px
                stage = 2
                stall_locked = False

            # Runner transition at TP1 (+1.80R) -> lock +0.85R
            if stage <= 2 and cur_mfe_r >= 1.80:
                run_lock = round(entry_px + 0.85 * sl_dist, 2)
                if run_lock > cur_sl: cur_sl = run_lock
                stage = 3
                stall_locked = False

            # Continuous 40R Chandelier Trail (+2.10R trigger)
            if cur_mfe_r >= 2.10:
                stage = 4
                stall_locked = False
                swing_15m_low = float(np.min(Lo[max(0, k - 45) : k + 1]))
                atr_floor = float(entry_px + (cur_mfe_r - 0.85) * sl_dist)
                cand_sl = round(max(swing_15m_low - 0.35 * sl_dist, atr_floor), 2)
                if cand_sl > cur_sl and cand_sl < C[k]:
                    cur_sl = cand_sl
        else: # SHORT
            fav = entry_px - Lo[k]
            adv = H[k] - entry_px
            if fav > peak_fav:
                peak_fav = fav
                peak_k = k
            if adv > worst_adv:
                worst_adv = adv
            cur_mfe_r = peak_fav / sl_dist
            cur_close_r = (entry_px - C[k]) / sl_dist

            # SL check
            if H[k] >= cur_sl:
                exit_px = cur_sl
                exit_k = k
                if stage == 0: exit_reason = "STOP_LOSS"
                elif stall_locked: exit_reason = "SMART_STALL_LOCK"
                elif stage in (1, 4): exit_reason = "CONTINUOUS_40R_SL_TRAIL"
                elif stage == 2: exit_reason = "BREAKEVEN"
                else: exit_reason = "UNCAPPED_RUNNER_TRAIL"
                break

            # Smart Stall Lock
            if stage <= 1 and cur_mfe_r >= 0.54:
                if (k - peak_k >= 6) and (C[k] <= entry_px - 0.33 * sl_dist):
                    lock_px = round(entry_px - 0.33 * sl_dist, 2)
                    if C[k] <= lock_px and lock_px < cur_sl:
                        cur_sl = lock_px
                        stage = max(stage, 1)
                        stall_locked = True

            # Breakeven Lock
            if stage <= 1 and cur_mfe_r >= 1.05:
                be_lock_px = round(entry_px - 0.45 * sl_dist, 2)
                if be_lock_px < cur_sl: cur_sl = be_lock_px
                stage = 2
                stall_locked = False

            # Runner transition
            if stage <= 2 and cur_mfe_r >= 1.80:
                run_lock = round(entry_px - 0.85 * sl_dist, 2)
                if run_lock < cur_sl: cur_sl = run_lock
                stage = 3
                stall_locked = False

            # Continuous 40R Chandelier Trail
            if cur_mfe_r >= 2.10:
                stage = 4
                stall_locked = False
                swing_15m_high = float(np.max(H[max(0, k - 45) : k + 1]))
                atr_ceil = float(entry_px - (cur_mfe_r - 0.85) * sl_dist)
                cand_sl = round(min(swing_15m_high + 0.35 * sl_dist, atr_ceil), 2)
                if cand_sl < cur_sl and cand_sl > C[k]:
                    cur_sl = cand_sl

    if exit_px is None:
        exit_k = end_k - 1
        exit_px = round(float(C[exit_k]), 2)
        exit_reason = f"TIME_{max_hold}M" if max_hold else "END_OF_DATA"

    pts = round((exit_px - entry_px) if is_long else (entry_px - exit_px), 2)
    r_mult = round(pts / sl_dist, 2)
    qty = 5.0 / sl_dist
    gross = round(pts * qty, 2)
    fee = round(0.0001 * qty * (entry_px + exit_px), 2)
    net = round(gross - fee, 2)
    
    return {
        'exit_px': exit_px,
        'exit_k': exit_k,
        'hold_mins': exit_k - entry_idx,
        'exit_reason': exit_reason,
        'pts': pts,
        'r_mult': r_mult,
        'net': net
    }

def main():
    df_bars = pd.read_parquet('data/processed/xautusd_delta_oct1_to_now_1m.parquet')
    if 'timestamp' in df_bars.columns:
        df_bars = df_bars.set_index('timestamp')
    df_bars = df_bars.sort_index()
    
    bars = {
        'open': df_bars['open'].to_numpy(),
        'high': df_bars['high'].to_numpy(),
        'low': df_bars['low'].to_numpy(),
        'close': df_bars['close'].to_numpy()
    }
    
    trades = pd.read_csv('data/processed/trades_DELTA_GOLD_MERGED_SUPER_CHAMPIONS.csv')
    m1 = trades[trades['profile_id'] == 'MERGE_1_SUPER_CONFLUENCE_OR_15M'].copy().reset_index(drop=True)
    
    results_base = []
    results_no_time = []
    
    for idx, t in m1.iterrows():
        ts = pd.to_datetime(t['entry_time'].replace(' UTC', ''))
        if ts.tzinfo is None: ts = ts.tz_localize('UTC')
        e_idx = df_bars.index.get_indexer([ts], method='nearest')[0]
        
        # Original (with time exit 180m / 270m)
        mh = 270 if t['tf'] in ('15m', '1h') else 180
        res_b = sim_with_custom_hold(bars, e_idx, t['direction'], float(t['entry_price']), float(t['init_risk_pts']), max_hold=mh)
        results_base.append(res_b)
        
        # No time exit (indefinite hold)
        res_no = sim_with_custom_hold(bars, e_idx, t['direction'], float(t['entry_price']), float(t['init_risk_pts']), max_hold=None)
        results_no_time.append(res_no)
        
    df_comp = pd.DataFrame({
        'id': m1['id'],
        'orig_reason': m1['exit_reason'],
        'orig_net': m1['net_pnl_usd'],
        'orig_hold': m1['hold_mins'],
        'no_time_reason': [r['exit_reason'] for r in results_no_time],
        'no_time_net': [r['net'] for r in results_no_time],
        'no_time_hold': [r['hold_mins'] for r in results_no_time],
        'diff_net': [round(r['net'] - t['net_pnl_usd'], 2) for r, (_, t) in zip(results_no_time, m1.iterrows())]
    })
    
    print("=== SUMMARY COMPARISON ACROSS ALL 108 TRADES ===")
    print(f"Original Engine Total Net: ${m1['net_pnl_usd'].sum():.2f}")
    print(f"NO Time Cycle Exit Total Net: ${df_comp['no_time_net'].sum():.2f}")
    print(f"Net Difference: ${df_comp['no_time_net'].sum() - m1['net_pnl_usd'].sum():.2f}")
    
    orig_wins = (m1['net_pnl_usd'] > 0).sum()
    no_time_wins = (df_comp['no_time_net'] > 0).sum()
    print(f"Original Win Rate: {orig_wins}/108 ({orig_wins/108*100:.1f}%)")
    print(f"NO Time Exit Win Rate: {no_time_wins}/108 ({no_time_wins/108*100:.1f}%)")
    
    # Breakdown specifically for the 21 TIME exit trades:
    time_mask = m1['exit_reason'].str.contains('TIME')
    df_time = df_comp[time_mask]
    print("\n=== THE 21 TRADES THAT PREVIOUSLY EXITED ON TIME ===")
    print(df_time[['id', 'orig_reason', 'orig_net', 'orig_hold', 'no_time_reason', 'no_time_net', 'no_time_hold', 'diff_net']].to_string())
    
    time_orig_net = df_time['orig_net'].sum()
    time_no_net = df_time['no_time_net'].sum()
    print(f"\nNet from these 21 trades with Time Exit: ${time_orig_net:.2f}")
    print(f"Net from these 21 trades WITHOUT Time Exit: ${time_no_net:.2f}")
    print(f"Difference: ${time_no_net - time_orig_net:.2f}")

if __name__ == '__main__':
    main()
