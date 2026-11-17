import pandas as pd
import numpy as np

def run_simulation():
    # Load 1m bars
    df_bars = pd.read_parquet('data/processed/xautusd_delta_oct1_to_now_1m.parquet')
    if 'timestamp' in df_bars.columns:
        df_bars = df_bars.set_index('timestamp')
    df_bars = df_bars.sort_index()
    
    O = df_bars['open'].to_numpy()
    H = df_bars['high'].to_numpy()
    Lo = df_bars['low'].to_numpy()
    C = df_bars['close'].to_numpy()
    n_bars = len(C)
    
    # Load the exact 108 trades of #1 Merged Super-Champion
    trades_df = pd.read_csv('data/processed/trades_DELTA_GOLD_MERGED_SUPER_CHAMPIONS.csv')
    m1 = trades_df[trades_df['profile_id'] == 'MERGE_1_SUPER_CONFLUENCE_OR_15M'].copy().reset_index(drop=True)
    
    # Also load the candidates pool from the report to see all candidate setups
    # We will simulate the exact 108 setups under two conditions:
    # 1. WITH Time Exit (as shown on the card: +$198.28, 79.63% WR, PF 3.20, Max DD -7.56%)
    # 2. WITHOUT Time Exit (positions hold until SL, Stall Lock, Breakeven, or Trailing SL triggers)
    
    def simulate_trade_engine(e_idx, direction, entry_px, sl_dist, tf, allow_time_exit=True):
        is_long = direction == 'LONG'
        init_sl = round(entry_px - sl_dist if is_long else entry_px + sl_dist, 2)
        cur_sl = init_sl
        stage = 0
        stall_locked = False
        peak_fav = 0.0
        peak_k = e_idx
        worst_adv = 0.0
        exit_px = None
        exit_k = None
        exit_reason = None
        
        max_hold = (270 if tf in ('15m', '1h') else 180) if allow_time_exit else 99999999
        end_k = min(n_bars, e_idx + max_hold + 1)
        
        for k in range(e_idx + 1, end_k):
            bars_held = k - e_idx
            if is_long:
                fav = H[k] - entry_px
                adv = entry_px - Lo[k]
                if fav > peak_fav:
                    peak_fav = fav
                    peak_k = k
                if adv > worst_adv: worst_adv = adv
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
                
                # Smart Stall Lock
                if stage <= 1 and cur_mfe_r >= 0.54:
                    if (k - peak_k >= 6) and (C[k] >= entry_px + 0.33 * sl_dist):
                        lock_px = round(entry_px + 0.33 * sl_dist, 2)
                        if C[k] >= lock_px and lock_px > cur_sl:
                            cur_sl = lock_px
                            stage = max(stage, 1)
                            stall_locked = True
                
                # Breakeven Lock (+1.05R -> +0.45R)
                if stage <= 1 and cur_mfe_r >= 1.05:
                    be_lock_px = round(entry_px + 0.45 * sl_dist, 2)
                    if be_lock_px > cur_sl: cur_sl = be_lock_px
                    stage = 2
                    stall_locked = False
                
                # Runner transition (+1.80R -> lock +0.85R)
                if stage <= 2 and cur_mfe_r >= 1.80:
                    run_lock = round(entry_px + 0.85 * sl_dist, 2)
                    if run_lock > cur_sl: cur_sl = run_lock
                    stage = 3
                    stall_locked = False
                
                # Continuous 40R Chandelier Trail (+2.10R trigger)
                if cur_mfe_r >= 2.10:
                    stage = 4
                    stall_locked = False
                    swing_low = float(np.min(Lo[max(0, k - 45): k + 1]))
                    atr_floor = float(entry_px + (cur_mfe_r - 0.85) * sl_dist)
                    cand_sl = round(max(swing_low - 0.35 * sl_dist, atr_floor), 2)
                    if cand_sl > cur_sl and cand_sl < C[k]:
                        cur_sl = cand_sl
            else: # SHORT
                fav = entry_px - Lo[k]
                adv = H[k] - entry_px
                if fav > peak_fav:
                    peak_fav = fav
                    peak_k = k
                if adv > worst_adv: worst_adv = adv
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
                    swing_high = float(np.max(H[max(0, k - 45): k + 1]))
                    atr_ceil = float(entry_px - (cur_mfe_r - 0.85) * sl_dist)
                    cand_sl = round(min(swing_high + 0.35 * sl_dist, atr_ceil), 2)
                    if cand_sl < cur_sl and cand_sl > C[k]:
                        cur_sl = cand_sl
                        
        if exit_px is None:
            exit_k = end_k - 1
            exit_px = round(float(C[exit_k]), 2)
            exit_reason = f"TIME_{max_hold}M" if allow_time_exit else "END_OF_SERIES"
            
        pts = round((exit_px - entry_px) if is_long else (entry_px - exit_px), 2)
        r_mult = round(pts / sl_dist, 2)
        qty = round(5.0 / sl_dist, 4)
        gross = round(pts * qty, 2)
        fee = round(0.0001 * qty * (entry_px + exit_px), 2)
        net = round(gross - fee, 2)
        
        return {
            'exit_px': exit_px,
            'exit_k': exit_k,
            'hold_mins': exit_k - e_idx,
            'exit_reason': exit_reason,
            'pts': pts,
            'r_mult': r_mult,
            'net_pnl_usd': net,
            'gross_pnl_usd': gross,
            'fee_usd': fee
        }

    # Now simulate all candidate trade setups under strict single-slot queue
    # 1. With Time Exit (exact baseline)
    # 2. Without Time Exit (indefinite hold)
    
    # We will run both queues through the exact same 108 setups
    trades_with_time = []
    trades_without_time = []
    
    # Track single-slot execution for both
    busy_until_time = -1
    busy_until_notime = -1
    
    for idx, t in m1.iterrows():
        ts = pd.to_datetime(t['entry_time'].replace(' UTC', ''))
        if ts.tzinfo is None: ts = ts.tz_localize('UTC')
        e_idx = df_bars.index.get_indexer([ts], method='nearest')[0]
        
        # Original with time exit (from official CSV)
        res_orig = {
            'id': t['id'],
            'entry_time': t['entry_time'],
            'net_pnl_usd': float(t['net_pnl_usd']),
            'gross_pnl_usd': float(t['gross_pnl_usd']),
            'hold_mins': int(t['hold_mins']),
            'exit_reason': t['exit_reason'],
            'r_mult': float(t['r_multiple']),
            'exit_k': e_idx + int(t['hold_mins'])
        }
        trades_with_time.append(res_orig)
        
        # Without time exit
        if e_idx >= busy_until_notime:
            res_notime = simulate_trade_engine(e_idx, t['direction'], float(t['entry_price']), float(t['init_risk_pts']), t['tf'], allow_time_exit=False)
            res_notime['id'] = len(trades_without_time) + 1
            res_notime['orig_id'] = t['id']
            res_notime['entry_time'] = t['entry_time']
            trades_without_time.append(res_notime)
            busy_until_notime = res_notime['exit_k']
            
    def calc_stats(t_list, start_eq=100.0):
        nets = [t['net_pnl_usd'] for t in t_list]
        wins = [n for n in nets if n > 0]
        losses = [n for n in nets if n <= 0]
        gw = sum(wins)
        gl = abs(sum(losses))
        pf = gw / gl if gl > 0 else 99.0
        tot_net = sum(nets)
        end_eq = start_eq + tot_net
        wr = len(wins) / len(nets) * 100 if nets else 0
        eq_curve = [start_eq]
        c_eq = start_eq
        for n in nets:
            c_eq += n
            eq_curve.append(c_eq)
        peaks = np.maximum.accumulate(eq_curve)
        dds = (peaks - eq_curve) / peaks * 100
        max_dd = np.max(dds)
        return {
            'count': len(t_list),
            'wins': len(wins),
            'losses': len(losses),
            'wr': wr,
            'tot_net': tot_net,
            'end_eq': end_eq,
            'pf': pf,
            'max_dd': max_dd
        }
        
    s_orig = calc_stats(trades_with_time)
    s_notime = calc_stats(trades_without_time)
    
    print("\n" + "="*80)
    print("EXACT #1 MERGED SUPER-CHAMPION STRATEGY AUDIT: WITH VS WITHOUT TIME EXIT")
    print("="*80)
    print(f"{'Metric':<25} | {'WITH Time Exit (Dashboard)':<28} | {'WITHOUT Time Exit':<25}")
    print("-"*80)
    print(f"{'Total Trades':<25} | {s_orig['count']:<28} | {s_notime['count']:<25}")
    print(f"{'Win Rate (%)':<25} | {s_orig['wr']:.2f}% ({s_orig['wins']}W / {s_orig['losses']}L)          | {s_notime['wr']:.2f}% ({s_notime['wins']}W / {s_notime['losses']}L)")
    print(f"{'Total Net Profit ($)':<25} | +${s_orig['tot_net']:.2f}                       | +${s_notime['tot_net']:.2f}")
    print(f"{'Ending Equity ($100 Init)':<25} | ${s_orig['end_eq']:.2f}                         | ${s_notime['end_eq']:.2f}")
    print(f"{'Profit Factor (PF)':<25} | {s_orig['pf']:.2f}                            | {s_notime['pf']:.2f}")
    print(f"{'Max Drawdown (%)':<25} | -{s_orig['max_dd']:.2f}%                         | -{s_notime['max_dd']:.2f}%")
    print("="*80)
    
    # Check missed trades
    executed_orig_ids = {t['orig_id'] for t in trades_without_time}
    missed_trades = [t for t in trades_with_time if t['id'] not in executed_orig_ids]
    print(f"\nTrades Missed/Blocked because previous trades held too long: {len(missed_trades)}")
    for mt in missed_trades:
        print(f"  - Trade #{mt['id']} ({mt['entry_time']}): Was a winner (+${mt['net_pnl_usd']:.2f}, {mt['exit_reason']}) in dashboard, but BLOCKED without time exit!")

if __name__ == '__main__':
    run_simulation()
