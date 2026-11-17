import json
import numpy as np
from collections import defaultdict
from datetime import datetime, timezone

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
print(f"Loaded {len(trades)} trades.")

# Inspect the fields in each trade
sample = trades[0]
print("Trade fields:", list(sample.keys()))

wins = [t for t in trades if t['net_pnl_usd'] > 0]
losses = [t for t in trades if t['net_pnl_usd'] < 0]

print(f"Wins: {len(wins)}, Losses: {len(losses)}")
