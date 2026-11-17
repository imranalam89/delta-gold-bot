import json

with open('data/processed/all_11_agents_lab_bundle.json', 'r') as f:
    bundle = json.load(f)

all_trades = []
for ag, data in bundle.items():
    champ = data.get('generations', {}).get('v3.0_ORACLE_CHAMPION', {})
    for t in champ.get('trades', []):
        all_trades.append(t)

print(f"Total trades across all 11 agents: {len(all_trades)}")

m_0_10 = 0
m_10_20 = 0
m_20_50 = 0
m_50_100 = 0
m_100_plus = 0

top_trades = []

for t in all_trades:
    peak_pts = t['peak_r'] * t['sl_dist']
    if peak_pts < 10.0:
        m_0_10 += 1
    elif 10.0 <= peak_pts < 20.0:
        m_10_20 += 1
    elif 20.0 <= peak_pts < 50.0:
        m_20_50 += 1
    elif 50.0 <= peak_pts < 100.0:
        m_50_100 += 1
    else:
        m_100_plus += 1

    if peak_pts >= 50.0:
        top_trades.append({
            'agent': t['agent'],
            'time': t['entry_time'],
            'dir': t['direction'],
            'session': t['session'],
            'peak_pts': round(peak_pts, 1),
            'sl_dist': round(t['sl_dist'], 1),
            'net_pnl': round(t['net_pnl'], 2)
        })

print(f"Trades with peak movement < 10 pts:      {m_0_10} ({m_0_10/len(all_trades)*100:.1f}%)")
print(f"Trades with peak movement 10 - 20 pts:   {m_10_20} ({m_10_20/len(all_trades)*100:.1f}%)")
print(f"Trades with peak movement 20 - 50 pts:   {m_20_50} ({m_20_50/len(all_trades)*100:.1f}%)")
print(f"Trades with peak movement 50 - 100 pts:  {m_50_100} ({m_50_100/len(all_trades)*100:.1f}%)")
print(f"Trades with peak movement > 100 pts:     {m_100_plus} ({m_100_plus/len(all_trades)*100:.1f}%)")

print("\n--- SAMPLE 50+ PT RUNNERS ACROSS THE AGENTS ---")
for tt in sorted(top_trades, key=lambda x: x['peak_pts'], reverse=True)[:8]:
    print(f"Agent: {tt['agent']:10s} | Time: {tt['time']} | Dir: {tt['dir']:5s} | Peak Move: +${tt['peak_pts']} | SL: ${tt['sl_dist']} | Net: +${tt['net_pnl']}")
