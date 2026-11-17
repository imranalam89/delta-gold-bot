import json

with open("data/processed/all_11_agents_lab_bundle.json", "r", encoding="utf-8") as f:
    bundle = json.load(f)

a1_trades = bundle["1:ALEX"]["generations"]["v3.0_ORACLE_CHAMPION"]["trades"]
a2_trades = bundle["2:MAYA"]["generations"]["v3.0_ORACLE_CHAMPION"]["trades"]
a3_trades = bundle["3:MARCUS"]["generations"]["v3.0_ORACLE_CHAMPION"]["trades"]

combo = []
for t in a1_trades:
    tc = dict(t); tc["agent"] = "1:ALEX"; combo.append(tc)
for t in a2_trades:
    tc = dict(t); tc["agent"] = "2:MAYA"; combo.append(tc)
for t in a3_trades:
    tc = dict(t); tc["agent"] = "3:MARCUS"; combo.append(tc)

combo.sort(key=lambda x: (x["entry_ts"], -x["net_pnl"]))
print(f"Total raw trades from Agent 1, 2, 3: {len(combo)}")

# Test Max Slots = 1 (Strict non-overlapping), 2, and 3
for max_slots in [1, 2, 3]:
    active = []
    executed = []
    eq = 100.0
    peak = 100.0
    max_dd = 0.0

    for t in combo:
        ent = t["entry_ts"]
        ext = t["exit_ts"]
        active = [e for e in active if e > ent]
        if len(active) < max_slots:
            active.append(ext)
            executed.append(t)
            eq += t["net_pnl"]
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100.0
            if dd > max_dd:
                max_dd = dd

    n = len(executed)
    wins = sum(1 for t in executed if t["net_pnl"] > 0)
    wr = wins / n * 100.0 if n else 0
    net = sum(t["net_pnl"] for t in executed)
    gw = sum(t["net_pnl"] for t in executed if t["net_pnl"] > 0)
    gl = abs(sum(t["net_pnl"] for t in executed if t["net_pnl"] < 0))
    pf = gw / gl if gl > 0 else 9.99

    print(f"Agent 1 + 2 + 3 (Max Slots = {max_slots}):")
    print(f"  Trades: {n} ({n/110.0:.2f}/day)")
    print(f"  Win Rate: {wr:.2f}% ({wins}W / {n - wins}L)")
    print(f"  Profit Factor: {pf:.2f}")
    print(f"  Net PnL: ${net:+.2f}")
    print(f"  Ending Equity: ${eq:.2f} ({eq/100:.2f}X multiplier)")
    print(f"  Max Drawdown: -{max_dd:.2f}%")
    by_agent = {}
    for t in executed:
        by_agent[t["agent"]] = by_agent.get(t["agent"], 0) + 1
    print(f"  Trades by Agent: {by_agent}")
    print("-" * 50)
