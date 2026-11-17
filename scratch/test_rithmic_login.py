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
system = "Rithmic Test"
gw = "rituz00100.rithmic.com:443"

print(f"Connecting to {gw} with system: {system} for {user}...")

async def main():
    client = RithmicClient(
        user=user,
        password=pwd,
        system_name=system,
        app_name="SyndicateFloor",
        app_version="1.0.0",
        url=gw
    )
    try:
        await asyncio.wait_for(client.connect(), timeout=12)
        print("LOGIN SUCCESSFUL!")
        print("Accounts:", client.accounts)
        await client.disconnect()
    except Exception as e:
        print("Login Result:", type(e), e)

asyncio.run(main())
