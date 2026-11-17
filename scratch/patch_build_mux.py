import os

with open('scripts/build_mux_exact_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace target_profile_key
text = text.replace(
    'target_profile_key = "MUX_085SL_40R_CONTINUOUS_TRAIL"',
    'target_profile_key = "MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL" if "MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL" in full_payload.get("profiles", {}) else "MUX_085SL_40R_CONTINUOUS_TRAIL"'
)

# Update hero banner title & numbers
text = text.replace('MUX_085SL_40R_CONTINUOUS_TRAIL (New 40R Continuous Trail)', 'MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL (Adaptive Chandelier Trail + 70/30 Moonbag)')
text = text.replace('MUX_085SL_40R_CONTINUOUS_TRAIL', 'MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL')
text = text.replace('+$430.70 NET PROFIT • $530.70 EQUITY (5.31X MULTIPLIER!)', '+$605.43 NET PROFIT • $705.43 EQUITY (7.05X MULTIPLIER!)')
text = text.replace('+$430.70 Net Profit ($530.70 Ending Equity)', '+$605.43 Net Profit ($705.43 Ending Equity)')
text = text.replace('61.13% Win Rate', '62.64% Win Rate')
text = text.replace('1.88 Profit Factor', '2.25 Profit Factor')
text = text.replace('$530.70</div>', '$705.43</div>')
text = text.replace('+$430.70 Net Gain (5.31X on $100 Account)', '+$605.43 Net Gain (7.05X on $100 Account)')
text = text.replace('61.13%</div>', '62.64%</div>')
text = text.replace('1.88 PF</div>', '2.25 PF</div>')
text = text.replace('18.43%</div>', '16.56%</div>')
text = text.replace('+$430.70</div>', '+$605.43</div>')
text = text.replace('Gross $568.85 - $138.15 Delta Fees = +$430.70 Clean', 'Gross $765.20 - $159.77 Delta Fees = +$605.43 Clean')
text = text.replace('+$140.03 Net • 1.89 PF', '+$196.40 Net • 2.25 PF')

# Update default profile key replacement
text = text.replace('currentProfileKey = "MUX_085SL_40R_CONTINUOUS_TRAIL";', 'currentProfileKey = "MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL";')

with open('scripts/build_mux_exact_dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("build_mux_exact_dashboard.py updated cleanly.")
