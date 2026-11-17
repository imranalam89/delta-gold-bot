import json
from datetime import datetime, timezone

with open("data/processed/dashboard_payload.json", "r", encoding="utf-8") as f:
    d = json.load(f)

base_trades = d["profiles"]["MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL"]["trades"]

news_shield_trades = []
for t in base_trades:
    dt = datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc)
    # The News Shield condition:
    if dt.hour == 13 and t["setup_agent"] in ["5_COMBINED_1_2_3_MASTER", "MASTER_16_ACTIVE_FLOOR"]:
        news_shield_trades.append(t)

print(f"Total Trades Blocked by 13:00 UTC News Shield: {len(news_shield_trades)}")
wins = sum(1 for t in news_shield_trades if t["net_pnl_usd"] > 0)
losses = sum(1 for t in news_shield_trades if t["net_pnl_usd"] < 0)
net_saved = sum(t["net_pnl_usd"] for t in news_shield_trades)
print(f"Wins Blocked: {wins}, Losses Blocked: {losses}")
print(f"Net PnL of Blocked Trades: ${net_saved:+.2f}")
print("-" * 110)

for t in news_shield_trades:
    dt = datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc)
    t_id = t.get("id")
    ent_t = t.get("entry_time")
    direction = t.get("direction")
    agent = t.get("setup_agent")
    pb = t.get("playbook")
    net = t.get("net_pnl_usd")
    reason = t.get("exit_reason")
    r_m = t.get("r_multiple")
    print(f"Trade #{t_id:3d} | {ent_t} | {direction:5s} | {agent:24s} | {pb:22s} | Net: ${net:+6.2f} ({r_m:+.2f}R) | Exit: {reason}")
