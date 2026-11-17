import os
import glob

matches = []
for root, dirs, files in os.walk('.'):
    if any(p in root for p in ['.git', '.venv', 'node_modules', '__pycache__']):
        continue
    for file in files:
        if file.endswith(('.py', '.md', '.txt', '.json', '.csv', '.parquet')):
            path = os.path.join(root, file)
            try:
                # check filename first
                fl = file.lower()
                if any(x in fl for x in ['5y', '5_year', '5year', '2020', '2021', '2022', 'history', 'historical']):
                    matches.append((path, 'filename'))
                    continue
                # check file content if not huge
                if os.path.getsize(path) < 5_000_000 and file.endswith(('.py', '.md', '.txt')):
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                        if '5 year' in text.lower() or '5-year' in text.lower() or '5yr' in text.lower():
                            matches.append((path, 'content'))
            except Exception:
                pass

print(f"Total matches found: {len(matches)}")
for m in matches[:25]:
    print(m)
