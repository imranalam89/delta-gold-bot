import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRUST_PATH = os.path.join(BASE_DIR, "data", "processed", "agent_trust_weights.json")
OUT_PATH1 = os.path.join(BASE_DIR, "trading_desk", "agent_edge_matrix.json")
OUT_PATH2 = os.path.join(BASE_DIR, "data", "processed", "agent_edge_matrix.json")

edge_matrix = {}

if os.path.exists(TRUST_PATH):
    with open(TRUST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f).get("trust_weights", {})
    
    for sess, reg_dict in data.items():
        edge_matrix[sess] = {}
        for reg, agents in reg_dict.items():
            edge_matrix[sess][reg] = {}
            for ag_key, info in agents.items():
                w = info.get("weight", 1.0)
                clean_name = ag_key.split(":")[-1]  # e.g. "ELENA" from "8:ELENA"
                edge_matrix[sess][reg][ag_key] = w
                edge_matrix[sess][reg][clean_name] = w
                # Map aliases like BEN -> CLARA
                if clean_name == "CLARA":
                    edge_matrix[sess][reg]["BEN"] = w
                    edge_matrix[sess][reg]["1:BEN"] = w
                elif clean_name == "ELENA":
                    edge_matrix[sess][reg]["PRICE_ACTION"] = w
else:
    # Default fallback
    sessions = ["ASIA", "LONDON", "NEW_YORK"]
    regimes = ["TRENDING", "SIDEWAYS"]
    agents = ["CLARA", "BEN", "ARTHUR", "MARCUS", "NINA", "MAX", "LEO", "KAI", "ELENA", "SAM", "OMAR", "JACK", "SARAH", "DAVID", "ETHAN", "VICTOR", "RYAN"]
    for s in sessions:
        edge_matrix[s] = {}
        for r in regimes:
            edge_matrix[s][r] = {a: 1.0 for a in agents}

for p in [OUT_PATH1, OUT_PATH2]:
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(edge_matrix, f, indent=2)

print("Generated agent_edge_matrix.json successfully.")
