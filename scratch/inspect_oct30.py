import json, base64, struct, datetime

with open('data/processed/dashboard_payload.json', 'r') as f:
    data = json.load(f)

c = data['continuous_1m']
n = c['n']
dt = struct.unpack(f'<{n}H', base64.b64decode(c['dt']))
do = struct.unpack(f'<{n}h', base64.b64decode(c['do']))
dh = struct.unpack(f'<{n}H', base64.b64decode(c['dh']))
dl = struct.unpack(f'<{n}H', base64.b64decode(c['dl']))
dc = struct.unpack(f'<{n}h', base64.b64decode(c['dc']))

cur_min = c['start_ts_min']
cur_open = c['start_open_d']

m5_bars = {}

for i in range(n):
    if i > 0:
        cur_min += dt[i]
        cur_open += do[i]
    ts = cur_min * 60
    b5 = (ts // 300) * 300
    if 1793368800 <= ts <= 1793390400: # 14:00 to 20:00 UTC
        o = round(cur_open * 0.1, 2)
        h = round((cur_open + dh[i]) * 0.1, 2)
        l = round((cur_open - dl[i]) * 0.1, 2)
        cl = round((cur_open + dc[i]) * 0.1, 2)
        if b5 not in m5_bars:
            m5_bars[b5] = {
                'time': datetime.datetime.utcfromtimestamp(b5).strftime('%H:%M'),
                'open': o,
                'high': h,
                'low': l,
                'close': cl
            }
        else:
            m5_bars[b5]['high'] = max(m5_bars[b5]['high'], h)
            m5_bars[b5]['low'] = min(m5_bars[b5]['low'], l)
            m5_bars[b5]['close'] = cl

print("=== 5-MINUTE BARS ON 2026-10-30 (14:00 - 20:00 UTC) ===")
for b5 in sorted(m5_bars.keys()):
    b = m5_bars[b5]
    print(f"{b['time']} UTC | O: {b['open']:7.2f} | H: {b['high']:7.2f} | L: {b['low']:7.2f} | C: {b['close']:7.2f}")
