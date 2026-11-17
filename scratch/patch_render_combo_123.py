import os

RENDER_PY = "scripts/render_html.py"

with open(RENDER_PY, "r", encoding="utf-8") as f:
    text = f.read()

# Update Hero Banner
old_hero = """      <div class="champ-badge-strip">
        <span class="champ-crown">🏆 CHAMPION MULTI-AGENT ARCHITECTURE (>500 TRADES ACHIEVED)</span>
        <span class="champ-pill">ALL 11 SPECIALISTS DUAL-SLOT CADENCE ENGINE</span>
        <span class="champ-pill green">100% REAL CME GLOBEX GOLD (GC.v.0)</span>
      </div>
      <div class="champ-title-row">
        <div>
          <h2>Dual-Slot High-Cadence Engine — 574 Trades Across 5 Months</h2>
          <p class="champ-sub">
            High-density multi-agent execution across all 11 field specialists (<code>1:ALEX</code> through <code>11:LIAM</code>).
            Allows up to 2 concurrent specialist positions ($5.00 fixed risk each), delivering <b>5.22 trades/day (574 total trades)</b>
            with a stellar <b>65.16% Win Rate</b> and <b>+$415.81 Net Return ($515.81 Ending Equity / 5.16X Account Multiplier)</b>!
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
          <div class="m-val pos">$515.81</div>
          <div class="m-sub">+415.81% Net Return · 5.16X Account Multiplier</div>
        </div>
        <div class="champ-m-card highlight">
          <div class="m-lbl">Win Rate (110 Active Days)</div>
          <div class="m-val pos">65.16%</div>
          <div class="m-sub">374 Wins / 200 Losses · 1.43 Profit Factor</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Total Executed Trades</div>
          <div class="m-val blue">574 Trades</div>
          <div class="m-sub">5.22 Trades / Active Day (>500 Trades Target Achieved!)</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Maximum Drawdown</div>
          <div class="m-val neg">-22.21%</div>
          <div class="m-sub">Controlled Peak-to-Trough · $5.00 Fixed Risk</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Delta Exchange Fees Paid</div>
          <div class="m-val gold">$251.92</div>
          <div class="m-sub">Exact 0.01% per leg (Entry + Exit) accounted for</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Net Average Expectancy</div>
          <div class="m-val pos">+$0.72 / Trade</div>
          <div class="m-sub">+0.23R Expected Value per Executed Signal</div>
        </div>
      </div>
      <div class="specialist-contrib-box">
        <div class="sc-title">Specialist Contribution in Champion Non-Overlapping Book:</div>
        <div class="sc-chips">
          <span class="sc-chip"><b>1:ALEX</b> (Indicators): 130 trades (43.9%)</span>
          <span class="sc-chip"><b>8:ELENA</b> (1m Scalp): 44 trades (14.9%)</span>
          <span class="sc-chip"><b>7:DEREK</b> (Fib OTE): 40 trades (13.5%)</span>
          <span class="sc-chip"><b>3:MARCUS</b> (Box Breakout): 32 trades (10.8%)</span>
          <span class="sc-chip"><b>2:MAYA</b> (Price Action): 26 trades (8.8%)</span>
          <span class="sc-chip"><b>6:SOPHIA</b> (Killzones): 12 trades (4.1%)</span>
          <span class="sc-chip"><b>10:OMAR</b> (Order Flow): 5 trades (1.7%)</span>
          <span class="sc-chip"><b>4:NINA</b> (SMC/FVG): 4 trades (1.4%)</span>
          <span class="sc-chip"><b>5:MAX</b> (Traps): 3 trades (1.0%)</span>
        </div>
      </div>"""

new_hero = """      <div class="champ-badge-strip">
        <span class="champ-crown">🏆 CHAMPION TRIO: AGENTS 1 + 2 + 3 (NON-OVERLAPPING)</span>
        <span class="champ-pill">1:ALEX (INDICATORS) + 2:MAYA (PRICE ACTION) + 3:MARCUS (BOX BREAKOUTS)</span>
        <span class="champ-pill green">LOWEST DRAWDOWN: ONLY -12.46%!</span>
      </div>
      <div class="champ-title-row">
        <div>
          <h2>Specialist Trio: Agents 1, 2, and 3 Combined (Skip Overlapping Trades)</h2>
          <p class="champ-sub">
            Combines <b>1:ALEX (Technical Trend & Momentum)</b>, <b>2:MAYA (Price Action Market Structure Shifts)</b>, and <b>3:MARCUS (Asian/London Range Box Breakouts)</b>.
            Whenever any of the 3 agents triggers a trade, it enters with strict $5.00 fixed risk. All overlapping trades from the other two agents are skipped while the position is active.
            Delivers <b>274 institutional trades (2.49 trades/day)</b> with a <b>64.23% Win Rate</b>, <b>+$182.04 Net Profit ($282.04 Ending Equity)</b>, and an ultra-safe <b>-12.46% Maximum Drawdown</b>!
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
          <div class="m-val pos">$282.04</div>
          <div class="m-sub">+182.04% Net Return · 2.82X Account Multiplier</div>
        </div>
        <div class="champ-m-card highlight">
          <div class="m-lbl">Win Rate (110 Active Days)</div>
          <div class="m-val pos">64.23%</div>
          <div class="m-sub">176 Wins / 98 Losses · 1.39 Profit Factor</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Total Executed Trades</div>
          <div class="m-val blue">274 Trades</div>
          <div class="m-sub">2.49 Trades / Day (Single Non-Overlapping Position)</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Maximum Drawdown</div>
          <div class="m-val pos">-12.46%</div>
          <div class="m-sub">Lowest Drawdown of Any Combined Model!</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Delta Exchange Fees Paid</div>
          <div class="m-val gold">$120.35</div>
          <div class="m-sub">Exact 0.01% per leg (Entry + Exit) accounted for</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Dual-Slot Variant (>500 Trades)</div>
          <div class="m-val blue">528 Trades</div>
          <div class="m-sub">64.77% WR · +$330.47 Net · $430.47 Eq (4.80/day)</div>
        </div>
      </div>
      <div class="specialist-contrib-box">
        <div class="sc-title">Trio Contribution in Non-Overlapping Book:</div>
        <div class="sc-chips">
          <span class="sc-chip"><b>1:ALEX</b> (Technical Indicators): 186 trades (67.9%)</span>
          <span class="sc-chip"><b>3:MARCUS</b> (Box Breakouts): 45 trades (16.4%)</span>
          <span class="sc-chip"><b>2:MAYA</b> (Price Action MSS): 43 trades (15.7%)</span>
        </div>
      </div>"""

text = text.replace(old_hero, new_hero)

# Update POD_PROFILES_META
old_meta = """const POD_PROFILES_META = [
  {
    key: "1_ULTRA_CADENCE_574_TRADES_DUAL_SLOT",
    title: "1. 🏆 DUAL-SLOT SPECIALIST CHAMPION (>500 TRADES)",
    badge: "CHAMPION >500 TRADES",
    desc: "Dual-slot specialist engine: up to 2 concurrent positions across all 11 specialists. 5.22 trades/day, +$415.81 net profit, $515.81 ending equity (5.16X multiplier)!",
    agents: "All 11 Specialists (ALEX, MAYA, MARCUS, NINA, MAX, SOPHIA, DEREK, ELENA, SAM, OMAR, LIAM)"
  },
  {
    key: "2_HIGH_FREQUENCY_847_TRADES_TRI_SLOT",
    title: "2. 🚀 TRI-SLOT HIGH-FREQUENCY SYNDICATE (>800 TRADES)",
    badge: "HIGH-OCTANE 800+ TRADES",
    desc: "Tri-slot high-frequency execution: up to 3 concurrent specialist positions. 7.70 trades/day, +$602.59 net profit, $702.59 ending equity (7.03X multiplier)!",
    agents: "All 11 Specialists (3 Concurrent Slots)"
  },
  {
    key: "3_SCALPER_DENSITY_1115_TRADES_QUAD_SLOT",
    title: "3. ⚡ QUAD-SLOT SCALPER DENSITY (>1000 TRADES)",
    badge: "HYPER-SCALP 1000+ TRADES",
    desc: "Quad-slot institutional scalper density: up to 4 concurrent positions. 10.14 trades/day, +$775.37 net profit, $875.37 ending equity (8.75X multiplier)!",
    agents: "All 11 Specialists (4 Concurrent Slots)"
  },
  {
    key: "4_CONSERVATIVE_296_TRADES_SINGLE_SLOT",
    title: "4. 🛡️ CONSERVATIVE SINGLE-SLOT BOOK (296 TRADES)",
    badge: "LOW DRAWDOWN (2.69/DAY)",
    desc: "Strict single-position non-overlapping book: 296 trades, 65.88% win rate, lowest drawdown (-16.23%), +$234.75 net profit.",
    agents: "All 11 Specialists (Strict 1 Slot)"
  },
  {
    key: "5_POD_MARCUS_SOPHIA_BREAKOUT",
    title: "5. 🎯 POD: MARCUS + SOPHIA (261 TRADES)",
    badge: "BREAKOUT + KILLZONE",
    desc: "Synergistic breakout pod: MARCUS Asian/London range box breaks confirmed by SOPHIA macro killzone momentum (+$200.95 net profit).",
    agents: "3:MARCUS (Box Breakouts) + 6:SOPHIA (Macro Killzones)"
  },
  {
    key: "6_POD_MAYA_SAM_LIQUIDITY",
    title: "6. 💧 POD: MAYA + SAM (270 TRADES)",
    badge: "L2 LIQUIDITY SWEEPS",
    desc: "Liquidity trap hunter: SAM Level-2 deep book pool sweeps backed by MAYA price action rejection wicks (+$177.58 net profit).",
    agents: "2:MAYA (Price Action) + 9:SAM (Level-2 Liquidity Pools)"
  }
];"""

new_meta = """const POD_PROFILES_META = [
  {
    key: "1_COMBINED_1_2_3_NON_OVERLAPPING",
    title: "1. 🏆 COMBINED AGENTS 1, 2, 3 (STRICT NON-OVERLAPPING)",
    badge: "CHAMPION NON-OVERLAPPING",
    desc: "Strict single-position book combining Agent 1 (ALEX), 2 (MAYA), and 3 (MARCUS). Lowest drawdown in syndicate (-12.46%), 2.49 trades/day, 64.23% WR, +$182.04 net profit.",
    agents: "1:ALEX (Indicators) + 2:MAYA (Price Action) + 3:MARCUS (Box Breakouts)"
  },
  {
    key: "2_COMBINED_1_2_3_DUAL_SLOT",
    title: "2. 🚀 COMBINED AGENTS 1, 2, 3 (DUAL-SLOT >500 TRADES)",
    badge: ">500 TRADES (4.80/DAY)",
    desc: "Dual-slot cadence engine for Agents 1, 2, 3: up to 2 concurrent positions, skipping 3rd overlaps. 528 trades, 64.77% WR, +$330.47 net profit ($430.47 Eq, 4.30X multiplier)!",
    agents: "1:ALEX + 2:MAYA + 3:MARCUS (Max 2 Concurrent Slots)"
  },
  {
    key: "3_COMBINED_1_2_3_TRI_SLOT",
    title: "3. ⚡ COMBINED AGENTS 1, 2, 3 (TRI-SLOT FULL TRIO)",
    badge: "FULL TRIO (6.52/DAY)",
    desc: "Tri-slot trio execution for Agents 1, 2, 3: 717 trades across 5 months, 64.85% WR, +$437.56 net profit ($537.56 Eq, 5.38X multiplier)!",
    agents: "1:ALEX + 2:MAYA + 3:MARCUS (Max 3 Concurrent Slots)"
  },
  {
    key: "4_ALL_11_AGENTS_ULTRA_CADENCE",
    title: "4. 🛡️ ALL 11 SPECIALISTS (DUAL-SLOT >500 TRADES)",
    badge: "574 TRADES (5.22/DAY)",
    desc: "Dual-slot master floor across all 11 specialists: 574 trades, 65.16% WR, +$415.81 net profit ($515.81 Ending Equity, 5.16X multiplier)!",
    agents: "All 11 Specialists (2 Concurrent Slots)"
  },
  {
    key: "5_ALL_11_AGENTS_HIGH_FREQUENCY",
    title: "5. 🎯 ALL 11 SPECIALISTS (TRI-SLOT >800 TRADES)",
    badge: "847 TRADES (7.70/DAY)",
    desc: "Tri-slot high-frequency master floor across all 11 specialists: 847 trades, 65.05% WR, +$602.59 net profit ($702.59 Ending Equity, 7.03X multiplier)!",
    agents: "All 11 Specialists (3 Concurrent Slots)"
  },
  {
    key: "6_ALL_11_AGENTS_SINGLE_SLOT_MASTER",
    title: "6. 👑 ALL 11 SPECIALISTS (SINGLE-SLOT NON-OVERLAPPING)",
    badge: "296 TRADES (2.69/DAY)",
    desc: "Strict single-position non-overlapping book for all 11 specialists: 296 trades, 65.88% WR, +$234.75 net profit ($334.75 Ending Equity)!",
    agents: "All 11 Specialists (Strict 1 Slot)"
  }
];"""

text = text.replace(old_meta, new_meta)

# Update default profile key
text = text.replace(
    'let currentProfileKey = "1_ULTRA_CADENCE_574_TRADES_DUAL_SLOT";',
    'let currentProfileKey = "1_COMBINED_1_2_3_NON_OVERLAPPING";'
)

with open(RENDER_PY, "w", encoding="utf-8") as f:
    f.write(text)

print(f"Updated {RENDER_PY} with Combined 1, 2, 3 metadata!")
