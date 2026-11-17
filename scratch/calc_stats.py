import sys, json, math
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

p = d['profiles']['MUX_085SL_40R_CONTINUOUS_TRAIL']
trades = p['trades']
df = pd.DataFrame(trades)

print('=== CORE METRICS ===')
print('Total Trades:', len(df))
print('Total Net PnL: $', round(df['net_pnl_usd'].sum(), 2))
print('Total Gross PnL: $', round(df['gross_pnl_usd'].sum(), 2))
print('Total Fees: $', round(df['delta_fee_usd'].sum(), 2))
wins = df[df['net_pnl_usd'] > 0]
losses = df[df['net_pnl_usd'] < 0]
print(f"Win Count: {len(wins)} ({len(wins)/len(df)*100:.2f}%)")
print(f"Loss Count: {len(losses)} ({len(losses)/len(df)*100:.2f}%)")
print(f"Avg Win: ${wins['net_pnl_usd'].mean():.2f} ({wins['r_multiple'].mean():.2f}R)")
print(f"Avg Loss: ${losses['net_pnl_usd'].mean():.2f} ({losses['r_multiple'].mean():.2f}R)")
print(f"Win/Loss Ratio: {abs(wins['net_pnl_usd'].mean() / losses['net_pnl_usd'].mean()):.2f}")
gross_win = wins['gross_pnl_usd'].sum()
gross_loss = abs(losses['gross_pnl_usd'].sum())
print(f"Profit Factor: {gross_win / gross_loss:.2f}")

# Streaks
cur_streak = 0
max_win_streak = 0
max_loss_streak = 0
cur_type = None
for pnl in df['net_pnl_usd']:
    if pnl > 0:
        if cur_type == 'W':
            cur_streak += 1
        else:
            cur_streak = 1
            cur_type = 'W'
        max_win_streak = max(max_win_streak, cur_streak)
    else:
        if cur_type == 'L':
            cur_streak += 1
        else:
            cur_streak = 1
            cur_type = 'L'
        max_loss_streak = max(max_loss_streak, cur_streak)

print(f"Max Consecutive Wins: {max_win_streak}")
print(f"Max Consecutive Losses: {max_loss_streak}")

# Holding time
print(f"Avg Hold Time: {df['hold_mins'].mean():.1f} mins (Median: {df['hold_mins'].median():.0f}m, Max: {df['hold_mins'].max()}m)")

# Daily Stats
daily = df.groupby('date').agg(net=('net_pnl_usd', 'sum'), trades=('id', 'count'), wr=('net_pnl_usd', lambda x: (x>0).mean()*100))
print(f"Active Trading Days: {len(daily)}")
print(f"Profitable Days: {len(daily[daily['net'] > 0])} ({len(daily[daily['net'] > 0])/len(daily)*100:.1f}%)")
print(f"Losing Days: {len(daily[daily['net'] < 0])} ({len(daily[daily['net'] < 0])/len(daily)*100:.1f}%)")
print(f"Best Day: {daily['net'].idxmax()} (+${daily['net'].max():.2f}, {daily.loc[daily['net'].idxmax(), 'trades']} trades)")
print(f"Worst Day: {daily['net'].idxmin()} (-${abs(daily['net'].min()):.2f}, {daily.loc[daily['net'].idxmin(), 'trades']} trades)")

print('\n=== MONTHLY STATS ===')
for m, grp in df.groupby('month'):
    m_wins = grp[grp['net_pnl_usd'] > 0]
    print(f"{m}: {len(grp)} trades, WR: {len(m_wins)/len(grp)*100:.1f}%, Net: ${grp['net_pnl_usd'].sum():.2f}, Fees: ${grp['delta_fee_usd'].sum():.2f}")

print('\n=== SESSION STATS ===')
for s, grp in df.groupby('session'):
    s_wins = grp[grp['net_pnl_usd'] > 0]
    print(f"{s}: {len(grp)} trades, WR: {len(s_wins)/len(grp)*100:.1f}%, Net: ${grp['net_pnl_usd'].sum():.2f}")

print('\n=== DIRECTION STATS ===')
for d_dir, grp in df.groupby('direction'):
    d_wins = grp[grp['net_pnl_usd'] > 0]
    print(f"{d_dir}: {len(grp)} trades, WR: {len(d_wins)/len(grp)*100:.1f}%, Net: ${grp['net_pnl_usd'].sum():.2f}")

print('\n=== DAY OF WEEK ===')
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
for day in days:
    grp = df[df['day_of_week'] == day]
    if len(grp):
        d_wins = grp[grp['net_pnl_usd'] > 0]
        print(f"{day}: {len(grp)} trades, WR: {len(d_wins)/len(grp)*100:.1f}%, Net: ${grp['net_pnl_usd'].sum():.2f}")

print('\n=== TOP 10 PLAYBOOKS ===')
pb = df.groupby('playbook').agg(count=('id', 'count'), wr=('net_pnl_usd', lambda x: (x>0).mean()*100), net=('net_pnl_usd', 'sum')).sort_values('net', ascending=False)
print(pb.head(10).to_string())

print('\n=== EXIT REASONS ===')
er = df.groupby('exit_reason').agg(count=('id', 'count'), wr=('net_pnl_usd', lambda x: (x>0).mean()*100), net=('net_pnl_usd', 'sum')).sort_values('count', ascending=False)
print(er.to_string())
