import json
import urllib.request
import urllib.error

env = {}
with open(".env", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

user = env.get("TRADOVATE_USER")
pwd = env.get("TRADOVATE_PASS")
print(f"Testing Tradovate / NinjaTrader login for user: {user}")

endpoints = [
    ("https://demo.tradovateapi.com/v1", "DEMO"),
    ("https://live.tradovateapi.com/v1", "LIVE")
]

for base_url, label in endpoints:
    payload = {
        "name": user,
        "password": pwd,
        "appId": "SampleApp",
        "appVersion": "1.0",
        "cid": 0,
        "sec": ""
    }
    url = f"{base_url}/auth/accesstokenrequest"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "SyndicateFloor/1.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[{label}] Status 200 OK. Response: {data}")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"[{label}] HTTPError {e.code}: {err_msg}")
    except Exception as e:
        print(f"[{label}] Exception: {e}")
