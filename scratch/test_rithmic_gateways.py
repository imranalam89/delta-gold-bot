import asyncio
import os
from async_rithmic import RithmicClient

env = {}
with open(".env", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

user = env.get("RITHMIC_USER")
pwd = env.get("RITHMIC_PASS")
system = env.get("RITHMIC_SYSTEM", "Rithmic Paper Trading")

print(f"Testing Rithmic credentials for user: {user} on system: {system}")

gateways = [
    "rituz00100.rithmic.com:443",
    "rituz01000.rithmic.com:443",
    "chi.rithmic.com:443",
    "chicago.rithmic.com:443",
]

async def test_gateway(gw):
    print(f"\n--- Trying gateway: {gw} ---")
    client = RithmicClient(
        user=user,
        password=pwd,
        system_name=system,
        app_name="SyndicateFloor",
        app_version="1.0.0",
        url=gw
    )
    try:
        await asyncio.wait_for(client.connect(), timeout=8)
        print("CONNECTED SUCCESSFULLY!")
        await client.disconnect()
        return True
    except Exception as e:
        print("Result:", type(e), e)
        return False

async def main():
    for gw in gateways:
        ok = await test_gateway(gw)
        if ok:
            break

asyncio.run(main())
