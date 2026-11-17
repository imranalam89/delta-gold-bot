import json

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)

p1_trades = payload.get('trades', [])
print(f"Pillar 1 trades count: {len(p1_trades)}")

# Let's inspect script scripts/backtest_pillar_2_macro_breakout.py
with open('scripts/backtest_pillar_2_macro_breakout.py', 'r', encoding='utf-8') as f:
    script_text = f.read()

print("Script length:", len(script_text))
