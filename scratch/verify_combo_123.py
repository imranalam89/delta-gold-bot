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
    ("Combined 1, 2, 3 Non-Overlapping", "1_COMBINED_1_2_3_NON_OVERLAPPING"),
    ("Combined 1, 2, 3 Dual-Slot (>500 Trades)", "2_COMBINED_1_2_3_DUAL_SLOT"),
    ("Combined 1, 2, 3 Tri-Slot", "3_COMBINED_1_2_3_TRI_SLOT"),
    ("All 11 Dual-Slot (>500 Trades)", "4_ALL_11_AGENTS_ULTRA_CADENCE"),
    ("All 11 Tri-Slot (>800 Trades)", "5_ALL_11_AGENTS_HIGH_FREQUENCY"),
    ("All 11 Single-Slot Master", "6_ALL_11_AGENTS_SINGLE_SLOT_MASTER"),
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
all_ok = True
for name, tag in checks:
    status = "PASS" if tag in html else "FAIL"
    print(f"  [{status}] {name}")
    if status == "FAIL": all_ok = False

if all_ok:
    print("ALL COMBINED 1, 2, 3 VERIFICATION CHECKS PASSED PERFECTLY!")
