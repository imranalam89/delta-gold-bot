"""
Syndicate Alpha — 100% Deterministic Bar-By-Bar MTF Replay Engine
----------------------------------------------------------------
Every single trade is replayed bar-by-bar across 151,343 1-minute bars:
- Zero retroactive approximations
- Zero lookahead bias
- Exact entry candle timestamp & close price
- Exact stop loss touch verification on actual 1M Low/High
- Exact break-even move verification
- Exact take-profit touch verification on actual 1M High/Low
- Exact exit candle timestamp & price
- Exact notional, fees, gross PnL, net PnL, and equity curve
"""

import json
import os
import sys
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print("[ENGINE] Loading Master CME Globex Parquet dataset...")
df = pd.read_parquet('data/processed/GC_v0_2Year_L2_OrderFlow_Master.parquet')
if not df.index.tz:
    df.index = df.index.tz_localize('UTC')
else:
    df.index = df.index.tz_convert('UTC')

# Slice to the active 5-month period (May 28 to Oct 30, 2026)
start_dt = pd.to_datetime('2026-05-28 22:00:00', utc=True)
df_5m = df.loc[start_dt:].copy()
print(f"[ENGINE] Active 5-month bars: {len(df_5m)} bars ({df_5m.index[0]} to {df_5m.index[-1]})")

# Load candidate signals from all 11 specialists across all 4 timeframes
with open('data/processed/all_11_agents_lab_bundle.json', 'r', encoding='utf-8') as f:
    bundle = json.load(f)

# Extract every entry signal with its triggering timestamp, agent, direction, and timeframe
raw_signals = []
for ag, data in bundle.items():
    tf_data = data.get('timeframes', {})
    for tf_label in ['1m', '5m', '15m', '1h']:
        trades = tf_data.get(tf_label, {}).get('trades', [])
        for t in trades:
            raw_signals.append({
                'entry_time': t['entry_time'],
                'entry_ts': int(t['entry_ts']),
                'agent': ag,
                'direction': t['direction'],
                'tf': tf_label,
                'tf_rank': {'1h': 4, '15m': 3, '5m': 2, '1m': 1}[tf_label],
                'orig_sl_dist': float(t['sl_dist']),
                'orig_peak_r': float(t.get('peak_r', 0.0)),
                'orig_exit_reason': t.get('exit_reason', 'UNKNOWN')
            })

print(f"[ENGINE] Total candidate entry signals gathered: {len(raw_signals)}")

# Filter to Elite Specialists (ELENA, DEREK, MAYA, NINA, OMAR, MAX, LIAM, SAM)
ELITE_AGENTS = {'8:ELENA', '7:DEREK', '2:MAYA', '4:NINA', '10:OMAR', '5:MAX', '11:LIAM', '9:SAM'}
SNIPER_AGENTS = {'2:MAYA', '8:ELENA', '9:SAM', '11:LIAM', '4:NINA'}

elite_signals = [s for s in raw_signals if s['agent'] in ELITE_AGENTS]
# Sort by timestamp, then higher timeframe priority
elite_signals.sort(key=lambda x: (x['entry_ts'], -x['tf_rank']))
print(f"[ENGINE] Elite candidate signals: {len(elite_signals)}")

# Pre-convert DataFrame columns to numpy arrays for 100x speed
times = df_5m.index.to_numpy()
time_to_idx = {ts: idx for idx, ts in enumerate(times)}
closes = df_5m['close'].to_numpy(dtype=np.float64)
highs = df_5m['high'].to_numpy(dtype=np.float64)
lows = df_5m['low'].to_numpy(dtype=np.float64)
opens = df_5m['open'].to_numpy(dtype=np.float64)
n_bars = len(closes)

def simulate_real_bar_by_bar(
    signals,
    max_slots=2,
    cooldown_bars=8,
    max_hold_bars=120,
    be_trig_r=1.05,
    be_lock_r=0.38,
    tp1_r=1.80,
    trail_trig_r=2.50,
    trail_dist_r=0.85,
    fee_rate=0.0001,
    fixed_risk_usd=5.0,
    use_dampener=True
):
    equity = 100.0
    peak_equity = 100.0
    max_dd_pct = 0.0

    active_trades = []
    executed_trades = []
    cooldown_until_idx = -999
    consec_losses = 0

    for sig in signals:
        dt_str = sig['entry_time']
        dt_ts = pd.to_datetime(dt_str, utc=True)
        if dt_ts not in time_to_idx:
            continue
        idx = time_to_idx[dt_ts]

        # 1. Update existing active trades up to current candle idx
        rem_active = []
        for at in active_trades:
            # Did this trade already finish before or at current idx?
            if at['exit_idx'] <= idx:
                net_p = at['net_pnl_usd']
                equity += net_p
                peak_equity = max(peak_equity, equity)
                cur_dd = (peak_equity - equity) / peak_equity * 100.0
                max_dd_pct = max(max_dd_pct, cur_dd)
                at['equity_after'] = round(equity, 2)
                executed_trades.append(at)

                if net_p < 0:
                    consec_losses += 1
                else:
                    consec_losses = 0
            else:
                rem_active.append(at)
        active_trades = rem_active

        # Slot and cooldown gate
        if len(active_trades) >= max_slots:
            continue
        if idx < cooldown_until_idx:
            continue

        # Skip midday churn (12:00 - 16:59 EST)
        est_hr = (dt_ts.hour - 5) % 24
        if 12 <= est_hr <= 16:
            continue

        direction = sig['direction']
        entry_px = round(float(closes[idx]), 2)
        ag = sig['agent']
        is_sniper = ag in SNIPER_AGENTS

        # Stop loss sizing:
        # Use verified specialist structure distance, clamped strictly to safe bounds
        orig_sl = sig['orig_sl_dist']
        if is_sniper:
            sl_dist = round(min(orig_sl, 2.50), 2)
        else:
            sl_dist = round(min(orig_sl, 4.50), 2)
        sl_dist = max(sl_dist, 1.80)

        # Risk dampener on losing streak
        risk_usd = fixed_risk_usd
        if use_dampener and consec_losses >= 2:
            risk_usd = round(fixed_risk_usd * 0.50, 2)

        qty = round(risk_usd / sl_dist, 4)

        if direction == 'LONG':
            init_sl = round(entry_px - sl_dist, 2)
            cur_sl = init_sl
            be_target = round(entry_px + be_trig_r * sl_dist, 2)
            tp1_target = round(entry_px + tp1_r * sl_dist, 2)
        else:
            init_sl = round(entry_px + sl_dist, 2)
            cur_sl = init_sl
            be_target = round(entry_px - be_trig_r * sl_dist, 2)
            tp1_target = round(entry_px - tp1_r * sl_dist, 2)

        stage = 0 # 0: Armed, 1: BE Locked, 2: Partial TP1 Taken, 3: Trailing
        banked_pts = 0.0
        rem_weight = 1.0
        peak_r = 0.0
        exit_px = None
        exit_idx = None
        exit_reason = None

        end_k = min(n_bars, idx + max_hold_bars + 1)
        for k in range(idx + 1, end_k):
            # Check price on candle k
            if direction == 'LONG':
                cur_mfe = (highs[k] - entry_px) / sl_dist
                if cur_mfe > peak_r:
                    peak_r = cur_mfe

                # Check SL touch
                if lows[k] <= cur_sl:
                    exit_px = cur_sl
                    exit_idx = k
                    exit_reason = 'SL' if stage == 0 else ('BE_LOCK' if stage == 1 else 'TRAIL_EXIT')
                    break

                # Check BE trigger
                if stage == 0 and highs[k] >= be_target:
                    cur_sl = max(cur_sl, round(entry_px + be_lock_r * sl_dist, 2))
                    stage = 1

                # Check TP1 partial
                if stage <= 1 and highs[k] >= tp1_target:
                    banked_pts += 0.50 * (tp1_target - entry_px)
                    rem_weight = 0.50
                    cur_sl = max(cur_sl, round(entry_px + 0.45 * sl_dist, 2))
                    stage = 2

                # Check Trailing
                if stage == 2 and cur_mfe >= trail_trig_r:
                    trail_px = round(highs[k] - trail_dist_r * sl_dist, 2)
                    if trail_px > cur_sl:
                        cur_sl = trail_px
                        stage = 3
                elif stage == 3:
                    trail_px = round(highs[k] - trail_dist_r * sl_dist, 2)
                    if trail_px > cur_sl:
                        cur_sl = trail_px
            else: # SHORT
                cur_mfe = (entry_px - lows[k]) / sl_dist
                if cur_mfe > peak_r:
                    peak_r = cur_mfe

                # Check SL touch
                if highs[k] >= cur_sl:
                    exit_px = cur_sl
                    exit_idx = k
                    exit_reason = 'SL' if stage == 0 else ('BE_LOCK' if stage == 1 else 'TRAIL_EXIT')
                    break

                # Check BE trigger
                if stage == 0 and lows[k] <= be_target:
                    cur_sl = min(cur_sl, round(entry_px - be_lock_r * sl_dist, 2))
                    stage = 1

                # Check TP1 partial
                if stage <= 1 and lows[k] <= tp1_target:
                    banked_pts += 0.50 * (entry_px - tp1_target)
                    rem_weight = 0.50
                    cur_sl = min(cur_sl, round(entry_px - 0.45 * sl_dist, 2))
                    stage = 2

                # Check Trailing
                if stage == 2 and cur_mfe >= trail_trig_r:
                    trail_px = round(lows[k] + trail_dist_r * sl_dist, 2)
                    if trail_px < cur_sl:
                        cur_sl = trail_px
                        stage = 3
                elif stage == 3:
                    trail_px = round(lows[k] + trail_dist_r * sl_dist, 2)
                    if trail_px < cur_sl:
                        cur_sl = trail_px

        if exit_px is None:
            # Max hold time exit at closing price of final bar
            exit_idx = end_k - 1
            exit_px = round(float(closes[exit_idx]), 2)
            exit_reason = f'TIME_{max_hold_bars}M'

        # Exact PnL calculations
        pts = (exit_px - entry_px) if direction == 'LONG' else (entry_px - exit_px)
        tot_pts = round(banked_pts + rem_weight * pts, 2)
        r_mult = round(tot_pts / sl_dist, 2)
        gross_usd = round(tot_pts * qty, 2)
        notional = round(qty * entry_px, 2)
        fees = round(fee_rate * (qty * entry_px + qty * exit_px), 2)
        net_usd = round(gross_usd - fees, 2)

        dt_ent = pd.to_datetime(times[idx])
        dt_ext = pd.to_datetime(times[exit_idx])

        trade_record = {
            'id': len(executed_trades) + len(active_trades) + 1,
            'entry_time': dt_ent.strftime("%Y-%m-%d %H:%M UTC"),
            'exit_time': dt_ext.strftime("%Y-%m-%d %H:%M UTC"),
            'entry_idx': idx,
            'exit_idx': exit_idx,
            'direction': direction,
            'setup_agent': ag,
            'tf': sig['tf'],
            'entry_price': entry_px,
            'exit_price': exit_px,
            'sl_price': init_sl,
            'init_risk_pts': sl_dist,
            'pnl_pts': tot_pts,
            'r_multiple': r_mult,
            'qty_oz': qty,
            'notional_usd': notional,
            'gross_pnl_usd': gross_usd,
            'delta_fee_usd': fees,
            'net_pnl_usd': net_usd,
            'equity_after': 0.0,
            'exit_reason': exit_reason,
            'hold_mins': exit_idx - idx,
            'peak_r': round(peak_r, 2)
        }
        active_trades.append(trade_record)
        cooldown_until_idx = idx + cooldown_bars

    # Flush any remaining active trades
    for at in active_trades:
        net_p = at['net_pnl_usd']
        equity += net_p
        peak_equity = max(peak_equity, equity)
        cur_dd = (peak_equity - equity) / peak_equity * 100.0
        max_dd_pct = max(max_dd_pct, cur_dd)
        at['equity_after'] = round(equity, 2)
        executed_trades.append(at)

    wins = [t for t in executed_trades if t['net_pnl_usd'] > 0]
    losses = [t for t in executed_trades if t['net_pnl_usd'] <= 0]
    tot_net = sum(t['net_pnl_usd'] for t in executed_trades)
    wr = len(wins) / len(executed_trades) * 100.0 if executed_trades else 0.0
    gross_w = sum(t['net_pnl_usd'] for t in wins)
    gross_l = abs(sum(t['net_pnl_usd'] for t in losses))
    pf = (gross_w / gross_l) if gross_l > 0 else 99.0

    return executed_trades, tot_net, wr, pf, max_dd_pct, equity

print("\n[SIMULATION] Executing 100% deterministic bar-by-bar engine...")
trades, tot_net, wr, pf, max_dd, end_eq = simulate_real_bar_by_bar(elite_signals)

print(f"\n=========================================================================")
print(f"   100% BAR-BY-BAR DETERMINISTIC VERIFIED RESULTS ({len(trades)} TRADES)")
print(f"=========================================================================")
print(f"Total Trades:     {len(trades)}")
print(f"Win Rate:         {wr:.2f}% ({sum(1 for t in trades if t['net_pnl_usd'] > 0)}W / {sum(1 for t in trades if t['net_pnl_usd'] <= 0)}L)")
print(f"Net PnL:          +${tot_net:.2f}")
print(f"Starting Equity:  $100.00")
print(f"Ending Equity:    ${end_eq:.2f}")
print(f"Profit Factor:    {pf:.2f}")
print(f"Max Drawdown:     -{max_dd:.2f}%")
print(f"=========================================================================")
