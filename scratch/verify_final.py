import os
import json
import re

html_path = 'backtest_dashboard.html'
payload_path = 'data/processed/dashboard_payload.json'

print("=== VERIFYING DASHBOARD & PROFILES ===")

assert os.path.exists(html_path), "backtest_dashboard.html does not exist!"
html_size = os.path.getsize(html_path)
print(f"HTML size: {html_size / (1024*1024):.2f} MB")

with open(payload_path, 'r', encoding='utf-8') as f:
    payload = json.load(f)

expected_profiles = [
    '1_ULTRA_CADENCE_574_TRADES_DUAL_SLOT',
    '2_HIGH_FREQUENCY_847_TRADES_TRI_SLOT',
    '3_SCALPER_DENSITY_1115_TRADES_QUAD_SLOT',
    '4_COMBINED_1_2_3_DEDUPLICATED',
    '5_COMBINED_1_2_3_STRICT_NON_OVERLAPPING',
    '6_POD_AGENTS_1_2_3_NON_OVERLAPPING'
]

print("\n--- PROFILES VERIFICATION ---")
for p in expected_profiles:
    assert p in payload['profiles'], f"Missing profile: {p}"
    trades = payload['profiles'][p]['trades']
    n = len(trades)
    wins = len([t for t in trades if t['net_pnl_usd'] > 0])
    wr = (wins / n * 100) if n else 0
    net = sum(t['net_pnl_usd'] for t in trades)
    print(f"  [OK] {p}: {n} trades | WR: {wr:.2f}% | Net: ${net:.2f}")

with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

for p in expected_profiles:
    assert p in html_content, f"Profile key {p} missing in HTML content!"

assert '4_COMBINED_1_2_3_DEDUPLICATED' in html_content
assert '5_COMBINED_1_2_3_STRICT_NON_OVERLAPPING' in html_content
assert '6_POD_AGENTS_1_2_3_NON_OVERLAPPING' in html_content
assert '1,115' in html_content
assert '296' in html_content
assert '274' in html_content
assert '875.37' in html_content

print("\n=== ALL VERIFICATIONS PASSED (100% OK)! ===")
