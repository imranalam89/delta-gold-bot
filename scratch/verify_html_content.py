import re

with open("backtest_dashboard.html", "r", encoding="utf-8") as f:
    html = f.read(100000) # first 100k chars

print("Title:", re.findall(r'<title>(.*?)</title>', html))
print("Default profile:", re.findall(r'currentProfileKey\s*=\s*"(.*?)";', html))
print("Hero text sample:", "MUX_085SL_NEWS_SHIELD_ELITE" in html)
print("Exit badges present:", "badge-instant" in html and "badge-stall" in html and "badge-trail-40r" in html)
