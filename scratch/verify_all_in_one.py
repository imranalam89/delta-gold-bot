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
    ("Champion Profile", "1_ALL_11_AGENTS_NON_OVERLAPPING_MASTER"),
    ("Pod Matrix Table", 'id="podMatrixTable"'),
    ("Lab Roadmap Bar", 'id="labRoadmapBar"'),
    ("Lab Leaderboard Table", 'id="labLeaderboardTable"'),
    ("Lab TV Chart Container", 'id="lab-tv-chart"'),
    ("Lab Forensic Box", 'id="lab-forensic-box"'),
    ("Continuous Chart Canvas", 'id="tvChart"'),
    ("Timeline Navigator Canvas", 'id="tvNavChart"'),
    ("Equity Canvas Tab 1", 'id="equityCanvas"'),
    ("Equity Canvas Tab 4", 'id="equityCanvasTab4"'),
    ("Calendar Grid", 'id="calendarGrid"'),
    ("Trade Table", 'id="tradeTable"'),
    ("CSV Export Button", 'id="exportCsvBtn"'),
    ("CSV Export Function", "exportTradesCSV"),
    ("Tab Switch Function", "switchMasterTab"),
    ("Lab Engine Init", "initLab()"),
    ("Pod Matrix Renderer", "renderPodMatrixTable()")
]

print(f"File size: {len(html)/1024/1024:.2f} MB")
all_ok = True
for name, tag in checks:
    if tag in html:
        print(f"  [PASS] {name}")
    else:
        print(f"  [FAIL] {name} missing!")
        all_ok = False

if all_ok:
    print("ALL 26 CRITICAL INTEGRATION CHECKS PASSED PERFECTLY!")
else:
    print("SOME CHECKS FAILED!")
