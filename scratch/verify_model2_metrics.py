import json
import pandas as pd
from datetime import datetime, timezone

PAYLOAD_PATH = "data/processed/dashboard_payload.json"
with open(PAYLOAD_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

base_profile = data["profiles"]["MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL"]
base_trades = base_profile["trades"]
print(f"Base Trades count: {len(base_trades)}")

filtered_trades = []
for t in base_trades:
    # 1. Prune LEO_LIQUIDITY_TRAP
    if t["playbook"] == "LEO_LIQUIDITY_TRAP":
        continue
    # 2. News Whipsaw Shield at 13:00 UTC
    entry_dt = datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc)
    if entry_dt.hour == 13 and t["setup_agent"] in ["5_COMBINED_1_2_3_MASTER", "MASTER_16_ACTIVE_FLOOR"]:
        continue
    filtered_trades.append(dict(t))

print(f"Filtered Model 2 Trades count: {len(filtered_trades)}")

# Sort chronologically by entry_ts
filtered_trades.sort(key=lambda x: x["entry_ts"])

# Recompute running equity and re-index trade IDs
equity = 100.0
peak_equity = 100.0
max_dd_usd = 0.0
max_dd_pct = 0.0

wins = 0
win_pnl = 0.0
loss_pnl = 0.0

is_trades = []
oos_trades = []

for idx, t in enumerate(filtered_trades, 1):
    t["orig_id"] = t["id"]
    t["id"] = idx
    pnl = t["net_pnl_usd"]
    equity += pnl
    t["equity_after"] = round(equity, 2)
    
    if equity > peak_equity:
        peak_equity = equity
    dd_usd = peak_equity - equity
    dd_pct = (dd_usd / peak_equity * 100.0) if peak_equity > 0 else 0.0
    if dd_usd > max_dd_usd:
        max_dd_usd = dd_usd
    if dd_pct > max_dd_pct:
        max_dd_pct = dd_pct
        
    if pnl > 0:
        wins += 1
        win_pnl += pnl
    else:
        loss_pnl += abs(pnl)
        
    if t.get("is_oos", False):
        oos_trades.append(t)
    else:
        is_trades.append(t)

tot_trades = len(filtered_trades)
wr = (wins / tot_trades * 100.0) if tot_trades > 0 else 0.0
net_pnl = equity - 100.0
pf = (win_pnl / loss_pnl) if loss_pnl > 0 else 99.0

print(f"Total Trades: {tot_trades}")
print(f"Wins: {wins} | Losses: {tot_trades - wins}")
print(f"Win Rate: {wr:.2f}%")
print(f"Net Profit: +${net_pnl:.2f}")
print(f"Ending Equity: ${equity:.2f} ({equity/100:.2f}X Multiplier)")
print(f"Profit Factor: {pf:.2f} PF")
print(f"Max Drawdown: {max_dd_pct:.2f}% (${max_dd_usd:.2f})")

is_wins = sum(1 for t in is_trades if t['net_pnl_usd'] > 0)
oos_wins = sum(1 for t in oos_trades if t['net_pnl_usd'] > 0)
is_net = sum(t['net_pnl_usd'] for t in is_trades)
oos_net = sum(t['net_pnl_usd'] for t in oos_trades)
is_pf = sum(t['net_pnl_usd'] for t in is_trades if t['net_pnl_usd'] > 0) / max(0.01, abs(sum(t['net_pnl_usd'] for t in is_trades if t['net_pnl_usd'] < 0)))
oos_pf = sum(t['net_pnl_usd'] for t in oos_trades if t['net_pnl_usd'] > 0) / max(0.01, abs(sum(t['net_pnl_usd'] for t in oos_trades if t['net_pnl_usd'] < 0)))

print(f"\nIn-Sample (IS): {len(is_trades)} Trades | WR: {is_wins/len(is_trades)*100:.2f}% | Net: +${is_net:.2f} | PF: {is_pf:.2f}")
print(f"Out-of-Sample (OOS): {len(oos_trades)} Trades | WR: {oos_wins/len(oos_trades)*100:.2f}% | Net: +${oos_net:.2f} | PF: {oos_pf:.2f}")
