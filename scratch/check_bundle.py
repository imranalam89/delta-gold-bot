import json

with open("data/processed/all_11_agents_lab_bundle.json", "r", encoding="utf-8") as f:
    bundle = json.load(f)

print(f"Total agents in bundle: {len(bundle)}")
for aid, data in bundle.items():
    g3 = data["generations"]["v3.0_ORACLE_CHAMPION"]
    print(f"Agent {aid} ({data['agent_role']}): {g3['trades_count']} trades, {g3['win_rate']:.1f}% WR, Net: ${g3['net_pnl']:+.2f}, End Eq: ${g3['end_equity']:.2f}")
