with open("backtest_dashboard.html", "r", encoding="utf-8") as f:
    html = f.read()

checks = [
    ("DOCTYPE", "<!DOCTYPE html>"),
    ("Lightweight Charts CDN", "unpkg.com/lightweight-charts"),
    ("Master Navigation Bar", 'class="master-tab-bar"'),
    ("Tab 1 Master Floor", 'id="tab-master-floor"'),
    ("Tab 2 Agent Lab", 'id="tab-agent-lab"'),
    ("Tab 3 TV Chart", 'id="tab-chart"'),
    ("Tab 4 Calendar", 'id="tab-calendar"'),
    ("Tab 5 Journal", 'id="tab-journal"'),
    ("Champion Hero Banner", 'class="champion-hero"'),
    ("574 Trades Champion", "1_ULTRA_CADENCE_574_TRADES_DUAL_SLOT"),
    ("847 Trades Tri-Slot", "2_HIGH_FREQUENCY_847_TRADES_TRI_SLOT"),
    ("1115 Trades Quad-Slot", "3_SCALPER_DENSITY_1115_TRADES_QUAD_SLOT"),
    ("296 Trades Single-Slot", "4_CONSERVATIVE_296_TRADES_SINGLE_SLOT"),
    ("Pod Matrix Table", 'id="podMatrixTable"'),
    ("Lab Roadmap Bar", 'id="labRoadmapBar"'),
    ("Lab Leaderboard Table", 'id="labLeaderboardTable"'),
    ("Lab TV Chart Container", 'id="lab-tv-chart"'),
    ("Continuous Chart Canvas", 'id="tvChart"'),
    ("Timeline Navigator Canvas", 'id="tvNavChart"'),
    ("Equity Canvas Tab 1", 'id="equityCanvas"'),
    ("Calendar Grid", 'id="calendarGrid"'),
    ("Trade Table", 'id="tradeTable"'),
    ("CSV Export Button", 'id="exportCsvBtn"'),
    ("CSV Export Function", "exportTradesCSV"),
    ("Tab Switch Function", "switchMasterTab"),
    ("Lab Engine Init", "initLab()")
]

print(f"HTML size: {len(html)/1024/1024:.2f} MB")
for name, tag in checks:
    status = "PASS" if tag in html else "FAIL"
    print(f"  [{status}] {name}")
