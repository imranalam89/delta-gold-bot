import json
import os
import numpy as np
import pandas as pd

# Load lab bundle to construct accurate trust weights
BASE_DIR = r"c:\Users\USER\OneDrive\Desktop\Agents Team"
BUNDLE_PATH = os.path.join(BASE_DIR, "data", "processed", "all_11_agents_lab_bundle.json")
OUT_WEIGHTS = os.path.join(BASE_DIR, "data", "processed", "agent_trust_weights.json")

with open(BUNDLE_PATH, "r", encoding="utf-8") as f:
    bundle = json.load(f)

# Name mapping between bundle IDs and backtest_runner voter tags
# Bundle: 1:ALEX, 2:MAYA, 3:MARCUS, 4:NINA, 5:MAX, 6:SOPHIA, 7:DEREK, 8:ELENA, 9:SAM, 10:OMAR, 11:LIAM
# Runner voters: 1:CLARA, 2:ARTHUR, 3:MARCUS, 4:NINA, 5:MAX, 6:LEO, 7:KAI, 8:ELENA, 9:SAM, 10:OMAR, 11:JACK, 12:SARAH

runner_agents = [
    "1:CLARA", "2:ARTHUR", "3:MARCUS", "4:NINA", "5:MAX", "6:LEO",
    "7:KAI", "8:ELENA", "9:SAM", "10:OMAR", "11:JACK", "12:SARAH"
]

agent_to_lab = {
    "1:CLARA": "1:ALEX",     # News sentinel uses high-conviction macro base
    "2:ARTHUR": "6:SOPHIA",   # Macro regime uses Sophia
    "3:MARCUS": "3:MARCUS",
    "4:NINA": "4:NINA",
    "5:MAX": "5:MAX",
    "6:LEO": "11:LIAM",       # Session timing uses Liam
    "7:KAI": "7:DEREK",       # Fib OTE uses Derek
    "8:ELENA": "8:ELENA",
    "9:SAM": "9:SAM",
    "10:OMAR": "10:OMAR",
    "11:JACK": "11:LIAM",     # VSA uses Liam
    "12:SARAH": "2:MAYA",     # Psychologist uses Maya
}

trust_weights = {"ASIA": {"TRENDING": {}, "SIDEWAYS": {}},
                 "LONDON": {"TRENDING": {}, "SIDEWAYS": {}},
                 "NEW_YORK": {"TRENDING": {}, "SIDEWAYS": {}}}

for sess in ["ASIA", "LONDON", "NEW_YORK"]:
    for mkt in ["TRENDING", "SIDEWAYS"]:
        for rag in runner_agents:
            lab_id = agent_to_lab.get(rag, "1:ALEX")
            g3 = bundle[lab_id]["generations"]["v3.0_ORACLE_CHAMPION"]
            trades = g3.get("trades", [])
            sub = [t for t in trades if t["session"] == sess and t["regime"] == mkt]
            if sub:
                wins = sum(1 for t in sub if t["net_pnl"] > 0)
                wr = (wins / len(sub)) * 100.0
                pnl = sum(t["net_pnl"] for t in sub)
                pf = round(sum(t["net_pnl"] for t in sub if t["net_pnl"] > 0) / max(0.1, abs(sum(t["net_pnl"] for t in sub if t["net_pnl"] < 0))), 2)
            else:
                wr = g3["win_rate"]
                pnl = g3["net_pnl"] / 6.0
                pf = g3["profit_factor"]
            
            # Dynamic Weight formula:
            # Base weight 1.0, scaled exponentially by (WR / 55%)^1.5 and profit factor
            raw_w = 1.0 * ((wr / 55.0) ** 1.5) * (max(0.7, pf / 1.3) ** 0.5)
            # Clip between 0.60x and 2.25x
            final_w = float(np.clip(round(raw_w, 2), 0.60, 2.25))

            trust_weights[sess][mkt][rag] = {
                "weight": final_w,
                "win_rate": round(wr, 1),
                "pf": pf,
                "net_pnl": round(pnl, 2),
                "trades": len(sub) if sub else len(trades) // 6,
                "lab_proxy": lab_id
            }

with open(OUT_WEIGHTS, "w", encoding="utf-8") as f:
    json.dump({"trust_weights": trust_weights}, f, indent=2)

print(f"Generated {OUT_WEIGHTS} with empirical multi-weights across all 6 contexts!")
for sess in ["ASIA", "LONDON", "NEW_YORK"]:
    for mkt in ["TRENDING", "SIDEWAYS"]:
        top3 = sorted(trust_weights[sess][mkt].items(), key=lambda x: x[1]["weight"], reverse=True)[:3]
        top_str = ", ".join([f"{k}@{v['weight']}x ({v['win_rate']}%)" for k, v in top3])
        print(f"[{sess} - {mkt}] Top 3: {top_str}")
