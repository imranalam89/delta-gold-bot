import json
import os
import pandas as pd

with open('data/processed/all_11_agents_lab_bundle.json', 'r', encoding='utf-8') as f:
    bundle = json.load(f)

print("Agents in lab bundle:", list(bundle.keys()))
for ag in list(bundle.keys())[:3]:
    tfs = bundle[ag].get('timeframes', {})
    print(f"Agent {ag}: timeframes = {list(tfs.keys())}")
    for tf, d in tfs.items():
        print(f"   {tf}: {len(d.get('trades', []))} trades")
