import json
import pandas as pd

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
df = pd.DataFrame(trades)
df['entry_dt'] = pd.to_datetime(df['entry_ts'], unit='s', utc=True)
df['entry_hour'] = df['entry_dt'].dt.hour
df['is_win'] = df['net_pnl_usd'] > 0

# Baseline
def calc_metrics(sub, name):
    wins = sub['is_win'].sum()
    total = len(sub)
    losses = total - wins
    wr = wins / total * 100
    net = sub['net_pnl_usd'].sum()
    win_sum = sub[sub['is_win']]['net_pnl_usd'].sum()
    loss_sum = abs(sub[~sub['is_win']]['net_pnl_usd'].sum())
    pf = win_sum / loss_sum if loss_sum > 0 else 99
    
    sub_sorted = sub.sort_values(by='exit_ts')
    eq = 100.0
    peak = 100.0
    max_dd = 0.0
    for pnl in sub_sorted['net_pnl_usd']:
        eq += pnl
        peak = max(peak, eq)
        dd = (peak - eq) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)
        
    print(f"[{name}]")
    print(f"  Trades: {total} | Wins: {wins} | Losses: {losses} | WR: {wr:.2f}%")
    print(f"  Net PnL: ${net:.2f} | Ending Eq: ${100+net:.2f} ({(100+net)/100:.2f}X)")
    print(f"  PF: {pf:.2f} | Max DD: {max_dd:.2f}%\n")

calc_metrics(df, "Baseline")

# 1. Skip 5_COMBINED and MASTER_16 at hour 13 UTC
f1 = df[~((df['entry_hour'] == 13) & (df['setup_agent'].isin(['5_COMBINED_1_2_3_MASTER', 'MASTER_16_ACTIVE_FLOOR'])))]
calc_metrics(f1, "Filter: Skip 5_COMBINED & MASTER_16 at 13 UTC (News Whipsaw Avoidance)")

# 2. Skip LEO_LIQUIDITY_TRAP playbook
f2 = df[df['playbook'] != 'LEO_LIQUIDITY_TRAP']
calc_metrics(f2, "Filter: Skip LEO_LIQUIDITY_TRAP")

# 3. Combine both:
f3 = df[
    (df['playbook'] != 'LEO_LIQUIDITY_TRAP') &
    ~((df['entry_hour'] == 13) & (df['setup_agent'].isin(['5_COMBINED_1_2_3_MASTER', 'MASTER_16_ACTIVE_FLOOR'])))
]
calc_metrics(f3, "Filter: Skip LEO_LIQUIDITY_TRAP + Skip News Whipsaw at 13 UTC")

# 4. What about toxic agents (POD_MAYA_SAM, 2:MAYA, 9:SAM)?
f4 = df[
    ~df['setup_agent'].isin(['POD_MAYA_SAM', '2:MAYA', '9:SAM']) &
    ~((df['entry_hour'] == 13) & (df['setup_agent'].isin(['5_COMBINED_1_2_3_MASTER', 'MASTER_16_ACTIVE_FLOOR'])))
]
calc_metrics(f4, "Filter: Skip Toxic Agents + Skip News Whipsaw at 13 UTC")

# 5. What if we also prune Hour 23 UTC chop on 5_COMBINED? Or hour 23 altogether?
f5 = df[
    (df['playbook'] != 'LEO_LIQUIDITY_TRAP') &
    ~((df['entry_hour'] == 13) & (df['setup_agent'].isin(['5_COMBINED_1_2_3_MASTER', 'MASTER_16_ACTIVE_FLOOR']))) &
    (df['entry_hour'] != 23)
]
calc_metrics(f5, "Filter: Skip LEO_LIQUIDITY_TRAP + News Whipsaw 13 UTC + Rollover 23 UTC")
