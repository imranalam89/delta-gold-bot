with open(r"c:\Users\USER\OneDrive\Desktop\Agents Team\.venv\Lib\site-packages\async_rithmic\client.py", "r") as f:
    text = f.read()

import re
print("Matches in client.py:", set(re.findall(r"[\w\.-]+\.rithmic\.com[^\s\"']*", text)))
