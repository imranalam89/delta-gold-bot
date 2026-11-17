import pandas as pd
import json

p1 = pd.read_csv('data/processed/trades_1_ULTRA_CADENCE_574_TRADES_DUAL_SLOT.csv')
p2 = pd.read_csv('data/processed/trades_2_HIGH_FREQUENCY_847_TRADES_TRI_SLOT.csv')
p3 = pd.read_csv('data/processed/trades_3_SCALPER_DENSITY_1115_TRADES_QUAD_SLOT.csv')

print(f"p1 count: {len(p1)}")
print(f"p2 count: {len(p2)}")
print(f"p3 count: {len(p3)}")

# Check how many trades in p1 are in p2
p1_keys = set(zip(p1['entry_time'], p1['setup_agent'], p1['direction']))
p2_keys = set(zip(p2['entry_time'], p2['setup_agent'], p2['direction']))
p3_keys = set(zip(p3['entry_time'], p3['setup_agent'], p3['direction']))

print(f"p1 keys: {len(p1_keys)}")
print(f"p2 keys: {len(p2_keys)}")
print(f"p3 keys: {len(p3_keys)}")
print(f"p1 in p2: {len(p1_keys.intersection(p2_keys))} of {len(p1_keys)}")
print(f"p2 in p3: {len(p2_keys.intersection(p3_keys))} of {len(p2_keys)}")
print(f"Total unique trades across p1, p2, p3: {len(p1_keys.union(p2_keys).union(p3_keys))}")
