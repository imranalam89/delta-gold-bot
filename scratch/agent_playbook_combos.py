import json
import pandas as pd

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
df = pd.DataFrame(trades)
df['is_win'] = df['net_pnl_usd'] > 0

combos = df.groupby(['setup_agent', 'playbook']).agg(
    total=('id', 'count'),
    wins=('is_win', 'sum'),
    net=('net_pnl_usd', 'sum')
)
combos['wr'] = (combos['wins'] / combos['total'] * 100).round(1)
combos['losses'] = combos['total'] - combos['wins']
combos = combos.sort_values(by='losses', ascending=False)
print("=== AGENT + PLAYBOOK COMBINATIONS ===")
print(combos.to_string())
