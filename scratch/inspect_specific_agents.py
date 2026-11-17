import json
import pandas as pd

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
df = pd.DataFrame(trades)
df['is_win'] = df['net_pnl_usd'] > 0

m16 = df[df['setup_agent'] == 'MASTER_16_ACTIVE_FLOOR']
print("=== MASTER_16_ACTIVE_FLOOR (18 Trades) ===")
print(m16[['id', 'direction', 'session', 'day_of_week', 'consensus_score', 'confirming_count', 'adx_15m', 'chop_15m', 'atr_15m', 'net_pnl_usd', 'exit_reason']].to_string())

comb = df[df['setup_agent'] == '5_COMBINED_1_2_3_MASTER']
print("\n=== 5_COMBINED_1_2_3_MASTER (104 Trades) ===")
print("Session breakdown for 5_COMBINED:")
print(comb.groupby('session').agg(total=('id', 'count'), wins=('is_win', 'sum'), net=('net_pnl_usd', 'sum'), wr=('is_win', lambda x: round(x.mean()*100, 1))))

print("\nHour breakdown for 5_COMBINED:")
comb['entry_hour'] = pd.to_datetime(comb['entry_ts'], unit='s', utc=True).dt.hour
print(comb.groupby('entry_hour').agg(total=('id', 'count'), wins=('is_win', 'sum'), net=('net_pnl_usd', 'sum'), wr=('is_win', lambda x: round(x.mean()*100, 1))))
