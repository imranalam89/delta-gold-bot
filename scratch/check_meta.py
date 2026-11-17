import sys, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')
from scripts.render_html import HTML_TEMPLATE

idx = HTML_TEMPLATE.find('const POD_PROFILES_META')
print(HTML_TEMPLATE[idx:idx+2500])
