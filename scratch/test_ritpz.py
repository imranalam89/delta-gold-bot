import asyncio
import ssl
from pathlib import Path
import websockets
import async_rithmic.protocol_buffers as pb

# Let's test endpoints
gateways = [
    "wss://ritpz00100.rithmic.com:443",
    "wss://ritpz01000.rithmic.com:443",
    "wss://ritpz00010.rithmic.com:443",
    "wss://rituz00100.rithmic.com:443",
]

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
cert_path = Path(r"c:\Users\USER\OneDrive\Desktop\Agents Team\.venv\Lib\site-packages\async_rithmic\certificates\rithmic_ssl_cert_auth_params")
ssl_context.load_verify_locations(cert_path)

async def check(gw):
    try:
        ws = await asyncio.wait_for(websockets.connect(gw, ssl=ssl_context), timeout=5)
        req = pb.request_rithmic_system_info_pb2.RequestRithmicSystemInfo()
        req.template_id = 16
        req.user_msg.append("test")
        await ws.send(req.SerializeToString())
        res = await asyncio.wait_for(ws.recv(), timeout=5)
        resp = pb.response_rithmic_system_info_pb2.ResponseRithmicSystemInfo()
        resp.ParseFromString(res)
        print(f"[{gw}] SUCCESS! Systems: {resp.system_name}")
        await ws.close()
    except Exception as e:
        print(f"[{gw}] Error: {e}")

async def main():
    for gw in gateways:
        await check(gw)

asyncio.run(main())
