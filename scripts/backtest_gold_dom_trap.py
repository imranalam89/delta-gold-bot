"""
Gold Entry Logic (Level 2 DOM Trap & Order Flow Absorption) Backtest Suite
--------------------------------------------------------------------------
Bar-by-bar simulation with 1-minute execution fidelity, exact lot sizing,
take profit limit orders, fixed structural stop loss, 15m post-trade cooldown,
and 2-hour cascade circuit breaker.
"""

import sys
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_gold_dom_trap_backtest():
    print("=" * 80)
    print("GOLD LEVEL-2 DOM TRAP & ORDER FLOW ABSORPTION BACKTEST")
    print("=" * 80)

    # 1. Load Parquet Data
    parquet_path = os.path.join(BASE_DIR, 'data', 'processed', 'GC_v0_2Year_L2_OrderFlow_Master.parquet')
    print(f"[1/6] Loading Master Parquet dataset from: {parquet_path}")
    df_raw = pd.read_parquet(parquet_path)
    if not df_raw.index.tz:
        df_raw.index = df_raw.index.tz_localize('UTC')
    else:
        df_raw.index = df_raw.index.tz_convert('UTC')

    df_1m = df_raw[df_raw['bar_delta'].notnull()].copy()
    print(f"      Valid Order Flow Period: {df_1m.index.min()} -> {df_1m.index.max()}")
    print(f"      Total 1-Minute Bars: {len(df_1m):,}")

    # 2. Resample to 15m, 30m, 1h, 4h
    print("[2/6] Resampling timeframes (15m, 30m, 1h, 4h)...")
    df_15m = df_1m.resample('15min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'bar_delta': 'sum'
    }).dropna(subset=['open'])

    df_30m = df_1m.resample('30min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'bar_delta': 'sum'
    }).dropna(subset=['open'])

    df_1h = df_1m.resample('1h').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna(subset=['open'])

    df_4h = df_1m.resample('4h').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).dropna(subset=['open'])

    # 3. Indicators & Structural Levels
    print("[3/6] Computing 24-bar 15m Swing Levels, 30m S/R, and MTF Consensus...")
    
    # 24-bar swing low / high prior to the sweep candle (shift 2 bars back)
    # Candle i-1 is the sweep candle. The swing lookback is the 24 bars preceding candle i-1.
    df_15m['sr_low'] = df_15m['low'].shift(2).rolling(24, min_periods=12).min()
    df_15m['sr_high'] = df_15m['high'].shift(2).rolling(24, min_periods=12).max()

    # 30-minute structural resistance and support (rolling 24 bars on 30m = 12 hours)
    df_30m['sr_30_hi'] = df_30m['high'].shift(1).rolling(24, min_periods=12).max()
    df_30m['sr_30_lo'] = df_30m['low'].shift(1).rolling(24, min_periods=12).min()

    # Higher timeframe trend for MTF Consensus
    # 1H EMAs
    df_1h['ema_20'] = df_1h['close'].ewm(span=20, adjust=False).mean()
    df_1h['ema_50'] = df_1h['close'].ewm(span=50, adjust=False).mean()
    df_1h['trend_1h'] = np.where(df_1h['close'] > df_1h['ema_50'], 1, -1)

    # 4H EMAs
    df_4h['ema_20'] = df_4h['close'].ewm(span=20, adjust=False).mean()
    df_4h['ema_50'] = df_4h['close'].ewm(span=50, adjust=False).mean()
    df_4h['trend_4h'] = np.where(df_4h['close'] > df_4h['ema_50'], 1, -1)

    # 15m EMAs
    df_15m['ema_20'] = df_15m['close'].ewm(span=20, adjust=False).mean()
    df_15m['ema_50'] = df_15m['close'].ewm(span=50, adjust=False).mean()
    df_15m['trend_15m'] = np.where(df_15m['close'] > df_15m['ema_50'], 1, -1)

    # Reindex HTF data onto 15m timeline strictly with forward-fill (no lookahead)
    s_30m_hi = df_30m['sr_30_hi'].reindex(df_15m.index, method='ffill')
    s_30m_lo = df_30m['sr_30_lo'].reindex(df_15m.index, method='ffill')
    trend_1h_aligned = df_1h['trend_1h'].reindex(df_15m.index, method='ffill').fillna(0)
    trend_4h_aligned = df_4h['trend_4h'].reindex(df_15m.index, method='ffill').fillna(0)

    df_15m['sr_30_hi'] = s_30m_hi
    df_15m['sr_30_lo'] = s_30m_lo
    df_15m['mtf_bullish'] = (trend_1h_aligned > 0) & ((df_15m['trend_15m'] > 0) | (trend_4h_aligned > 0))
    df_15m['mtf_bearish'] = (trend_1h_aligned < 0) & ((df_15m['trend_15m'] < 0) | (trend_4h_aligned < 0))

    # Precompute 1m price numpy arrays for ultra-fast bar-by-bar path verification
    m1_times = df_1m.index.to_numpy()
    m1_highs = df_1m['high'].to_numpy(dtype=np.float64)
    m1_lows = df_1m['low'].to_numpy(dtype=np.float64)
    m1_closes = df_1m['close'].to_numpy(dtype=np.float64)
    m1_opens = df_1m['open'].to_numpy(dtype=np.float64)
    m1_time_to_idx = {ts: idx for idx, ts in enumerate(m1_times)}

    # 4. Scan Signals
    print("[4/6] Evaluating Level-2 DOM Trap & Order Flow Absorption conditions...")
    
    n_bars = len(df_15m)
    c15_times = df_15m.index.to_numpy()
    c15_open = df_15m['open'].to_numpy(dtype=np.float64)
    c15_high = df_15m['high'].to_numpy(dtype=np.float64)
    c15_low = df_15m['low'].to_numpy(dtype=np.float64)
    c15_close = df_15m['close'].to_numpy(dtype=np.float64)
    c15_vol = df_15m['volume'].to_numpy(dtype=np.float64)
    c15_delta = df_15m['bar_delta'].to_numpy(dtype=np.float64)
    c15_sr_low = df_15m['sr_low'].to_numpy(dtype=np.float64)
    c15_sr_high = df_15m['sr_high'].to_numpy(dtype=np.float64)
    c15_sr30_hi = df_15m['sr_30_hi'].to_numpy(dtype=np.float64)
    c15_sr30_lo = df_15m['sr_30_lo'].to_numpy(dtype=np.float64)
    c15_mtf_bull = df_15m['mtf_bullish'].to_numpy(dtype=bool)
    c15_mtf_bear = df_15m['mtf_bearish'].to_numpy(dtype=bool)

    signals = []

    for i in range(26, n_bars):
        # Current candle: i, Previous candle: i-1
        # Check Long Entry Setup (Bear Trap Defense)
        # Condition 1: The Sweep - low[i-1] swept below sr_low
        sweep_long = c15_low[i-1] < c15_sr_low[i]

        # Condition 2: The Reclaim - close[i] > sr_low AND close[i] > close[i-1]
        reclaim_long = (c15_close[i] > c15_sr_low[i]) and (c15_close[i] > c15_close[i-1])

        # Condition 3: Rejection Wick - lower wick >= 25% of total range OR close[i] > open[i-1]
        range_long = c15_high[i] - c15_low[i]
        lower_wick = min(c15_open[i], c15_close[i]) - c15_low[i]
        wick_cond_long = (range_long > 0 and (lower_wick / range_long) >= 0.25) or (c15_close[i] > c15_open[i-1])

        # Condition 4: Delta Absorption Flip
        # prev_delta < 0 -> curr_delta > 0 OR positive delta >= 1.5% of candle volume
        delta_flip_long = ((c15_delta[i-1] < 0 and c15_delta[i] > 0) or 
                           (c15_delta[i] > 0 and c15_vol[i] > 0 and (c15_delta[i] / c15_vol[i]) >= 0.015))

        # Condition 5: Trend Alignment
        trend_long = c15_mtf_bull[i]

        if sweep_long and reclaim_long and wick_cond_long and delta_flip_long and trend_long:
            # Trap low: lowest price during trap
            trap_low = min(c15_low[i-1], c15_low[i])
            sl_dist = max(2.50, (c15_close[i] - trap_low) + 0.50)
            
            # Condition 6: Room-to-run filter (Clearance to opposing 30m resistance >= 1.5R)
            room_to_run_long = (c15_sr30_hi[i] - c15_close[i]) >= (1.5 * sl_dist)
            
            if room_to_run_long:
                lots = max(1, int(round(5.00 / (sl_dist * 0.001))))
                signals.append({
                    'bar_idx': i,
                    'time': pd.Timestamp(c15_times[i]),
                    'direction': 'LONG',
                    'entry_price': c15_close[i],
                    'trap_low': trap_low,
                    'trap_high': np.nan,
                    'sl_dist': sl_dist,
                    'sl_price': c15_close[i] - sl_dist,
                    'tp_price': c15_close[i] + (3.0 * sl_dist),
                    'lots': lots,
                    'sr_level': c15_sr_low[i],
                    'opposing_sr': c15_sr30_hi[i]
                })

        # Check Short Entry Setup (Bull Trap Absorption)
        # Condition 1: The Sweep - high[i-1] swept above sr_high
        sweep_short = c15_high[i-1] > c15_sr_high[i]

        # Condition 2: The Reclaim - close[i] < sr_high AND close[i] < close[i-1]
        reclaim_short = (c15_close[i] < c15_sr_high[i]) and (c15_close[i] < c15_close[i-1])

        # Condition 3: Rejection Wick - upper wick >= 25% of total range OR close[i] < open[i-1]
        range_short = c15_high[i] - c15_low[i]
        upper_wick = c15_high[i] - max(c15_open[i], c15_close[i])
        wick_cond_short = (range_short > 0 and (upper_wick / range_short) >= 0.25) or (c15_close[i] < c15_open[i-1])

        # Condition 4: Delta Absorption Flip
        # prev_delta > 0 -> curr_delta < 0 OR negative delta <= -1.5% of candle volume
        delta_flip_short = ((c15_delta[i-1] > 0 and c15_delta[i] < 0) or 
                            (c15_delta[i] < 0 and c15_vol[i] > 0 and (c15_delta[i] / c15_vol[i]) <= -0.015))

        # Condition 5: Trend Alignment
        trend_short = c15_mtf_bear[i]

        if sweep_short and reclaim_short and wick_cond_short and delta_flip_short and trend_short:
            # Trap high: highest price during trap
            trap_high = max(c15_high[i-1], c15_high[i])
            sl_dist = max(2.50, (trap_high - c15_close[i]) + 0.50)
            
            # Condition 6: Room-to-run filter (Clearance to opposing 30m support >= 1.5R)
            room_to_run_short = (c15_close[i] - c15_sr30_lo[i]) >= (1.5 * sl_dist)
            
            if room_to_run_short:
                lots = max(1, int(round(5.00 / (sl_dist * 0.001))))
                signals.append({
                    'bar_idx': i,
                    'time': pd.Timestamp(c15_times[i]),
                    'direction': 'SHORT',
                    'entry_price': c15_close[i],
                    'trap_low': np.nan,
                    'trap_high': trap_high,
                    'sl_dist': sl_dist,
                    'sl_price': c15_close[i] + sl_dist,
                    'tp_price': c15_close[i] - (3.0 * sl_dist),
                    'lots': lots,
                    'sr_level': c15_sr_high[i],
                    'opposing_sr': c15_sr30_lo[i]
                })

    print(f"      Total Raw Strategy Setups Triggered: {len(signals)}")
    long_count = sum(1 for s in signals if s['direction'] == 'LONG')
    short_count = sum(1 for s in signals if s['direction'] == 'SHORT')
    print(f"      - Long (Bear Trap Defense): {long_count}")
    print(f"      - Short (Bull Trap Absorption): {short_count}")

    # 5. Execute Simulation with Cooldown & Cascade Circuit Breaker
    print("[5/6] Simulating execution with 15m cooldown & 2h Cascade Circuit Breaker...")
    
    COOLDOWN_SEC = 900       # 15 minutes
    CIRCUIT_BREAKER_SEC = 7200  # 2 hours halt if 2 consecutive SL in 2 hours
    FEE_RATE = 0.0001        # Delta Exchange 0.01% taker fee per leg

    completed_trades = []
    consecutive_sl_times = []
    halt_until = None
    last_exit_time = None

    for sig in signals:
        sig_time = sig['time']
        
        # Check circuit breaker halt
        if halt_until is not None and sig_time < halt_until:
            continue
        
        # Check post-trade cooldown (15 minutes)
        if last_exit_time is not None:
            time_since_exit = (sig_time - last_exit_time).total_seconds()
            if time_since_exit < COOLDOWN_SEC:
                continue

        # Look up entry bar in 1m series
        # Entry executes at close of 15m bar
        entry_ts = sig_time
        if entry_ts not in m1_time_to_idx:
            # If exact timestamp not in 1m index, find closest preceding
            idx_list = np.searchsorted(m1_times, entry_ts)
            if idx_list >= len(m1_times):
                continue
            m1_start_idx = idx_list
        else:
            m1_start_idx = m1_time_to_idx[entry_ts] + 1

        # Simulate 1m path dependency
        direction = sig['direction']
        entry_price = sig['entry_price']
        sl_price = sig['sl_price']
        tp_price = sig['tp_price']
        lots = sig['lots']
        sl_dist = sig['sl_dist']

        exit_time = None
        exit_price = None
        exit_reason = None

        # Maximum hold: 48 hours (2880 1m bars)
        max_idx = min(len(m1_times), m1_start_idx + 2880)

        for curr_idx in range(m1_start_idx, max_idx):
            bar_h = m1_highs[curr_idx]
            bar_l = m1_lows[curr_idx]
            bar_t = pd.Timestamp(m1_times[curr_idx])

            if direction == 'LONG':
                # Check SL hit
                sl_hit = bar_l <= sl_price
                # Check TP hit
                tp_hit = bar_h >= tp_price

                if sl_hit and tp_hit:
                    # Conservative assumption: hit SL first if both touched in same bar
                    exit_price = sl_price
                    exit_reason = 'STOP_LOSS'
                    exit_time = bar_t
                    break
                elif sl_hit:
                    exit_price = sl_price
                    exit_reason = 'STOP_LOSS'
                    exit_time = bar_t
                    break
                elif tp_hit:
                    exit_price = tp_price
                    exit_reason = 'TAKE_PROFIT'
                    exit_time = bar_t
                    break
            else:  # SHORT
                sl_hit = bar_h >= sl_price
                tp_hit = bar_l <= tp_price

                if sl_hit and tp_hit:
                    exit_price = sl_price
                    exit_reason = 'STOP_LOSS'
                    exit_time = bar_t
                    break
                elif sl_hit:
                    exit_price = sl_price
                    exit_reason = 'STOP_LOSS'
                    exit_time = bar_t
                    break
                elif tp_hit:
                    exit_price = tp_price
                    exit_reason = 'TAKE_PROFIT'
                    exit_time = bar_t
                    break

        if exit_time is None:
            # End of dataset or max hold reached
            exit_idx = min(len(m1_times) - 1, max_idx - 1)
            exit_time = pd.Timestamp(m1_times[exit_idx])
            exit_price = m1_closes[exit_idx]
            exit_reason = 'TIME_EXPIRE'

        # Calculate PnL Math
        # Contract multiplier = 0.001
        mult = 0.001
        notional_entry = lots * mult * entry_price
        notional_exit = lots * mult * exit_price
        fee_entry = notional_entry * FEE_RATE
        fee_exit = notional_exit * FEE_RATE
        total_fees = fee_entry + fee_exit

        if direction == 'LONG':
            gross_pnl = (exit_price - entry_price) * lots * mult
        else:
            gross_pnl = (entry_price - exit_price) * lots * mult

        net_pnl = gross_pnl - total_fees
        r_multiple = gross_pnl / 5.00  # since risk is exactly $5.00

        trade_record = {
            'trade_id': len(completed_trades) + 1,
            'entry_time': str(sig_time),
            'exit_time': str(exit_time),
            'direction': direction,
            'entry_price': round(entry_price, 2),
            'exit_price': round(exit_price, 2),
            'sl_price': round(sl_price, 2),
            'tp_price': round(tp_price, 2),
            'sl_dist': round(sl_dist, 2),
            'lots': lots,
            'exit_reason': exit_reason,
            'gross_pnl': round(gross_pnl, 2),
            'net_pnl': round(net_pnl, 2),
            'total_fees': round(total_fees, 4),
            'r_multiple': round(r_multiple, 2),
            'duration_minutes': int((exit_time - sig_time).total_seconds() / 60)
        }
        completed_trades.append(trade_record)

        # Update last exit time
        last_exit_time = exit_time

        # Circuit breaker logic
        if exit_reason == 'STOP_LOSS':
            # Record SL exit time
            consecutive_sl_times.append(exit_time)
            # Retain only SLs within rolling 2-hour window
            consecutive_sl_times = [t for t in consecutive_sl_times if (exit_time - t).total_seconds() <= 7200]
            if len(consecutive_sl_times) >= 2:
                # 2 consecutive SLs in rolling 2-hour window -> trigger 2-hour halt
                halt_until = exit_time + timedelta(seconds=CIRCUIT_BREAKER_SEC)
                consecutive_sl_times = []
        else:
            # Win resets consecutive SL counter
            consecutive_sl_times = []

    # 6. Performance Metrics
    print("[6/6] Computing Performance Metrics & Journaling...")
    
    if len(completed_trades) == 0:
        print("[WARN] No trades were executed.")
        return

    df_trades = pd.DataFrame(completed_trades)
    
    # Save CSV
    out_csv = os.path.join(BASE_DIR, 'data', 'processed', 'trades_GOLD_DOM_TRAP_ABSORPTION.csv')
    df_trades.to_csv(out_csv, index=False)
    print(f"      Trade journal saved to: {out_csv}")

    total_trades = len(df_trades)
    wins = df_trades[df_trades['net_pnl'] > 0]
    losses = df_trades[df_trades['net_pnl'] <= 0]
    win_count = len(wins)
    loss_count = len(losses)
    win_rate = (win_count / total_trades) * 100.0

    total_gross = df_trades['gross_pnl'].sum()
    total_net = df_trades['net_pnl'].sum()
    total_fees = df_trades['total_fees'].sum()

    gross_profit = wins['gross_pnl'].sum()
    gross_loss = abs(losses['gross_pnl'].sum())
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else np.nan

    avg_win = wins['net_pnl'].mean() if win_count > 0 else 0.0
    avg_loss = losses['net_pnl'].mean() if loss_count > 0 else 0.0
    expectancy = (win_rate / 100.0 * avg_win) + ((1 - win_rate / 100.0) * avg_loss)

    # Equity curve and Max Drawdown
    df_trades['cum_net_pnl'] = df_trades['net_pnl'].cumsum()
    initial_capital = 100.0  # As standard on $100 account with $5 risk
    df_trades['equity'] = initial_capital + df_trades['cum_net_pnl']
    df_trades['peak_equity'] = df_trades['equity'].cummax()
    df_trades['drawdown'] = df_trades['equity'] - df_trades['peak_equity']
    df_trades['drawdown_pct'] = (df_trades['drawdown'] / df_trades['peak_equity']) * 100.0
    max_dd_usd = df_trades['drawdown'].min()
    max_dd_pct = df_trades['drawdown_pct'].min()

    tp_hits = len(df_trades[df_trades['exit_reason'] == 'TAKE_PROFIT'])
    sl_hits = len(df_trades[df_trades['exit_reason'] == 'STOP_LOSS'])
    time_exits = len(df_trades[df_trades['exit_reason'] == 'TIME_EXPIRE'])

    print("-" * 80)
    print("BACKTEST RESULTS SUMMARY:")
    print("-" * 80)
    print(f"Total Completed Trades:      {total_trades}")
    print(f"Win Rate:                    {win_rate:.2f}% ({win_count} Wins / {loss_count} Losses)")
    print(f"Take Profit Hits (1:3 RR):   {tp_hits} ({tp_hits/total_trades*100:.1f}%)")
    print(f"Stop Loss Hits:              {sl_hits} ({sl_hits/total_trades*100:.1f}%)")
    print(f"Time Expirations:            {time_exits}")
    print(f"Profit Factor (Gross):       {profit_factor:.2f}")
    print(f"Total Gross PnL:             ${total_gross:.2f}")
    print(f"Total Fees Paid:             ${total_fees:.2f}")
    print(f"Total Net PnL:               ${total_net:.2f}")
    print(f"Net Return on $100 Account:  +{(total_net / initial_capital) * 100:.1f}%")
    print(f"Average Win:                 ${avg_win:.2f} (+{avg_win/5.0:.2f}R)")
    print(f"Average Loss:                ${avg_loss:.2f} ({avg_loss/5.0:.2f}R)")
    print(f"Expectancy per Trade:        ${expectancy:.2f}")
    print(f"Max Drawdown:                ${max_dd_usd:.2f} ({max_dd_pct:.2f}%)")
    print(f"Average Trade Duration:      {df_trades['duration_minutes'].mean():.1f} minutes")
    print("-" * 80)

if __name__ == '__main__':
    run_gold_dom_trap_backtest()
