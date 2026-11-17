import csv

with open('data/processed/mtf_100s_combinations_results.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

for r in rows:
    r['score'] = float(r['score'])
    r['net_pnl'] = float(r['net_pnl'])
    r['wr'] = float(r['wr'])
    r['max_dd'] = float(r['max_dd'])
    r['trades'] = int(r['trades'])
    r['pf'] = float(r['pf'])
    r['calmar'] = float(r['calmar'])

# 1. Top 5 overall by Max Net PnL
by_pnl = sorted(rows, key=lambda x: -x['net_pnl'])
print("=== TOP 5 BY NET PNL (PROFIT MAXIMIZATION) ===")
print(f"{'Combo':<6} | {'Mode':<14} | {'TFs':<18} | {'Slots':<5} | {'Trades':<6} | {'WR %':<6} | {'PF':<5} | {'Net PnL':<10} | {'Max DD':<7} | {'Calmar':<6}")
print("-" * 105)
for r in by_pnl[:5]:
    tf_str = "+".join(eval(r['allowed_tfs']))
    print(f"{r['combo_id']:<6} | {r['agent_filter_mode']:<14} | {tf_str:<18} | {r['max_slots']:<5} | {r['trades']:<6} | {r['wr']:<6.2f}% | {r['pf']:<5.2f} | ${r['net_pnl']:<9.2f} | -{r['max_dd']:<6.2f}% | {r['calmar']:<6.2f}")

# 2. Top 5 including 1m (High Cadence > 250 trades)
high_cadence = [r for r in rows if '1m' in r['allowed_tfs'] and r['trades'] >= 200]
high_cadence.sort(key=lambda x: -x['net_pnl'])
print("\n=== TOP 5 HIGH CADENCE (INCLUDING 1M > 200 TRADES) ===")
print(f"{'Combo':<6} | {'Mode':<14} | {'TFs':<18} | {'Slots':<5} | {'Trades':<6} | {'WR %':<6} | {'PF':<5} | {'Net PnL':<10} | {'Max DD':<7} | {'Calmar':<6}")
print("-" * 105)
for r in high_cadence[:5]:
    tf_str = "+".join(eval(r['allowed_tfs']))
    print(f"{r['combo_id']:<6} | {r['agent_filter_mode']:<14} | {tf_str:<18} | {r['max_slots']:<5} | {r['trades']:<6} | {r['wr']:<6.2f}% | {r['pf']:<5.2f} | ${r['net_pnl']:<9.2f} | -{r['max_dd']:<6.2f}% | {r['calmar']:<6.2f}")

# 3. Top 5 by Calmar Ratio (Lowest Drawdown & Safe Growth)
by_calmar = sorted(rows, key=lambda x: -x['calmar'])
print("\n=== TOP 5 BY CALMAR RATIO (SAFEST LOW DRAWDOWN) ===")
print(f"{'Combo':<6} | {'Mode':<14} | {'TFs':<18} | {'Slots':<5} | {'Trades':<6} | {'WR %':<6} | {'PF':<5} | {'Net PnL':<10} | {'Max DD':<7} | {'Calmar':<6}")
print("-" * 105)
for r in by_calmar[:5]:
    tf_str = "+".join(eval(r['allowed_tfs']))
    print(f"{r['combo_id']:<6} | {r['agent_filter_mode']:<14} | {tf_str:<18} | {r['max_slots']:<5} | {r['trades']:<6} | {r['wr']:<6.2f}% | {r['pf']:<5.2f} | ${r['net_pnl']:<9.2f} | -{r['max_dd']:<6.2f}% | {r['calmar']:<6.2f}")
