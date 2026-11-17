import sys, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')
from scripts.render_html import HTML_TEMPLATE

print(f"HTML_TEMPLATE length: {len(HTML_TEMPLATE)} chars")
lines = HTML_TEMPLATE.split('\n')
print(f"HTML_TEMPLATE lines: {len(lines)}")

for i, line in enumerate(lines):
    l = line.strip()
    if any(k in l for k in ['top-header', 'master-tab-bar', 'champion-hero', 'id="tab-', 'class="panel"', 'class="tv-workspace"']):
        print(f"Line {i+1}: {l[:100]}")
