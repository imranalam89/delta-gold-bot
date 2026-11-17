with open('scripts/render_html.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'currentProfileKey\s*=\s*["\']([^"\']+)["\']', text)
print('currentProfileKey matches:', matches)

matches2 = re.findall(r'<option\s+value=["\']([^"\']+)["\']', text)
print('option values in HTML:', matches2)

# Also find where strategySelect or profile keys are used
lines = text.split('\n')
for i, l in enumerate(lines):
    if 'profileSelect' in l or 'strategySelect' in l or 'currentProfile' in l:
        print(f'{i+1}: {l.strip()[:100]}')
