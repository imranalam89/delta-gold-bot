import json
import os
import sys
import numpy as np

# Load the 11 specialists bundle
print("[OPTIMIZER] Loading all 11 agents lab bundle...")
with open('data/processed/all_11_agents_lab_bundle.json', 'r') as f:
    bundle = json.load(f)

# Extract trades from all 11 agents
# Identify whether each agent is a SNIPER (Price Action / Order Flow) or STRUCTURAL (Trend / Breakout)
SNIPER_AGENTS = {'2:MAYA', '8:ELENA', '9:SAM', '11:LIAM', '4:NINA'}
STRUCTURAL_AGENTS = {'1:ALEX', '3:MARCUS', '5:MAX', '6:SOPHIA', '7:DEREK', '10:OMAR'}

all_agent_trades = []
for ag, data in bundle.items():
    champ = data.get('generations', {}).get('v3.0_ORACLE_CHAMPION', {})
    trades = champ.get('trades', [])
    for t in trades:
        t_copy = dict(t)
        t_copy['source_agent'] = ag
        t_copy['is_sniper'] = (ag in SNIPER_AGENTS)
        all_agent_trades.append(t_copy)

# Sort all candidate signals chronologically
all_agent_trades.sort(key=lambda x: (x['entry_ts'], -x.get('net_pnl', 0)))
print(f"[OPTIMIZER] Total candidate specialist trades across 11 agents: {len(all_agent_trades)}")

# Multi-Agent Simulation Function
def simulate_combination(
    sniper_sl_pts,       # e.g., 2.80, 3.50, 4.20
    struct_sl_mult,      # e.g., 1.25, 1.45, 1.65
    be_trig_r,           # e.g., 1.10, 1.35
    be_lock_r,           # e.g., 0.35, 0.45
    trail_trig_r,        # e.g., 2.10, 2.50
    trail_dist_r,        # e.g., 1.05, 1.25
    use_reversal_exit,   # True / False
    consensus_continuation, # True / False (if True, trail TP to 6R+ when high confidence)
    max_slots=1,         # 1 position at a time (low DD) vs 2 positions
    fee_rate=0.0001
):
    equity = 100.0
    peak_equity = 100.0
    max_dd_pct = 0.0

    active_trades = []
    executed_trades = []
    cooldown_ts = 0

    for cand in all_agent_trades:
        ts = cand['entry_ts']

        # 1. Update and expire currently active trades
        remaining_active = []
        for at in active_trades:
            # Check if this trade is already closed before current candidate entry
            if at['exit_ts'] <= ts:
                # Trade finished naturally
                equity += at['net_pnl']
                peak_equity = max(peak_equity, equity)
                cur_dd = (peak_equity - equity) / peak_equity * 100.0
                max_dd_pct = max(max_dd_pct, cur_dd)
                executed_trades.append(at)
            else:
                # Check for REVERSAL EXIT: Opposing signal arrives while in trade
                if use_reversal_exit and cand['direction'] != at['direction'] and ts < at['exit_ts']:
                    # Exit early at market price of the reversal candle
                    rev_exit_px = cand['entry_price']
                    entry_px = at['entry_price']
                    init_rk = at['init_sl']
                    qty = 5.0 / init_rk

                    if at['direction'] == 'LONG':
                        pts = rev_exit_px - entry_px
                    else:
                        pts = entry_px - rev_exit_px

                    # Cap loss or retain banked profit
                    early_r = pts / init_rk
                    # If trade had reached partial TP, retain banked portion
                    if at['peak_r'] >= 1.80:
                        adj_pts = 0.50 * 1.80 * init_rk + 0.50 * pts
                    else:
                        adj_pts = max(pts, -init_rk)

                    gross = adj_pts * qty
                    fees = fee_rate * (qty * entry_px + qty * rev_exit_px)
                    net = gross - fees
                    at['net_pnl'] = net
                    at['exit_reason'] = 'REVERSAL_EXIT'
                    at['exit_ts'] = ts

                    equity += net
                    peak_equity = max(peak_equity, equity)
                    cur_dd = (peak_equity - equity) / peak_equity * 100.0
                    max_dd_pct = max(max_dd_pct, cur_dd)
                    executed_trades.append(at)
                else:
                    remaining_active.append(at)

        active_trades = remaining_active

        # 2. Check if we can enter a new trade
        if len(active_trades) >= max_slots:
            continue
        if ts < cooldown_ts:
            continue

        # 3. Size and configure new trade based on agent type (Sniper vs Structural)
        is_sniper = cand['is_sniper']
        orig_sl_dist = cand['sl_dist']
        entry_px = cand['entry_price']

        if is_sniper:
            # Dynamic Sniper SL: tight fixed bounds ($2.50 to $3.50)
            init_sl = min(sniper_sl_pts, orig_sl_dist)
        else:
            # Dynamic Structural SL: proportional to ATR
            init_sl = min(struct_sl_mult * (orig_sl_dist / 1.35), 8.5)

        init_sl = max(init_sl, 2.0) # floor at $2.00 to prevent spread whipsaw
        qty = 5.0 / init_sl
        peak_mfe = cand['peak_r'] * orig_sl_dist
        peak_r_new = peak_mfe / init_sl

        # Calculate outcome with dynamic SL, Trailing, and TP continuation
        r_mult = 0.0
        exit_reason = cand['exit_reason']

        # Did it get stopped out?
        if cand['exit_reason'] == 'SL':
            r_mult = -1.0
            exit_reason = 'SL'
        else:
            # Smart Stall Lock / Breakeven Lock
            if peak_r_new >= be_trig_r:
                r_mult = be_lock_r
                exit_reason = 'BE_LOCK'

            # TP1 reached (Bank 40%)
            if peak_r_new >= 1.80:
                banked_r = 0.40 * 1.80 # 0.72R
                rem_r = 0.60 * min(peak_r_new - trail_dist_r, peak_r_new)

                if consensus_continuation and peak_r_new >= trail_trig_r:
                    # Consensus continuation: trail runner up to 80% of peak (capturing $20 - $50+ moves)
                    runner_r = 0.60 * (0.80 * peak_r_new)
                    r_mult = banked_r + runner_r
                    exit_reason = 'CONSENSUS_RUNNER'
                else:
                    # Standard TP2 cap at 3.35R
                    tp2_cap_r = min(peak_r_new, 3.35)
                    r_mult = banked_r + 0.60 * (tp2_cap_r - 0.40)
                    exit_reason = 'TP'
            else:
                r_mult = max(cand['r_multiple'], -1.0)

        total_pts = r_mult * init_sl
        gross_usd = total_pts * qty
        fee_usd = fee_rate * (qty * entry_px * 2)
        net_usd = gross_usd - fee_usd

        trade_record = {
            'agent': cand['source_agent'],
            'entry_ts': ts,
            'exit_ts': cand['exit_ts'],
            'direction': cand['direction'],
            'entry_price': entry_px,
            'init_sl': init_sl,
            'is_sniper': is_sniper,
            'peak_r': peak_r_new,
            'peak_pts': peak_mfe,
            'r_mult': r_mult,
            'net_pnl': net_usd,
            'exit_reason': exit_reason,
            'win': net_usd > 0
        }
        active_trades.append(trade_record)
        cooldown_ts = ts + 8 * 60 # 8 min cooldown between entries

    # Flush remaining active trades at end
    for at in active_trades:
        equity += at['net_pnl']
        peak_equity = max(peak_equity, equity)
        cur_dd = (peak_equity - equity) / peak_equity * 100.0
        max_dd_pct = max(max_dd_pct, cur_dd)
        executed_trades.append(at)

    wins = [t for t in executed_trades if t['win']]
    losses = [t for t in executed_trades if not t['win']]
    wr = len(wins) / max(len(executed_trades), 1) * 100.0
    tot_net = sum(t['net_pnl'] for t in executed_trades)
    gross_w = sum(t['net_pnl'] for t in wins)
    gross_l = abs(sum(t['net_pnl'] for t in losses))
    pf = (gross_w / gross_l) if gross_l > 0 else 999.0

    return {
        'trades_count': len(executed_trades),
        'win_rate': wr,
        'net_pnl': tot_net,
        'profit_factor': pf,
        'max_dd_pct': max_dd_pct,
        'end_equity': equity,
        'trades': executed_trades
    }

# -------------------------------------------------------------
# RUN 100+ COMBINATIONS GRID SEARCH
# -------------------------------------------------------------
print("[GRID SEARCH] Running 288 Multi-Agent Parameter Combinations...")

sniper_sl_list = [2.50, 3.00, 3.80]
struct_sl_list = [1.25, 1.45, 1.65]
be_trig_list = [1.05, 1.25, 1.45]
trail_trig_list = [2.10, 2.50]
reversal_exit_list = [True, False]
consensus_continuation_list = [True, False]
slots_list = [1, 2] # 1 slot for ultra-low drawdown, 2 slots for higher density

combos = []
combo_id = 0

for sn_sl in sniper_sl_list:
    for st_sl in struct_sl_list:
        for be_tr in be_trig_list:
            for tr_tr in trail_trig_list:
                for rev_ex in reversal_exit_list:
                    for cons_cont in consensus_continuation_list:
                        for slots in slots_list:
                            combo_id += 1
                            res = simulate_combination(
                                sniper_sl_pts=sn_sl,
                                struct_sl_mult=st_sl,
                                be_trig_r=be_tr,
                                be_lock_r=0.38,
                                trail_trig_r=tr_tr,
                                trail_dist_r=1.05,
                                use_reversal_exit=rev_ex,
                                consensus_continuation=cons_cont,
                                max_slots=slots
                            )
                            # Composite Score prioritizing: High Win Rate (weight 0.4), Low DD (weight 0.4), Net PnL (weight 0.2)
                            # Penalize DD heavily
                            score = (res['win_rate'] * 2.0) + (res['net_pnl'] * 0.5) - (res['max_dd_pct'] * 4.0)

                            combos.append({
                                'id': combo_id,
                                'sn_sl': sn_sl,
                                'st_sl': st_sl,
                                'be_tr': be_tr,
                                'tr_tr': tr_tr,
                                'rev_ex': rev_ex,
                                'cons_cont': cons_cont,
                                'slots': slots,
                                'trades': res['trades_count'],
                                'wr': res['win_rate'],
                                'net': res['net_pnl'],
                                'pf': res['profit_factor'],
                                'dd': res['max_dd_pct'],
                                'score': score,
                                'sample_trades': res['trades']
                            })

print(f"[GRID SEARCH] Completed {len(combos)} combinations backtest across 5-month dataset!")

# Sort by Composite Score
combos.sort(key=lambda x: x['score'], reverse=True)

# Save summary to CSV
out_csv = 'data/processed/multi_agent_100_combos_results.csv'
with open(out_csv, 'w') as f:
    f.write("Rank,ID,SniperSL,StructSL,BE_Trig,TrailTrig,ReversalExit,ConsensusTrail,Slots,Trades,WinRate,NetProfit,ProfitFactor,MaxDD,Score\n")
    for r, c in enumerate(combos, 1):
        f.write(f"{r},{c['id']},{c['sn_sl']},{c['st_sl']},{c['be_tr']},{c['tr_tr']},{c['rev_ex']},{c['cons_cont']},{c['slots']},{c['trades']},{c['wr']:.2f},{c['net']:.2f},{c['pf']:.2f},{c['dd']:.2f},{c['score']:.2f}\n")

print(f"[GRID SEARCH] Results saved to {out_csv}")

print("\n" + "="*80)
print("  TOP 5 HIGHEST PERFORMING MULTI-AGENT SETTINGS (HIGH WINRATE + LOW DRAWDOWN)")
print("="*80)
for r, c in enumerate(combos[:5], 1):
    print(f"Rank {r}: Combo #{c['id']:03d} | Slots: {c['slots']} | Sniper SL: ${c['sn_sl']} | Struct SL Mult: {c['st_sl']}x")
    print(f"        Settings: BE Trig={c['be_tr']}R | Trail Trig={c['tr_tr']}R | RevExit={c['rev_ex']} | 70% Consensus Trail={c['cons_cont']}")
    print(f"        METRICS:  Win Rate: {c['wr']:.2f}% | Net Profit: +${c['net']:.2f} | Profit Factor: {c['pf']:.2f} | Max DD: {c['dd']:.2f}% | Score: {c['score']:.1f}")
    print("-" * 80)
