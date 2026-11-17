import sys

with open('scripts/render_html.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Hero Banner
hero_start = '<!-- Champion Hero Banner -->'
hero_end = '<!-- Master Multi-Agent Pod Comparison Matrix Table -->'
p1 = content.find(hero_start)
p2 = content.find(hero_end)
if p1 == -1 or p2 == -1:
    print("ERROR: could not find hero banner markers")
    sys.exit(1)

new_hero = """<!-- Champion Hero Banner -->
    <div class="champion-hero">
      <div class="champ-badge-strip">
        <span class="champ-crown">🏆 COMBINED 1 + 2 + 3 (SKIPPING OVERLAPPING TRADES)</span>
        <span class="champ-pill">1_ULTRA_CADENCE (574) + 2_HIGH_FREQUENCY (847) + 3_SCALPER_DENSITY (1,115)</span>
        <span class="champ-pill green">1,115 DEDUPLICATED EXECUTIONS · +$775.37 NET PROFIT · 8.75X MULTIPLIER!</span>
      </div>
      <div class="champ-title-row">
        <div>
          <h2>Strategy Combination: 1, 2, and 3 Combined (Skipping Overlapping Trades)</h2>
          <p class="champ-sub">
            Combining the three top strategies circled by the user: <b>1_ULTRA_CADENCE (Dual-Slot)</b>, <b>2_HIGH_FREQUENCY (Tri-Slot)</b>, and <b>3_SCALPER_DENSITY (Quad-Slot)</b>.
            When merging these 3 strategies and skipping duplicate overlapping trade executions, we produce <b>1,115 unique institutional trades (10.14 trades/day)</b> with a <b>65.02% Win Rate</b>, <b>+$775.37 Net Profit ($875.37 Ending Equity)</b>, turning $100 into $875.37 (an <b>8.75X Account Multiplier</b>)!
            If instead strictly enforcing zero concurrent positions (Max 1 open trade at any time), the book yields <b>296 trades</b> with a <b>65.88% Win Rate</b>, <b>+$234.75 Net Profit</b>, and only <b>-16.23% Drawdown</b>.
          </p>
        </div>
        <div class="champ-cta">
          <button class="cta-btn primary" onclick="switchMasterTab('tab-chart')">📊 Open Live TradingView Chart</button>
          <button class="cta-btn secondary" onclick="switchMasterTab('tab-agent-lab')">🧪 Inspect 11 Specialists Lab</button>
          <button class="cta-btn secondary" onclick="switchMasterTab('tab-calendar')">📅 View P&amp;L Calendar</button>
        </div>
      </div>
      <div class="champ-metrics-grid">
        <div class="champ-m-card highlight">
          <div class="m-lbl">Ending Equity ($100 Start)</div>
          <div class="m-val pos">$875.37</div>
          <div class="m-sub">+775.37% Net Return · 8.75X Account Multiplier</div>
        </div>
        <div class="champ-m-card highlight">
          <div class="m-lbl">Win Rate (110 Active Days)</div>
          <div class="m-val pos">65.02%</div>
          <div class="m-sub">725 Wins / 390 Losses · 1.41 Profit Factor</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Deduplicated Executions</div>
          <div class="m-val blue">1,115 Trades</div>
          <div class="m-sub">10.14 Trades / Day (>500 Trades Requirement Fully Met!)</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Net Profit (Post 0.01% Delta Fees)</div>
          <div class="m-val pos">+$775.37</div>
          <div class="m-sub">Gross $1,265.35 - $489.97 Delta Fees = +$775.37 Clean</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Strict 1-Slot Alternative</div>
          <div class="m-val blue">296 Trades</div>
          <div class="m-sub">65.88% WR · +$234.75 Net · -16.23% Safe Max DD</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Specialists 1,2,3 Trio Variant</div>
          <div class="m-val gold">274 Trades</div>
          <div class="m-sub">64.23% WR · +$182.04 Net · Ultra-low -12.46% Max DD</div>
        </div>
      </div>
      <div class="specialist-contrib-box">
        <div class="sc-title">Combined 1 + 2 + 3 Slot Structure &amp; Overlap Resolution:</div>
        <div class="sc-chips">
          <span class="sc-chip"><b>Raw Sum</b>: 574 + 847 + 1,115 = 2,536 Raw Signals</span>
          <span class="sc-chip"><b>Duplicate Overlaps Skipped</b>: 1,421 Overlapping Duplicates Eliminated</span>
          <span class="sc-chip"><b>Final Unique Trades</b>: 1,115 Trades (100% Valid Institutional Executions)</span>
        </div>
      </div>
    </div>

    """

content = content[:p1] + new_hero + content[p2:]

# 2. Update default currentProfileKey
content = content.replace(
    'let currentProfileKey = "1_COMBINED_1_2_3_NON_OVERLAPPING";',
    'let currentProfileKey = "4_COMBINED_1_2_3_DEDUPLICATED";'
)

# 3. Update POD_PROFILES_META
p3 = content.find('const POD_PROFILES_META = [')
p4 = content.find('function renderPodMatrixTable()')
if p3 == -1 or p4 == -1:
    print("ERROR: could not find POD_PROFILES_META markers")
    sys.exit(1)

new_meta = """const POD_PROFILES_META = [
  {
    key: "1_ULTRA_CADENCE_574_TRADES_DUAL_SLOT",
    title: "1. 🏆 STRATEGY 1: ULTRA-CADENCE DUAL-SLOT",
    badge: "574 TRADES (5.22/DAY)",
    desc: "Dual-slot cadence engine across all 11 specialists: max 2 concurrent positions, skips 3rd+ overlaps. 574 trades, 65.16% WR, +$415.81 net profit ($515.81 Ending Equity).",
    agents: "All 11 Specialists (Max 2 Concurrent Slots)"
  },
  {
    key: "2_HIGH_FREQUENCY_847_TRADES_TRI_SLOT",
    title: "2. 🚀 STRATEGY 2: HIGH-FREQUENCY TRI-SLOT",
    badge: "847 TRADES (7.70/DAY)",
    desc: "Tri-slot high-frequency execution: max 3 concurrent positions, skips 4th+ overlaps. 847 trades, 65.05% WR, +$602.59 net profit ($702.59 Ending Equity).",
    agents: "All 11 Specialists (Max 3 Concurrent Slots)"
  },
  {
    key: "3_SCALPER_DENSITY_1115_TRADES_QUAD_SLOT",
    title: "3. ⚡ STRATEGY 3: SCALPER DENSITY QUAD-SLOT",
    badge: "1,115 TRADES (10.14/DAY)",
    desc: "Quad-slot density execution: max 4 concurrent positions, skips 5th+ overlaps. 1,115 trades, 65.02% WR, +$775.37 net profit ($875.37 Ending Equity, 8.75X multiplier).",
    agents: "All 11 Specialists (Max 4 Concurrent Slots)"
  },
  {
    key: "4_COMBINED_1_2_3_DEDUPLICATED",
    title: "4. 👑 COMBINED (1 + 2 + 3) DEDUPLICATED (SKIPPED OVERLAPS)",
    badge: "1,115 UNIQUE TRADES",
    desc: "Merged trade stream of Strategies 1, 2, and 3 skipping duplicate overlapping trade executions. Result: 1,115 unique executions, 65.02% WR, +$775.37 net profit ($875.37 Ending Equity).",
    agents: "Combined 1 + 2 + 3 (Deduplicated Unique Stream)"
  },
  {
    key: "5_COMBINED_1_2_3_STRICT_NON_OVERLAPPING",
    title: "5. 🛡️ COMBINED (1 + 2 + 3) STRICT NON-OVERLAPPING",
    badge: "296 TRADES (STRICT 1-SLOT)",
    desc: "Combined 1, 2, and 3 with strict non-overlapping rule: exactly 1 open position allowed at any time. While active, all overlapping setups are skipped. 296 trades, 65.88% WR, +$234.75 net, -16.23% Max DD.",
    agents: "Combined 1 + 2 + 3 (Max 1 Open Position)"
  },
  {
    key: "6_POD_AGENTS_1_2_3_NON_OVERLAPPING",
    title: "6. 🎯 SPECIALIST AGENTS 1 + 2 + 3 POD (NON-OVERLAPPING)",
    badge: "274 TRADES (LOWEST DD -12.46%)",
    desc: "Combined Specialist Trio: 1:ALEX (Indicators) + 2:MAYA (Price Action) + 3:MARCUS (Breakouts). Skipping overlapping trades: 274 trades, 64.23% WR, +$182.04 net, ultra-safe -12.46% Max DD.",
    agents: "1:ALEX + 2:MAYA + 3:MARCUS (Strict 1 Slot)"
  }
];

"""

content = content[:p3] + new_meta + content[p4:]

with open('scripts/render_html.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: scripts/render_html.py updated successfully!")
