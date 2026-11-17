import urllib.request
import re

base_url = "http://62.72.31.29:5050/"
pages = [
    "agent_journal.html",
    "backtest_v3.html",
    "backtest_v4.html",
    "backtest_v5.html",
    "btc_journal.html",
    "combined_portfolio_backtest_report.html",
    "dom_2day_journal_report.html",
    "dom_heatmap.html",
    "eth_journal.html",
    "gold_journal.html",
    "live_journal.html",
    "strategy_guide.html"
]

all_endpoints = set()
for page in pages:
    try:
        url = base_url + page
        html = urllib.request.urlopen(url, timeout=5).read().decode("utf-8", errors="ignore")
        eps = re.findall(r'["\'](/api/[^"\']+)["\']', html)
        for ep in eps:
            all_endpoints.add((page, ep))
    except Exception as e:
        print(f"Failed {page}: {e}")

print("All endpoints discovered:")
for page, ep in sorted(list(all_endpoints)):
    print(f"[{page}] -> {ep}")

