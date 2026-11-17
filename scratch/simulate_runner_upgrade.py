import json

with open('data/processed/all_11_agents_lab_bundle.json', 'r') as f:
    bundle = json.load(f)

# Compare Original vs 3-Tier Multi-Horizon Runner across all 11 agents
orig_total_net = 0.0
runner_total_net = 0.0
runner_bonus_usd = 0.0

total_trades = 0
runner_boosted_trades = 0

for ag, data in bundle.items():
    champ = data.get('generations', {}).get('v3.0_ORACLE_CHAMPION', {})
    for t in champ.get('trades', []):
        total_trades += 1
        net_orig = t['net_pnl']
        orig_total_net += net_orig

        sl_dist = t['sl_dist']
        peak_pts = t['peak_r'] * sl_dist
        qty = t['qty']

        # If trade reached >= $20 (session expansion or megatrend)
        # Original took TP1 at 1.8R, TP2 at 3.35R
        # With 3-Tranche Runner (35% TP1, 35% TP2, 30% Runner up to 80% of peak):
        if peak_pts >= 20.0 and t['r_multiple'] > 0:
            runner_boosted_trades += 1
            # 30% of position trails to 80% of peak (retaining profit before reversal)
            extra_runner_pts = (0.80 * peak_pts - 3.35 * sl_dist)
            if extra_runner_pts > 0:
                extra_usd = 0.30 * qty * extra_runner_pts
                runner_bonus_usd += extra_usd
                runner_total_net += (net_orig + extra_usd)
            else:
                runner_total_net += net_orig
        else:
            runner_total_net += net_orig

print("="*65)
print(" 3-TIER MULTI-HORIZON RUNNER IMPACT ON AGENTS BUNDLE")
print("="*65)
print(f"Total Trades Evaluated:             {total_trades}")
print(f"Trades Expanding >= $20:            {runner_boosted_trades} ({runner_boosted_trades/total_trades*100:.1f}%)")
print(f"Original Net Desk Profit (Capped):  ${orig_total_net:.2f}")
print(f"Additional Runner Profit Unlocked: +${runner_bonus_usd:.2f}")
print(f"New Total Net Desk Profit:          ${runner_total_net:.2f}")
print(f"Desk Profit Multiplier:             {runner_total_net / orig_total_net:.2f}x")
print("="*65)
