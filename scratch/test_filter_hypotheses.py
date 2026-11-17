import json
import pandas as pd
import numpy as np

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
df = pd.DataFrame(trades)

df['entry_dt'] = pd.to_datetime(df['entry_ts'], unit='s', utc=True)
df['entry_hour'] = df['entry_dt'].dt.hour
df['is_win'] = df['net_pnl_usd'] > 0

def evaluate_subset(sub, name=""):
    n_trades = len(sub)
    if n_trades == 0:
        print(f"{name}: 0 trades")
        return
    wins = sub['is_win'].sum()
    losses = n_trades - wins
    wr = wins / n_trades * 100
    net_pnl = sub['net_pnl_usd'].sum()
    
    # Calculate equity curve & drawdown
    sub_sorted = sub.sort_values(by='exit_ts')
    eq = 100.0
    peak = 100.0
    max_dd = 0.0
    for pnl in sub_sorted['net_pnl_usd']:
        eq += pnl
        peak = max(peak, eq)
        dd = (peak - eq) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)
        
    win_sum = sub[sub['net_pnl_usd'] > 0]['net_pnl_usd'].sum()
    loss_sum = abs(sub[sub['net_pnl_usd'] < 0]['net_pnl_usd'].sum())
    pf = win_sum / loss_sum if loss_sum > 0 else 99.0
    
    print(f"[{name}]")
    print(f"  Trades: {n_trades} | Wins: {wins} | Losses: {losses} | WR: {wr:.2f}%")
    print(f"  Net PnL: ${net_pnl:.2f} | Ending Eq: ${100+net_pnl:.2f} ({(100+net_pnl)/100:.2f}X)")
    print(f"  PF: {pf:.2f} | Max DD: {max_dd:.2f}%\n")
    return {'name': name, 'trades': n_trades, 'wr': wr, 'net_pnl': net_pnl, 'pf': pf, 'max_dd': max_dd, 'losses_skipped': 99 - losses}

print("=== BASELINE CHAMPION ===")
evaluate_subset(df, "Baseline Champion (MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL)")

# HYPOTHESIS 1: Filter out LEO_LIQUIDITY_TRAP (40.9% WR, +$2.09 net)
h1 = df[df['playbook'] != 'LEO_LIQUIDITY_TRAP']
evaluate_subset(h1, "Filter 1: Skip 'LEO_LIQUIDITY_TRAP'")

# HYPOTHESIS 2: Filter out toxic setup agents (POD_MAYA_SAM, 2:MAYA, 9:SAM)
toxic_agents = ['POD_MAYA_SAM', '2:MAYA', '9:SAM']
h2 = df[~df['setup_agent'].isin(toxic_agents)]
evaluate_subset(h2, "Filter 2: Skip 'POD_MAYA_SAM', '2:MAYA', '9:SAM'")

# HYPOTHESIS 3: Filter out 23:00 UTC rollover hour (50% WR, +$4.25 across 20 trades)
h3 = df[df['entry_hour'] != 23]
evaluate_subset(h3, "Filter 3: Skip Hour 23 UTC (Rollover dead zone)")

# HYPOTHESIS 4: Filter out low ADX chop (e.g. adx_15m < 5.0 or chop_15m > 60)
h4 = df[df['adx_15m'] >= 5.0]
evaluate_subset(h4, "Filter 4: Minimum ADX >= 5.0 (Skip dead chop)")

# HYPOTHESIS 5: Combine Filter 1 (Skip LEO_LIQUIDITY_TRAP) + Filter 3 (Skip Hour 23)
h5 = df[(df['playbook'] != 'LEO_LIQUIDITY_TRAP') & (df['entry_hour'] != 23)]
evaluate_subset(h5, "Filter 5: Skip 'LEO_LIQUIDITY_TRAP' + Skip Hour 23 UTC")

# HYPOTHESIS 6: Combine Filter 1 (Skip LEO_LIQUIDITY_TRAP) + Filter 2 (Toxic Agents)
h6 = df[(df['playbook'] != 'LEO_LIQUIDITY_TRAP') & (~df['setup_agent'].isin(toxic_agents))]
evaluate_subset(h6, "Filter 6: Skip LEO_LIQUIDITY_TRAP + Skip Toxic Agents")

# HYPOTHESIS 7: Triple Quality Prune:
# Skip LEO_LIQUIDITY_TRAP + Skip Hour 23 + Skip Toxic Agents
h7 = df[(df['playbook'] != 'LEO_LIQUIDITY_TRAP') & (df['entry_hour'] != 23) & (~df['setup_agent'].isin(toxic_agents))]
evaluate_subset(h7, "Filter 7: Elite Prune (Skip LEO_LIQUIDITY_TRAP + Skip Hour 23 + Skip Toxic Agents)")
