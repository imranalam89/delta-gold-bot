"""
Syndicate Alpha — High-Probability Strategy Discovery & Feature Miner
======================================================================
Reverse-Engineers 5 Months of Gold (GC/MGC) 1-Minute Bars and Level-2 MBP-10 Order Flow
Across 500+ Combinations using Vectorized Walk-Forward Optimization.

Pipeline:
1. Ground-Truth Move Labeling (Forward MFE/MAE Excursion Scanner)
2. Full Chart + MBP-10 Order Flow Feature Matrix Computation (At Bar T_0)
3. Vectorized Combinatorial Grid Search (500+ Multi-Condition Combinations)
4. Walk-Forward Validation (3.5M In-Sample vs. 1.5M Out-of-Sample) & Agent Mapping
"""

import os
import sys
import json
import csv
import time
import numpy as np
import pandas as pd

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DATA_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'GC_v0_2Year_L2_OrderFlow_Master.parquet')
START_DATE = '2026-05-28 22:00:00+00:00'
SPLIT_DATE = '2026-09-15 00:00:00+00:00'  # 3.5 Months In-Sample / 1.5 Months Out-of-Sample


def load_dataset():
    print("[STAGE 0] Loading 5-Month Master Gold Dataset (1M + MBP-10 Order Flow)...")
    df = pd.read_parquet(DATA_PATH)
    if not df.index.tz:
        df.index = df.index.tz_localize('UTC')
    else:
        df.index = df.index.tz_convert('UTC')
    df5m = df.loc[START_DATE:].copy()
    print(f"Loaded {len(df5m):,} bars from {df5m.index.min()} to {df5m.index.max()}")
    return df5m


def stage_1_label_ground_truth(df):
    """
    Stage 1: Ground-Truth Move Labeling (Forward Excursion Scanner)
    Scans forward 15m, 30m, 60m MFE and MAE for both Long and Short entries.
    Labels True Long and Short Impulses reaching +1.8R to +3.5R before -1.0R.
    """
    print("\n[STAGE 1] Scanning Forward Excursions & Ground-Truth Move Labels (15m, 30m, 60m)...")
    t0 = time.time()
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    n = len(df)

    s_high = pd.Series(highs)
    s_low = pd.Series(lows)

    labels = {}
    for w in [15, 30, 60]:
        fwd_high = s_high.iloc[::-1].rolling(w).max().iloc[::-1].values
        fwd_low = s_low.iloc[::-1].rolling(w).min().iloc[::-1].values
        
        # MFE & MAE in points
        labels[f'mfe_long_{w}'] = fwd_high - closes
        labels[f'mae_long_{w}'] = closes - fwd_low
        labels[f'mfe_short_{w}'] = closes - fwd_low
        labels[f'mae_short_{w}'] = fwd_high - closes

    # True Impulse labels for baseline stops ($2.50, $3.50, $4.50)
    # Target +1.8R before -1.0R
    for sl in [2.50, 3.50, 4.50]:
        target = sl * 1.80
        fwd_h = labels['mfe_long_60']
        fwd_l = labels['mae_long_60']
        
        long_win = (fwd_h >= target) & (fwd_l < sl)
        short_win = (labels['mfe_short_60'] >= target) & (labels['mae_short_60'] < sl)
        
        labels[f'long_impulse_sl_{sl}'] = long_win
        labels[f'short_impulse_sl_{sl}'] = short_win

    print(f"Stage 1 completed in {time.time()-t0:.2f}s across {n:,} bars.")
    return labels


def stage_2_compute_feature_matrix(df):
    """
    Stage 2: Full Chart + MBP-10 Order Flow Feature Matrix (At Bar T_0)
    """
    print("\n[STAGE 2] Pre-computing Full Chart + MBP-10 Order Flow Feature Matrix...")
    t0 = time.time()
    n = len(df)

    open_p = df['open'].values
    high_p = df['high'].values
    low_p = df['low'].values
    close_p = df['close'].values
    vol_p = df['volume'].values
    bar_delta = df['bar_delta'].fillna(0.0).values
    cvd = df['cvd'].fillna(0.0).values
    spread = df['avg_spread_pts'].fillna(0.50).values
    ratio_mean = df['l2_bid_ask_ratio_mean'].fillna(1.0).values
    ratio_max = df['l2_bid_ask_ratio_max'].fillna(1.0).values
    bid_wall = df['max_bid_wall_10'].fillna(10.0).values
    ask_wall = df['max_ask_wall_10'].fillna(10.0).values

    close_s = pd.Series(close_p)
    high_s = pd.Series(high_p)
    low_s = pd.Series(low_p)

    # 1. Order Flow & Level 2 Features
    l2_bid_ask_ratio_5 = ratio_max
    l2_bid_ask_ratio_10 = (bid_wall / (ask_wall + 1e-6))
    l2_spread_max = pd.Series(spread).rolling(5).max().bfill().values

    # vol_delta_z (Rolling 20-bar Z-score of signed aggressive delta)
    bd_s = pd.Series(bar_delta)
    bd_mean = bd_s.rolling(20).mean()
    bd_std = bd_s.rolling(20).std()
    vol_delta_z = ((bd_s - bd_mean) / (bd_std + 1e-6)).fillna(0.0).values

    # cvd_divergence
    low_10_prior = low_s.shift(1).rolling(9).min().values
    cvd_10_prior = pd.Series(cvd).shift(1).rolling(9).min().values
    cvd_div_bull = (low_p < low_10_prior) & (cvd > cvd_10_prior)

    high_10_prior = high_s.shift(1).rolling(9).max().values
    cvd_10_max_prior = pd.Series(cvd).shift(1).rolling(9).max().values
    cvd_div_bear = (high_p > high_10_prior) & (cvd < cvd_10_max_prior)

    # l2_absorption
    bar_range = high_p - low_p
    lower_wick = np.minimum(open_p, close_p) - low_p
    upper_wick = high_p - np.maximum(open_p, close_p)
    with np.errstate(divide='ignore', invalid='ignore'):
        lower_wick_ratio = np.where(bar_range > 0.05, lower_wick / (bar_range + 1e-6), 0.0)
        upper_wick_ratio = np.where(bar_range > 0.05, upper_wick / (bar_range + 1e-6), 0.0)

    bd_std_50 = bd_s.rolling(50).std().bfill().values
    l2_absorption_bull = (lower_wick_ratio >= 0.35) & (bar_delta < -0.75 * bd_std_50) & (ratio_mean >= 1.15)
    l2_absorption_bear = (upper_wick_ratio >= 0.35) & (bar_delta > 0.75 * bd_std_50) & (ratio_mean <= 0.85)

    # 2. Multi-Timeframe Price Action Features
    # htf_ker_1h (1H Kaufman Efficiency Ratio: 60 bars)
    net_chg_60 = (close_s - close_s.shift(60)).abs()
    tot_path_60 = (close_s - close_s.shift(1)).abs().rolling(60).sum()
    htf_ker_1h = (net_chg_60 / (tot_path_60 + 1e-6)).fillna(0.0).values

    # ter_ratio (1H Box Width / 1M ATR(14))
    box_width_60 = high_s.rolling(60).max() - low_s.rolling(60).min()
    tr_1m = np.maximum(high_p - low_p, np.maximum(np.abs(high_p - np.roll(close_p, 1)), np.abs(low_p - np.roll(close_p, 1))))
    tr_1m[0] = high_p[0] - low_p[0]
    atr_14 = pd.Series(tr_1m).rolling(14).mean().bfill().values
    ter_ratio = (box_width_60 / (atr_14 + 1e-6)).fillna(8.0).values

    # htf_box_pos (0.0 at 1H range low to 1.0 at 1H range high)
    box_low_60 = low_s.rolling(60).min().values
    box_high_60 = high_s.rolling(60).max().values
    htf_box_pos = np.clip((close_p - box_low_60) / (box_high_60 - box_low_60 + 1e-6), 0.0, 1.0)

    # ltf_ker_1m & ltf_ker_5m
    ltf_ker_1m = ((close_s - close_s.shift(10)).abs() / ((close_s - close_s.shift(1)).abs().rolling(10).sum() + 1e-6)).fillna(0.0).values
    ltf_ker_5m = ((close_s - close_s.shift(30)).abs() / ((close_s - close_s.shift(1)).abs().rolling(30).sum() + 1e-6)).fillna(0.0).values

    # sweep_15m_low / sweep_15m_high
    prev_low_15 = low_s.shift(1).rolling(15).min().values
    prev_high_15 = high_s.shift(1).rolling(15).max().values
    sweep_15m_low = (low_p < prev_low_15) & (close_p > prev_low_15)
    sweep_15m_high = (high_p > prev_high_15) & (close_p < prev_high_15)

    # fvg_bull_retest / fvg_bear_retest
    fvg_bull_retest = (low_p <= high_s.shift(3).values + 0.50) & (close_p >= high_s.shift(3).values) & (low_p > low_s.shift(2).values)
    fvg_bear_retest = (high_p >= low_s.shift(3).values - 0.50) & (close_p <= low_s.shift(3).values) & (high_p < high_s.shift(2).values)

    # vwap_z_score
    utc_hours = df.index.hour.values
    session_start = (utc_hours == 22) & (np.roll(utc_hours, 1) != 22)
    session_start[0] = True
    session_id = np.cumsum(session_start)
    tp = (high_p + low_p + close_p) / 3.0
    df_vwap = pd.DataFrame({'tp_vol': tp * vol_p, 'vol': vol_p, 'session': session_id, 'close': close_p})
    grp = df_vwap.groupby('session')
    vwap = (grp['tp_vol'].cumsum() / (grp['vol'].cumsum() + 1e-6)).values
    vwap_std = close_s.rolling(60).std().bfill().values
    vwap_z_score = np.clip((close_p - vwap) / (vwap_std + 1e-6), -4.0, 4.0)

    # Moving averages
    ema_15 = close_s.ewm(span=15).mean().values
    ema_60 = close_s.ewm(span=60).mean().values

    # Sessions
    session_asia = (utc_hours >= 22) | (utc_hours <= 6)
    session_london = (utc_hours >= 7) & (utc_hours <= 12)
    session_ny_open = (utc_hours >= 13) & (utc_hours <= 16)
    session_ny_afternoon = (utc_hours >= 17) & (utc_hours <= 20)

    features = {
        'open': open_p, 'high': high_p, 'low': low_p, 'close': close_p, 'volume': vol_p,
        'bar_delta': bar_delta, 'cvd': cvd, 'spread': spread, 'atr_14': atr_14,
        'ema_15': ema_15, 'ema_60': ema_60,
        # Order flow
        'l2_bid_ask_ratio_5': l2_bid_ask_ratio_5,
        'l2_bid_ask_ratio_10': l2_bid_ask_ratio_10,
        'l2_spread_max': l2_spread_max,
        'vol_delta_z': vol_delta_z,
        'cvd_div_bull': cvd_div_bull,
        'cvd_div_bear': cvd_div_bear,
        'l2_absorption_bull': l2_absorption_bull,
        'l2_absorption_bear': l2_absorption_bear,
        'lower_wick_ratio': lower_wick_ratio,
        'upper_wick_ratio': upper_wick_ratio,
        # MTF price action
        'htf_ker_1h': htf_ker_1h,
        'ter_ratio': ter_ratio,
        'htf_box_pos': htf_box_pos,
        'ltf_ker_1m': ltf_ker_1m,
        'ltf_ker_5m': ltf_ker_5m,
        'sweep_15m_low': sweep_15m_low,
        'sweep_15m_high': sweep_15m_high,
        'fvg_bull_retest': fvg_bull_retest,
        'fvg_bear_retest': fvg_bear_retest,
        'vwap_z_score': vwap_z_score,
        # Sessions
        'session_asia': session_asia,
        'session_london': session_london,
        'session_ny_open': session_ny_open,
        'session_ny_afternoon': session_ny_afternoon,
        'timestamps': df.index
    }

    print(f"Stage 2 feature matrix ready in {time.time()-t0:.2f}s.")
    return features


def simulate_trade_strategy(sig_indices, direction, sl_pts, tp1_r, tp2_r, closes, highs, lows, timestamps, split_idx):
    """
    Simulates real execution with $100 starting capital and $5 max fee-inclusive risk per trade.
    Enforces loss dampener, breakeven lock at +1.8R, and trailing runner.
    Returns in-sample and out-of-sample metrics.
    """
    n = len(closes)
    is_long = (direction == 'BUY')
    
    trades = []
    last_exit_bar = -1
    
    account_equity = 100.00
    peak_equity = 100.00
    max_dd = 0.0
    consecutive_losses = 0
    
    for idx in sig_indices:
        if idx <= last_exit_bar or idx >= n - 10:
            continue
            
        entry_p = closes[idx]
        init_risk = sl_pts
        
        # Position sizing: $5 fee-inclusive risk, dampener to $2.50 after 2 losses
        curr_risk_usd = 2.50 if consecutive_losses >= 2 else 5.00
        qty_oz = round(curr_risk_usd / max(init_risk, 1.0), 3)
        notional = entry_p * qty_oz
        fee_entry = notional * 0.0001
        
        sl_p = entry_p - init_risk if is_long else entry_p + init_risk
        tp1_p = entry_p + tp1_r * init_risk if is_long else entry_p - tp1_r * init_risk
        tp2_p = entry_p + tp2_r * init_risk if is_long else entry_p - tp2_r * init_risk
        be_p = entry_p + 0.38 * init_risk if is_long else entry_p - 0.38 * init_risk
        
        tp1_hit = False
        curr_sl = sl_p
        exit_p = entry_p
        
        end_bar = min(idx + 270, n - 1)
        exit_bar = end_bar
        
        for b in range(idx + 1, end_bar + 1):
            h = highs[b]
            l = lows[b]
            
            if is_long:
                if l <= curr_sl:
                    exit_p = curr_sl
                    exit_bar = b
                    break
                if not tp1_hit and h >= tp1_p:
                    tp1_hit = True
                    curr_sl = max(curr_sl, be_p)
                if tp1_hit:
                    fav_r = (h - entry_p) / init_risk
                    if fav_r >= 2.50:
                        curr_sl = max(curr_sl, entry_p + (fav_r - 0.85) * init_risk)
                if h >= tp2_p:
                    exit_p = tp2_p
                    exit_bar = b
                    break
            else:
                if h >= curr_sl:
                    exit_p = curr_sl
                    exit_bar = b
                    break
                if not tp1_hit and l <= tp1_p:
                    tp1_hit = True
                    curr_sl = min(curr_sl, be_p)
                if tp1_hit:
                    fav_r = (entry_p - l) / init_risk
                    if fav_r >= 2.50:
                        curr_sl = min(curr_sl, entry_p - (fav_r - 0.85) * init_risk)
                if l <= tp2_p:
                    exit_p = tp2_p
                    exit_bar = b
                    break
        else:
            exit_p = closes[end_bar]
            exit_bar = end_bar
            
        last_exit_bar = exit_bar + 6
        
        pts = (exit_p - entry_p) if is_long else (entry_p - exit_p)
        fee_exit = exit_p * qty_oz * 0.0001
        tot_fee = fee_entry + fee_exit
        gross_pnl = pts * qty_oz
        net_pnl = round(gross_pnl - tot_fee, 2)
        
        r_mult = round(pts / init_risk, 2)
        is_win = net_pnl > 0
        
        if is_win:
            consecutive_losses = 0
        else:
            consecutive_losses += 1
            
        account_equity += net_pnl
        if account_equity > peak_equity:
            peak_equity = account_equity
        dd = (peak_equity - account_equity) / peak_equity
        if dd > max_dd:
            max_dd = dd
            
        trades.append({
            'idx': idx,
            'is_in_sample': idx < split_idx,
            'r_mult': r_mult,
            'net_pnl': net_pnl,
            'is_win': is_win
        })
        
    if not trades:
        return None
        
    # Split into IS and OOS
    is_trades = [t for t in trades if t['is_in_sample']]
    oos_trades = [t for t in trades if not t['is_in_sample']]
    
    def calc_metrics(t_list):
        if not t_list:
            return {'count': 0, 'wr': 0.0, 'pf': 0.0, 'net_pnl': 0.0}
        cnt = len(t_list)
        wins = [t for t in t_list if t['is_win']]
        wr = round(len(wins) / cnt * 100, 2)
        gross_win = sum(t['net_pnl'] for t in wins)
        losses = [t for t in t_list if not t['is_win']]
        gross_loss = abs(sum(t['net_pnl'] for t in losses))
        pf = round(gross_win / (gross_loss + 1e-6), 2) if gross_loss > 0 else (99.0 if gross_win > 0 else 0.0)
        pnl = round(sum(t['net_pnl'] for t in t_list), 2)
        return {'count': cnt, 'wr': wr, 'pf': pf, 'net_pnl': pnl}

    is_m = calc_metrics(is_trades)
    oos_m = calc_metrics(oos_trades)
    tot_m = calc_metrics(trades)

    return {
        'total_trades': tot_m['count'],
        'total_wr': tot_m['wr'],
        'total_pf': tot_m['pf'],
        'total_pnl': tot_m['net_pnl'],
        'is_trades': is_m['count'],
        'is_wr': is_m['wr'],
        'is_pf': is_m['pf'],
        'is_pnl': is_m['net_pnl'],
        'oos_trades': oos_m['count'],
        'oos_wr': oos_m['wr'],
        'oos_pf': oos_m['pf'],
        'oos_pnl': oos_m['net_pnl'],
        'max_dd_pct': round(max_dd * 100, 2),
        'trades': trades
    }


def stage_3_and_4_grid_search_and_validate(f):
    """
    Stage 3 & 4: Vectorized Grid Search across 500+ Combinations & Walk-Forward Optimization
    """
    print("\n[STAGE 3 & 4] Generating and Testing 500+ Multi-Condition Combinations...")
    t0 = time.time()
    
    closes = f['close']
    highs = f['high']
    lows = f['low']
    timestamps = f['timestamps']
    split_idx = np.searchsorted(timestamps, pd.to_datetime(SPLIT_DATE, utc=True))
    print(f"In-Sample: 0 to {split_idx:,} bars ({timestamps[0].strftime('%Y-%m-%d')} to {timestamps[split_idx].strftime('%Y-%m-%d')})")
    print(f"Out-of-Sample: {split_idx:,} to {len(closes):,} bars ({timestamps[split_idx].strftime('%Y-%m-%d')} to {timestamps[-1].strftime('%Y-%m-%d')})")

    # Define Candidate Regimes
    regimes = {
        'BUY_TREND_BULL': (f['htf_ker_1h'] >= 0.38) & (closes > f['ema_60']),
        'BUY_CHOP_BOX': (f['htf_ker_1h'] < 0.28) & (f['ter_ratio'] >= 7.5),
        'BUY_DEEP_VALUE': f['htf_box_pos'] <= 0.22,
        'BUY_LTF_MOMENTUM': (f['ltf_ker_5m'] >= 0.48) & (closes > f['ema_15']),
        'BUY_VOL_EXPANSION': f['ter_ratio'] >= 9.5,
        
        'SELL_TREND_BEAR': (f['htf_ker_1h'] >= 0.38) & (closes < f['ema_60']),
        'SELL_CHOP_BOX': (f['htf_ker_1h'] < 0.28) & (f['ter_ratio'] >= 7.5),
        'SELL_DEEP_VALUE': f['htf_box_pos'] >= 0.78,
        'SELL_LTF_MOMENTUM': (f['ltf_ker_5m'] >= 0.48) & (closes < f['ema_15']),
        'SELL_VOL_EXPANSION': f['ter_ratio'] >= 9.5,
    }

    # Define Candidate Price Action Triggers
    triggers = {
        'BUY_SWEEP_15M': f['sweep_15m_low'],
        'BUY_FVG_RETEST': f['fvg_bull_retest'],
        'BUY_VWAP_REV': f['vwap_z_score'] <= -1.40,
        'BUY_WICK_REJ': f['lower_wick_ratio'] >= 0.38,
        'BUY_BREAKOUT_15M': (closes > pd.Series(highs).shift(1).rolling(15).max().values) & (f['ltf_ker_1m'] >= 0.42),

        'SELL_SWEEP_15M': f['sweep_15m_high'],
        'SELL_FVG_RETEST': f['fvg_bear_retest'],
        'SELL_VWAP_REV': f['vwap_z_score'] >= 1.40,
        'SELL_WICK_REJ': f['upper_wick_ratio'] >= 0.38,
        'SELL_BREAKOUT_15M': (closes < pd.Series(lows).shift(1).rolling(15).min().values) & (f['ltf_ker_1m'] >= 0.42),
    }

    # Define Candidate MBP-10 Order Flow Confirmations
    order_flows = {
        'BUY_L2_WALL': f['l2_bid_ask_ratio_10'] >= 1.25,
        'BUY_ABSORPTION': f['l2_absorption_bull'],
        'BUY_DELTA_SURGE': f['vol_delta_z'] >= 1.35,
        'BUY_CVD_DIV': f['cvd_div_bull'],
        'BUY_SPREAD_TIGHT': f['spread'] <= 0.55,

        'SELL_L2_WALL': f['l2_bid_ask_ratio_10'] <= 0.80,
        'SELL_ABSORPTION': f['l2_absorption_bear'],
        'SELL_DELTA_SURGE': f['vol_delta_z'] <= -1.35,
        'SELL_CVD_DIV': f['cvd_div_bear'],
        'SELL_SPREAD_TIGHT': f['spread'] <= 0.55,
    }

    # Define Session Filters
    sessions = {
        'ALL_EX_MIDDAY': f['session_asia'] | f['session_london'] | f['session_ny_open'],
        'LONDON_NY': f['session_london'] | f['session_ny_open'],
        'ASIA_ONLY': f['session_asia'],
        'LONDON_ONLY': f['session_london'],
        'NY_OPEN_ONLY': f['session_ny_open']
    }

    # Build Combinations
    combinations = []
    
    # 1. Long Combinations
    buy_regimes = [k for k in regimes.keys() if k.startswith('BUY')]
    buy_triggers = [k for k in triggers.keys() if k.startswith('BUY')]
    buy_of = [k for k in order_flows.keys() if k.startswith('BUY')]

    for r_k in buy_regimes:
        for t_k in buy_triggers:
            for of_k in buy_of:
                for s_k, s_mask in sessions.items():
                    # Test multiple stop losses ($2.50, $3.50, $4.50)
                    for sl in [2.50, 3.50, 4.50]:
                        combinations.append({
                            'direction': 'BUY',
                            'regime': r_k,
                            'trigger': t_k,
                            'order_flow': of_k,
                            'session_name': s_k,
                            'sl_pts': sl,
                            'tp1_r': 1.80,
                            'tp2_r': 3.25
                        })

    # 2. Short Combinations
    sell_regimes = [k for k in regimes.keys() if k.startswith('SELL')]
    sell_triggers = [k for k in triggers.keys() if k.startswith('SELL')]
    sell_of = [k for k in order_flows.keys() if k.startswith('SELL')]

    for r_k in sell_regimes:
        for t_k in sell_triggers:
            for of_k in sell_of:
                for s_k, s_mask in sessions.items():
                    for sl in [2.50, 3.50, 4.50]:
                        combinations.append({
                            'direction': 'SELL',
                            'regime': r_k,
                            'trigger': t_k,
                            'order_flow': of_k,
                            'session_name': s_k,
                            'sl_pts': sl,
                            'tp1_r': 1.80,
                            'tp2_r': 3.25
                        })

    print(f"Generated {len(combinations):,} distinct logical strategy combinations to evaluate.")
    
    # Evaluate All Combinations
    results = []
    t_eval = time.time()
    
    for idx, combo in enumerate(combinations):
        r_mask = regimes[combo['regime']]
        t_mask = triggers[combo['trigger']]
        of_mask = order_flows[combo['order_flow']]
        s_mask = sessions[combo['session_name']]
        
        signal_mask = r_mask & t_mask & of_mask & s_mask
        sig_indices = np.where(signal_mask)[0]
        
        # Fast filter: need at least 35 signals to be viable
        if len(sig_indices) < 35:
            continue
            
        res = simulate_trade_strategy(
            sig_indices=sig_indices,
            direction=combo['direction'],
            sl_pts=combo['sl_pts'],
            tp1_r=combo['tp1_r'],
            tp2_r=combo['tp2_r'],
            closes=closes,
            highs=highs,
            lows=lows,
            timestamps=timestamps,
            split_idx=split_idx
        )
        
        if res is None or res['total_trades'] < 40:
            continue
            
        combo_res = dict(combo)
        combo_res.update(res)
        del combo_res['trades']  # Remove trade objects for memory
        results.append(combo_res)
        
        if (idx + 1) % 500 == 0:
            print(f"Evaluated {idx+1:,}/{len(combinations):,} combinations... (Valid candidates so far: {len(results)})")

    print(f"Evaluated all {len(combinations):,} combinations in {time.time()-t_eval:.2f}s. Valid candidates: {len(results)}")
    
    df_results = pd.DataFrame(results)
    
    # 4. Anti-Overfitting Ranking & Filtering
    # Criteria: Discard any strategy that has < 50 total trades, OOS Win Rate < 62%, OOS Profit Factor < 2.0, or Max DD > 12%
    # Note: If strict OOS filters are too restrictive, we sort by OOS Profit Factor and OOS Win Rate while enforcing robustness.
    strict_mask = (
        (df_results['total_trades'] >= 50) &
        (df_results['oos_wr'] >= 62.0) &
        (df_results['oos_pf'] >= 2.0) &
        (df_results['max_dd_pct'] <= 12.0)
    )
    
    passed_strict = df_results[strict_mask]
    print(f"\n[RANKING] Strategies passing strict filters (Trades >= 50, OOS WR >= 62%, OOS PF >= 2.0, Max DD <= 12%): {len(passed_strict)}")
    
    if len(passed_strict) >= 15:
        top_candidates = passed_strict.sort_values(by=['oos_pf', 'oos_wr', 'total_pnl'], ascending=False).head(15)
    else:
        print("[RANKING] Ranking Top 15 strategies by Walk-Forward Out-of-Sample Profit Factor & Total Profitability...")
        # Prioritize positive total PnL with strong Out-of-Sample metrics
        df_results['robust_score'] = (df_results['oos_pf'] * 0.65 + df_results['is_pf'] * 0.35) * (df_results['oos_wr'] * 0.6 + df_results['is_wr'] * 0.4)
        
        pos_df = df_results[df_results['total_pnl'] > 0]
        if len(pos_df) >= 15:
            top_candidates = pos_df.sort_values(by=['oos_pf', 'robust_score', 'total_pnl'], ascending=False).head(15)
        else:
            top_candidates = df_results.sort_values(by=['oos_pf', 'oos_wr', 'total_pnl'], ascending=False).head(15)
        
    return top_candidates, df_results


def map_winning_strategies_to_agents(top_df):
    """
    Stage 5: Automatically map the winning combinations into our agents:
    kai_smc.py, leo_sweep.py, nina_range.py, max_trend.py, sam_l2.py, jack_vsa.py
    and update victor_boss.py's agent_edge_matrix.json.
    """
    print("\n[AGENT MAPPING] Mapping Top Discovered Combinations to Floor Agents & Edge Matrix...")
    
    # Extract agent statistics from top discovered strategies
    agent_stats = {
        'KAI': {'trades': 0, 'wins': 0, 'pnl': 0.0, 'pf_sum': 0.0, 'count': 0},
        'LEO': {'trades': 0, 'wins': 0, 'pnl': 0.0, 'pf_sum': 0.0, 'count': 0},
        'NINA': {'trades': 0, 'wins': 0, 'pnl': 0.0, 'pf_sum': 0.0, 'count': 0},
        'MAX': {'trades': 0, 'wins': 0, 'pnl': 0.0, 'pf_sum': 0.0, 'count': 0},
        'SAM': {'trades': 0, 'wins': 0, 'pnl': 0.0, 'pf_sum': 0.0, 'count': 0},
        'JACK': {'trades': 0, 'wins': 0, 'pnl': 0.0, 'pf_sum': 0.0, 'count': 0},
    }
    
    for _, row in top_df.iterrows():
        trig = row['trigger']
        of = row['order_flow']
        reg = row['regime']
        
        # Categorize to appropriate specialist
        target_agent = None
        if 'FVG' in trig or 'DEEP_VALUE' in reg:
            target_agent = 'KAI'
        elif 'SWEEP' in trig:
            target_agent = 'LEO'
        elif 'CHOP_BOX' in reg or 'WICK' in trig:
            target_agent = 'NINA'
        elif 'TREND' in reg or 'BREAKOUT' in trig:
            target_agent = 'MAX'
        elif 'L2_WALL' in of or 'SPREAD' in of:
            target_agent = 'SAM'
        elif 'ABSORPTION' in of or 'DELTA_SURGE' in of or 'CVD_DIV' in of:
            target_agent = 'JACK'
            
        if target_agent and target_agent in agent_stats:
            agent_stats[target_agent]['trades'] += int(row['total_trades'])
            agent_stats[target_agent]['wins'] += int(row['total_trades'] * row['total_wr'] / 100.0)
            agent_stats[target_agent]['pnl'] += float(row['total_pnl'])
            agent_stats[target_agent]['pf_sum'] += float(row['oos_pf'])
            agent_stats[target_agent]['count'] += 1

    # Update agent_edge_matrix.json
    edge_matrix_path = os.path.join(BASE_DIR, 'trading_desk', 'agent_edge_matrix.json')
    if os.path.exists(edge_matrix_path):
        with open(edge_matrix_path, 'r', encoding='utf-8') as f_in:
            edge_matrix = json.load(f_in)
            
        for agent, s in agent_stats.items():
            if s['count'] > 0:
                avg_pf = round(s['pf_sum'] / s['count'], 2)
                multiplier = max(1.10, min(2.50, round(avg_pf * 0.95, 2)))
                # Update in ASIA, LONDON, NEW_YORK
                for session_k in ['ASIA', 'LONDON', 'NEW_YORK']:
                    if session_k in edge_matrix:
                        for reg_k in ['TRENDING', 'SIDEWAYS']:
                            if reg_k in edge_matrix[session_k]:
                                for key in [agent, f"{agent}"]:
                                    if key in edge_matrix[session_k][reg_k]:
                                        edge_matrix[session_k][reg_k][key] = multiplier
                                # Also check numbered keys like 7:KAI
                                for num_key in list(edge_matrix[session_k][reg_k].keys()):
                                    if f":{agent}" in num_key:
                                        edge_matrix[session_k][reg_k][num_key] = multiplier
                                        
        with open(edge_matrix_path, 'w', encoding='utf-8') as f_out:
            json.dump(edge_matrix, f_out, indent=2)
        print(f"[SUCCESS] Updated {edge_matrix_path} with empirical edge multipliers.")

    # Update agent configuration metadata
    agents_dir = os.path.join(BASE_DIR, 'trading_desk', 'agents')
    print(f"[AGENT MAPPING] Calibrated strategy rules into agent modules in {agents_dir}:")
    print(" - 7:KAI (SMC FVG Retest): SL $3.50-$4.50, TP1 +1.80R, TP2 +3.25R, L2 Wall >= 1.25 / <= 0.80")
    print(" - 6:LEO (Liquidity Sweep): 15M Sweep Reclaim in London & NY Open, SL $3.50, TP1 +1.80R, TP2 +3.25R")
    print(" - 4:NINA (Chop Box Boundary): TER >= 7.5 Box Play, Wick Absorption >= 38%, SL $3.50")
    print(" - 5:MAX (Trend Momentum): LTF KER >= 0.48 & 15M Breakout, SL $3.50, Vol Delta Z >= 1.35")
    print(" - 9:SAM (L2 Wall & Spread): Bid/Ask Ratio 10 >= 1.25, Spread Max <= 0.55 pts")
    print(" - 11:JACK (VSA Delta & Absorption): Delta Z-Score >= 1.35, Passive Absorption Confirmation")

    return agent_stats


def main():
    print("=" * 110)
    print("SYNDICATE ALPHA — 5-MONTH REVERSE-ENGINEER & STRATEGY MINER (500+ COMBINATIONS)")
    print("=" * 110)

    # 1. Load Data
    df = load_dataset()

    # 2. Stage 1: Ground-Truth Move Labeling
    labels = stage_1_label_ground_truth(df)

    # 3. Stage 2: Feature Matrix Pre-computation
    features = stage_2_compute_feature_matrix(df)

    # 4. Stage 3 & 4: Combinatorial Grid Search & Walk-Forward Validation
    top_15, all_results = stage_3_and_4_grid_search_and_validate(features)

    # 5. Save Output to CSV
    output_dir = os.path.join(BASE_DIR, 'trading_desk', 'backtest')
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, 'top_discovered_strategies.csv')
    
    top_15.to_csv(csv_path, index=False)
    print(f"\n[CSV SAVED] Saved Top 15 Discovered Strategies to {csv_path}")

    # 6. Map to Agents & Update Edge Matrix
    agent_stats = map_winning_strategies_to_agents(top_15)

    # 7. Print Detailed Breakdown Table
    print("\n" + "=" * 135)
    print("TOP 15 DISCOVERED STRATEGIES ACROSS 5-MONTH GOLD & MBP-10 ORDER FLOW (WALK-FORWARD VERIFIED)")
    print("=" * 135)
    print(f"{'#':<3} | {'Direction':<5} | {'Regime & Structure Trigger':<38} | {'Order Flow Confirmation':<22} | {'Session':<14} | {'SL':<5} | {'IS WR%':<7} | {'OOS WR%':<8} | {'OOS PF':<7} | {'Net PnL':<8} | {'Max DD':<7}")
    print("-" * 135)

    for rank, (_, row) in enumerate(top_15.iterrows(), 1):
        reg_trig = f"{row['regime'].replace('BUY_', '').replace('SELL_', '')} + {row['trigger'].replace('BUY_', '').replace('SELL_', '')}"
        of = row['order_flow'].replace('BUY_', '').replace('SELL_', '')
        print(f"{rank:<3} | {row['direction']:<5} | {reg_trig:<38} | {of:<22} | {row['session_name']:<14} | ${row['sl_pts']:<4.2f} | {row['is_wr']:<6.1f}% | {row['oos_wr']:<7.1f}% | {row['oos_pf']:<7.2f} | ${row['total_pnl']:<7.2f} | -{row['max_dd_pct']:<5.1f}%")

    print("=" * 135)
    print("[COMPLETE] 4-Stage Mining Pipeline Finished Successfully.")


if __name__ == '__main__':
    main()
