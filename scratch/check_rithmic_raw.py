import asyncio
import ssl
from pathlib import Path
import websockets
import async_rithmic.protocol_buffers as pb

# Rithmic paper trading test gateway
gateway = "wss://rithmic-test.rithmic.com:443"

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
cert_path = Path(r"c:\Users\USER\OneDrive\Desktop\Agents Team\.venv\Lib\site-packages\async_rithmic\certificates\rithmic_ssl_cert_auth_params")
ssl_context.load_verify_locations(cert_path)

async def check():
    try:
        print("Connecting to Rithmic test gateway...")
        ws = await asyncio.wait_for(websockets.connect(gateway, ssl=ssl_context), timeout=10)
        print("Connected! Sending RequestRithmicSystemInfo (template 16)...")
        req = pb.request_rithmic_system_info_pb2.RequestRithmicSystemInfo()
        req.template_id = 16
        req.user_msg.append("test")
        buf = req.SerializeToString()
        
        # In rithmic proto length-prefixed or raw?
        await ws.send(buf)
        res = await asyncio.wait_for(ws.recv(), timeout=5)
        resp = pb.response_rithmic_system_info_pb2.ResponseRithmicSystemInfo()
        resp.ParseFromString(res)
        print("Systems available:", resp.system_name)
        await ws.close()
    except Exception as e:
        print("Rithmic test error:", type(e), e)

asyncio.run(check())
