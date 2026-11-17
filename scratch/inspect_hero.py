import sys, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')
from scripts.render_html import HTML_TEMPLATE

# Inspect Hero banner in HTML_TEMPLATE
s_hero = HTML_TEMPLATE.find('<div class="champion-hero">')
e_hero = HTML_TEMPLATE.find('<!-- Comparison Table -->', s_hero)
print("=== CURRENT HERO BANNER ===")
print(HTML_TEMPLATE[s_hero:e_hero])
