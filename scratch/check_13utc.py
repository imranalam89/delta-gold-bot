import json
import pandas as pd

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
df = pd.DataFrame(trades)
df['entry_dt'] = pd.to_datetime(df['entry_ts'], unit='s', utc=True)
df['entry_hour'] = df['entry_dt'].dt.hour
df['entry_min'] = df['entry_dt'].dt.minute
df['is_win'] = df['net_pnl_usd'] > 0

h13 = df[df['entry_hour'] == 13]
print(f"Total trades at 13:00 UTC: {len(h13)}")
print(h13.groupby('setup_agent').agg(total=('id', 'count'), wins=('is_win', 'sum'), net=('net_pnl_usd', 'sum'), wr=('is_win', lambda x: round(x.mean()*100, 1))))

print("\nDetailed 13:00 UTC trades for 5_COMBINED:")
print(h13[h13['setup_agent'] == '5_COMBINED_1_2_3_MASTER'][['id', 'entry_time', 'direction', 'init_risk_pts', 'net_pnl_usd', 'exit_reason']].to_string())
