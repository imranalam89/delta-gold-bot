import json

with open("data/processed/all_11_agents_lab_bundle.json", "r", encoding="utf-8") as f:
    bundle = json.load(f)

all_trades = []
for aid, data in bundle.items():
    g3_trades = data["generations"]["v3.0_ORACLE_CHAMPION"]["trades"]
    for t in g3_trades:
        t_copy = dict(t)
        t_copy["agent_id"] = aid
        all_trades.append(t_copy)

all_trades.sort(key=lambda x: x["entry_ts"])

for max_slots in [1, 2, 3, 4, 5]:
    active_positions = []
    executed = []
    for t in all_trades:
        ent = t["entry_ts"]
        ext = t["exit_ts"]
        active_positions = [e for e in active_positions if e > ent]
        if len(active_positions) < max_slots:
            active_positions.append(ext)
            executed.append(t)

    n = len(executed)
    wins = sum(1 for t in executed if t["net_pnl"] > 0)
    wr = wins / n * 100.0 if n else 0
    net = sum(t["net_pnl"] for t in executed)
    
    # Calculate equity curve with sequential trades
    eq = 100.0
    eq_curve = [eq]
    peak = 100.0
    max_dd = 0.0
    for t in executed:
        eq += t["net_pnl"]
        eq_curve.append(eq)
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100.0
        if dd > max_dd:
            max_dd = dd

    gw = sum(t["net_pnl"] for t in executed if t["net_pnl"] > 0)
    gl = abs(sum(t["net_pnl"] for t in executed if t["net_pnl"] < 0))
    pf = gw / gl if gl > 0 else 9.99

    print(f"Max Slots = {max_slots}:")
    print(f"  Trades: {n} ({n/110.0:.2f}/day)")
    print(f"  Win Rate: {wr:.2f}% ({wins}W / {n - wins}L)")
    print(f"  Profit Factor: {pf:.2f}")
    print(f"  Net PnL: ${net:+.2f}")
    print(f"  Ending Equity: ${eq:.2f} (Start $100 -> {eq/100:.2f}X multiplier)")
    print(f"  Max Drawdown: -{max_dd:.2f}%")
    print("-" * 50)
