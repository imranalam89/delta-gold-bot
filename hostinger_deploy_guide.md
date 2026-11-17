# Hostinger VPS Isolated Deployment Guide (New Dedicated Port 5055)

> [!IMPORTANT]
> **Zero Conflict Guarantee**: Your existing bot running on **`62.72.31.29:5050`** remains **100% untouched and unaffected**. This new 16-Agent Floor runs in its own separate directory and uses dedicated port **`5055`**.

---

## 1. Summary of Isolation

| Component | Existing Bot | **New Syndicate Agent Floor** |
| :--- | :--- | :--- |
| **Port** | `5050` | **`5055`** |
| **Dashboard URL** | `http://62.72.31.29:5050/` | **`http://62.72.31.29:5055/`** |
| **Directory** | Existing folder | **`/var/www/syndicate_floor/`** |
| **Systemd Service** | Existing service | **`syndicate_floor.service`** |
| **Data Feed** | Existing | **Tradovate GC CME Futures (Free)** |
| **Execution** | Existing | **Delta Exchange India (Account 74634658)** |

---

## 2. Step-by-Step Installation on Hostinger VPS

### Step 1: Connect via SSH
```bash
ssh root@62.72.31.29
```

### Step 2: Create a Dedicated Directory for the New Agents
```bash
mkdir -p /var/www/syndicate_floor
cd /var/www/syndicate_floor
```

### Step 3: Copy / Upload the Files
From your Windows machine, upload this workspace to the new folder:
```powershell
scp -r "c:\Users\USER\OneDrive\Desktop\Agents Team\*" root@62.72.31.29:/var/www/syndicate_floor/
```

### Step 4: Configure Credentials in `.env`
On the VPS inside `/var/www/syndicate_floor`:
```bash
cp .env.example .env
nano .env
```
Ensure the port is set to **`5055`**:
```ini
# Tradovate CME Market Data (Free Live Gold GC Feed)
TRADOVATE_USER="YOUR_TRADOVATE_USERNAME"
TRADOVATE_PASS="YOUR_TRADOVATE_PASSWORD"
TRADOVATE_APP_ID="SampleApp"
TRADOVATE_ENV="live"

# Delta Exchange India (Execution Account 74634658)
DELTA_API_KEY="YOUR_DELTA_API_KEY"
DELTA_API_SECRET="YOUR_DELTA_API_SECRET"
DELTA_ACCOUNT_ID="74634658"

# Isolated Port (Leaves 5050 untouched)
PORT=5055
```
Press `Ctrl+O` then `Enter` to save, and `Ctrl+X` to exit.

---

## 3. Create Independent Background Service (`syndicate_floor.service`)

Create a dedicated systemd service so this new floor runs 24/7 independently:
```bash
sudo nano /etc/systemd/system/syndicate_floor.service
```

Paste the following:
```ini
[Unit]
Description=Syndicate Alpha 16-Agent Live Floor (Port 5055)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/syndicate_floor
ExecStart=/usr/bin/python3 /var/www/syndicate_floor/hostinger_live_bridge.py
Restart=always
RestartSec=5
Environment=PORT=5055

[Install]
WantedBy=multi-user.target
```

Enable and start the new service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable syndicate_floor
sudo systemctl start syndicate_floor
sudo systemctl status syndicate_floor
```

---

## 4. Open Port 5055 in Firewall (UFW)

If UFW firewall is enabled on your VPS, allow port 5055:
```bash
sudo ufw allow 5055/tcp
sudo ufw status
```

---

## 5. Access Both Dashboards Simultaneously

- **Existing Bot**: `http://62.72.31.29:5050/` (Running continuously as before)
- **New 16-Agent Floor**: `http://62.72.31.29:5055/` (Running on the new Tradovate GC + Delta bridge)
