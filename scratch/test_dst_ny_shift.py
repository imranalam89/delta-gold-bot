import json
import pandas as pd
from datetime import datetime, timezone
import zoneinfo

with open("data/processed/dashboard_payload.json", "r", encoding="utf-8") as f:
    d = json.load(f)

base_trades = d["profiles"]["MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL"]["trades"]
# Filter out LEO_LIQUIDITY_TRAP first (Model 2 baseline without news shield)
model2_raw = [t for t in base_trades if t["playbook"] != "LEO_LIQUIDITY_TRAP"]

ny_tz = zoneinfo.ZoneInfo("America/New_York")

print(f"Total Base Trades (Pruned LEO_LIQUIDITY_TRAP): {len(model2_raw)}")

# Analyze trades by NY local hour and UTC hour
records = []
for t in model2_raw:
    dt_utc = datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc)
    dt_ny = dt_utc.astimezone(ny_tz)
    records.append({
        "id": t["id"],
        "entry_time": t["entry_time"],
        "utc_hour": dt_utc.hour,
        "ny_hour": dt_ny.hour,
        "ny_minute": dt_ny.minute,
        "dst": bool(dt_ny.dst()),
        "net_pnl": t["net_pnl_usd"],
        "setup_agent": t["setup_agent"],
        "playbook": t["playbook"],
        "exit_reason": t["exit_reason"]
    })

df = pd.DataFrame(records)

print("\n--- PERFORMANCE BY NY LOCAL HOUR ---")
for hr, sub in df.groupby("ny_hour"):
    w = (sub["net_pnl"] > 0).sum()
    net = sub["net_pnl"].sum()
    w_sum = sub[sub["net_pnl"] > 0]["net_pnl"].sum()
    l_sum = abs(sub[sub["net_pnl"] < 0]["net_pnl"].sum())
    pf = w_sum / l_sum if l_sum > 0 else 99.0
    print(f"NY Hour {hr:02d}:00: {len(sub):2d} Trades | WR: {w/len(sub)*100:5.1f}% ({w:2d}W / {len(sub)-w:2d}L) | Net: ${net:+7.2f} | PF: {pf:4.2f}")

print("\n--- PERFORMANCE BY UTC HOUR ---")
for hr, sub in df.groupby("utc_hour"):
    w = (sub["net_pnl"] > 0).sum()
    net = sub["net_pnl"].sum()
    w_sum = sub[sub["net_pnl"] > 0]["net_pnl"].sum()
    l_sum = abs(sub[sub["net_pnl"] < 0]["net_pnl"].sum())
    pf = w_sum / l_sum if l_sum > 0 else 99.0
    print(f"UTC Hour {hr:02d}:00: {len(sub):2d} Trades | WR: {w/len(sub)*100:5.1f}% ({w:2d}W / {len(sub)-w:2d}L) | Net: ${net:+7.2f} | PF: {pf:4.2f}")

# Now let's test different Shields:
def test_shield(name, condition_fn):
    remaining = [t for t in model2_raw if not condition_fn(t)]
    wins = sum(1 for t in remaining if t["net_pnl_usd"] > 0)
    tot = len(remaining)
    wr = wins / tot * 100
    net = sum(t["net_pnl_usd"] for t in remaining)
    w_sum = sum(t["net_pnl_usd"] for t in remaining if t["net_pnl_usd"] > 0)
    l_sum = abs(sum(t["net_pnl_usd"] for t in remaining if t["net_pnl_usd"] < 0))
    pf = w_sum / l_sum if l_sum > 0 else 99.0
    
    # Calculate Max DD
    eq = 100.0
    pk = 100.0
    max_dd = 0.0
    for t in remaining:
        eq += t["net_pnl_usd"]
        pk = max(pk, eq)
        dd = (pk - eq) / pk * 100.0 if pk > 0 else 0
        max_dd = max(max_dd, dd)
        
    print(f"{name:<45}: {tot} Trades | WR: {wr:.2f}% | Net: ${net:+.2f} | End Eq: ${100+net:.2f} | PF: {pf:.2f} | Max DD: {max_dd:.2f}%")

print("\n--- COMPARING DIFFERENT NEWS SHIELD IMPLEMENTATIONS ---")
# 0. Baseline (No News Shield)
test_shield("0. No News Shield (Pruned Leo Trap only)", lambda t: False)

# 1. Current Model 2 (Fixed UTC 13:00-13:59)
test_shield("1. Current Model 2 (UTC 13:00-13:59)", 
    lambda t: datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc).hour == 13 and t["setup_agent"] in ["5_COMBINED_1_2_3_MASTER", "MASTER_16_ACTIVE_FLOOR"])

# 2. Shift 1 Hour Later: Fixed UTC 14:00-14:59
test_shield("2. Shift 1hr Later in UTC (UTC 14:00-14:59)", 
    lambda t: datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc).hour == 14 and t["setup_agent"] in ["5_COMBINED_1_2_3_MASTER", "MASTER_16_ACTIVE_FLOOR"])

# 3. True NY Local Time 8:00 AM - 8:59 AM (Actual 8:30 AM Economic News Release)
test_shield("3. True NY Local 8:00 AM (8:30 News Release)", 
    lambda t: datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc).astimezone(ny_tz).hour == 8 and t["setup_agent"] in ["5_COMBINED_1_2_3_MASTER", "MASTER_16_ACTIVE_FLOOR"])

# 4. True NY Local Time 9:00 AM - 9:59 AM (9:30 AM NYSE / Comex Open - "1hr later")
test_shield("4. True NY Local 9:00 AM (9:30 Equity Open)", 
    lambda t: datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc).astimezone(ny_tz).hour == 9 and t["setup_agent"] in ["5_COMBINED_1_2_3_MASTER", "MASTER_16_ACTIVE_FLOOR"])

# 5. Dual NY Shield: 8:00 AM + 9:00 AM NY (Full Macro Opening Whipsaw Shield 8:00-9:59 AM)
test_shield("5. Full NY Open Shield (8:00 - 9:59 AM NY)", 
    lambda t: datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc).astimezone(ny_tz).hour in (8, 9) and t["setup_agent"] in ["5_COMBINED_1_2_3_MASTER", "MASTER_16_ACTIVE_FLOOR"])

# 6. Shift 1hr later for ALL agents at UTC 14:00
test_shield("6. Shift 1hr Later in UTC (All Agents UTC 14)", 
    lambda t: datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc).hour == 14)

# 7. True NY Local 8:30 News Shield (8:15 AM - 8:45 AM window)
test_shield("7. Precision News Release (8:15 - 8:45 AM NY)", 
    lambda t: (
        datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc).astimezone(ny_tz).hour == 8 
        and 15 <= datetime.fromtimestamp(t["entry_ts"], tz=timezone.utc).astimezone(ny_tz).minute <= 45
        and t["setup_agent"] in ["5_COMBINED_1_2_3_MASTER", "MASTER_16_ACTIVE_FLOOR"]
    ))
