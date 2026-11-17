import json

with open("data/processed/all_11_agents_2year_bundle.json", "r", encoding="utf-8") as f:
    bundle = json.load(f)

tot = 0
for aid, data in bundle.items():
    tf_data = data.get("timeframes", {})
    for tf, res in tf_data.items():
        n = res.get("trades_count", 0)
        tot += n
        wr = res.get("win_rate", 0)
        net = res.get("net_pnl", 0)
        print(f"{aid:10s} | {tf:3s} | {n:4d} trades | WR: {wr:5.1f}% | Net: ${net:+7.2f}")

print(f"\nTotal Specialist Trades across 2 Years: {tot:,}")
