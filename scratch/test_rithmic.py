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

async def test():
    client = RithmicClient(
        user=user,
        password=pwd,
        system_name=system,
        app_name="SyndicateFloor",
        app_version="1.0.0"
    )
    try:
        await client.connect()
        print("Rithmic Connect SUCCESS!")
        await client.disconnect()
    except Exception as e:
        print("Rithmic Connect ERROR:", type(e), e)

asyncio.run(test())
