import json
from datetime import datetime, timezone
import numpy as np

with open('data/processed/all_11_agents_lab_bundle.json', 'r', encoding='utf-8') as f:
    bundle = json.load(f)

SNIPER_AGENTS = {'2:MAYA', '8:ELENA', '9:SAM', '11:LIAM', '4:NINA'}

all_agent_trades = []
for ag, data in bundle.items():
    champ = data.get('generations', {}).get('v3.0_ORACLE_CHAMPION', {})
    for t in champ.get('trades', []):
        t_copy = dict(t)
        t_copy['source_agent'] = ag
        t_copy['is_sniper'] = (ag in SNIPER_AGENTS)
        all_agent_trades.append(t_copy)

all_agent_trades.sort(key=lambda x: (x['entry_ts'], -x.get('net_pnl', 0)))

def run_simulation(
    consecutive_loss_dampener=False,
    session_analog_filter=False,
    daily_loss_limit=None,
    daily_profit_lock=None,
    trail_trig_r=2.50,
    trail_dist_r=1.05,
    be_trig_r=1.05,
    be_lock_r=0.38,
    max_slots=2,
    cooldown_seconds=480
):
    equity = 100.0
    peak_equity = 100.0
    max_dd_pct = 0.0
    fee_rate = 0.0001

    active_trades = []
    executed_trades = []
    cooldown_ts = 0

    current_day = None
    daily_pnl = 0.0
    daily_locked = False
    consec_losses = 0

    for cand in all_agent_trades:
        ts = cand['entry_ts']
        dt_ent = datetime.fromtimestamp(ts, tz=timezone.utc)
        day_str = dt_ent.strftime("%Y-%m-%d")
        est_hr = (dt_ent.hour - 5) % 24

        if day_str != current_day:
            current_day = day_str
            daily_pnl = 0.0
            daily_locked = False

        remaining_active = []
        for at in active_trades:
            if at['exit_ts'] <= ts:
                net_p = at['net_pnl_usd']
                equity += net_p
                daily_pnl += net_p
                peak_equity = max(peak_equity, equity)
                cur_dd = (peak_equity - equity) / peak_equity * 100.0
                max_dd_pct = max(max_dd_pct, cur_dd)
                at['equity_after'] = round(equity, 2)
                executed_trades.append(at)

                if net_p < 0:
                    consec_losses += 1
                else:
                    consec_losses = 0

                if daily_loss_limit and daily_pnl <= daily_loss_limit:
                    daily_locked = True
                if daily_profit_lock and daily_pnl >= daily_profit_lock:
                    daily_locked = True
            else:
                remaining_active.append(at)

        active_trades = remaining_active

        if daily_locked:
            continue
        if len(active_trades) >= max_slots:
            continue
        if ts < cooldown_ts:
            continue
        if session_analog_filter and est_hr in (12, 13, 14, 15, 16):
            continue

        is_sniper = cand['is_sniper']
        orig_sl = cand['sl_dist']
        entry_px = cand['entry_price']

        if is_sniper:
            init_sl = min(2.50, orig_sl)
        else:
            init_sl = min(1.25 * (orig_sl / 1.35), 8.5)
        init_sl = max(init_sl, 2.0)

        risk_usd = 5.0
        if consecutive_loss_dampener and consec_losses >= 2:
            risk_usd = 2.50

        qty = round(risk_usd / init_sl, 4)
        peak_mfe = cand['peak_r'] * orig_sl
        peak_r_new = peak_mfe / init_sl
        direction = cand['direction']

        if direction == 'LONG':
            sl_px = round(entry_px - init_sl, 2)
        else:
            sl_px = round(entry_px + init_sl, 2)

        if cand['exit_reason'] == 'SL':
            r_mult = -1.0
            exit_px = sl_px
            exit_reason = 'SL'
        else:
            if peak_r_new >= be_trig_r:
                r_mult = be_lock_r
                exit_reason = 'BE_LOCK'
            if peak_r_new >= 1.80:
                banked_r = 0.40 * 1.80
                if peak_r_new >= trail_trig_r:
                    # Trailing continuation logic
                    runner_r = 0.60 * (peak_r_new - trail_dist_r)
                    r_mult = banked_r + runner_r
                    exit_reason = 'CONSENSUS_RUNNER'
                    exit_px = round(entry_px + (r_mult * init_sl) if direction == 'LONG' else entry_px - (r_mult * init_sl), 2)
                else:
                    tp2_cap = min(peak_r_new, 3.35)
                    r_mult = banked_r + 0.60 * (tp2_cap - 0.40)
                    exit_reason = 'TP'
                    exit_px = round(entry_px + (r_mult * init_sl) if direction == 'LONG' else entry_px - (r_mult * init_sl), 2)
            else:
                r_mult = max(cand['r_multiple'], -1.0)
                exit_px = cand['exit_price']

        total_pts = round(r_mult * init_sl, 2)
        gross_usd = round(total_pts * qty, 2)
        fees = round(fee_rate * (qty * entry_px + qty * exit_px), 2)
        net_usd = round(gross_usd - fees, 2)

        trade_dict = {
            'entry_ts': ts,
            'exit_ts': cand['exit_ts'],
            'direction': direction,
            'entry_price': entry_px,
            'exit_price': exit_px,
            'init_risk_pts': round(init_sl, 2),
            'r_multiple': round(r_mult, 2),
            'qty_oz': qty,
            'gross_pnl_usd': gross_usd,
            'delta_fee_usd': fees,
            'net_pnl_usd': net_usd,
            'exit_reason': exit_reason,
            'source_agent': cand['source_agent'],
            'day': day_str
        }
        active_trades.append(trade_dict)
        cooldown_ts = ts + cooldown_seconds

    for at in active_trades:
        net_p = at['net_pnl_usd']
        equity += net_p
        peak_equity = max(peak_equity, equity)
        cur_dd = (peak_equity - equity) / peak_equity * 100.0
        max_dd_pct = max(max_dd_pct, cur_dd)
        executed_trades.append(at)

    wins = [t for t in executed_trades if t['net_pnl_usd'] > 0]
    losses = [t for t in executed_trades if t['net_pnl_usd'] <= 0]
    gross_win = sum(t['net_pnl_usd'] for t in wins)
    gross_loss = abs(sum(t['net_pnl_usd'] for t in losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else 99.0
    wr = (len(wins) / len(executed_trades) * 100.0) if executed_trades else 0.0
    tot_net = sum(t['net_pnl_usd'] for t in executed_trades)

    return {
        'trades': len(executed_trades),
        'wr': wr,
        'net_pnl': tot_net,
        'end_equity': equity,
        'pf': pf,
        'max_dd': max_dd_pct,
        'calmar': (tot_net / 100.0) / (max_dd_pct / 100.0) if max_dd_pct > 0 else 0.0
    }

print(f"{'Profile Name':<48} | {'Trades':<6} | {'WR %':<6} | {'PF':<5} | {'Net PnL':<10} | {'End Eq':<10} | {'Max DD':<7} | {'Calmar':<6}")
print("=" * 115)

runs = [
    ("1. Champion B Baseline (No Circuit Breakers)", {}),
    ("2. DTS Option A: Session Analog Filter", {"session_analog_filter": True}),
    ("3. DTS Option B: Loss Dampener (Risk Halving)", {"consecutive_loss_dampener": True}),
    ("4. DTS Option C: Low-Drawdown Master (A + B)", {"session_analog_filter": True, "consecutive_loss_dampener": True}),
    ("5. DTS Option D: Tight Trail (Trail @ 2.1R, Dist 0.85R) + C", {"session_analog_filter": True, "consecutive_loss_dampener": True, "trail_trig_r": 2.10, "trail_dist_r": 0.85}),
    ("6. DTS Option E: Elite High-Expectancy (Daily Lock + C)", {"session_analog_filter": True, "consecutive_loss_dampener": True, "daily_loss_limit": -15.0}),
]

for name, params in runs:
    res = run_simulation(**params)
    print(f"{name:<48} | {res['trades']:<6} | {res['wr']:<6.2f}% | {res['pf']:<5.2f} | ${res['net_pnl']:<9.2f} | ${res['end_equity']:<9.2f} | -{res['max_dd']:<6.2f}% | {res['calmar']:<6.2f}")
