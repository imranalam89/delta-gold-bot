# Hostinger VPS Deployment Guide — Delta Gold 50x Bot (Port 5055)

> [!IMPORTANT]
> **Zero Conflict Guarantee**:
> - Your existing bot running on **`62.72.31.29:5050`** remains **100% untouched and running continuously**.
> - This new bot runs in its own dedicated directory **`/var/www/delta_gold_bot/`** on dedicated port **`5055`**.
> - Uses **100% in-memory circular buffers (RAM)**: Zero disk space consumed on your Hostinger VPS!

---

## 1. System Overview

| Parameter | Existing Bot | **New Delta Gold 50x Bot** |
| :--- | :--- | :--- |
| **Port** | `5050` | **`5055`** |
| **Dashboard URL** | `http://62.72.31.29:5050/` | **`http://62.72.31.29:5055/`** |
| **Directory** | Existing bot folder | **`/var/www/delta_gold_bot/`** |
| **Systemd Service**| Existing service | **`delta_gold_bot.service`** |
| **Instrument** | Existing | **Delta Exchange India XAUTUSD Perpetual** |
| **Leverage** | Existing | **50x Leverage** ($1\text{ Contract} = 0.001\text{ oz}$) |
| **Risk / Sizing** | Existing | **Fixed \$5.00 Risk** ($\text{Lots} = \text{round}(\text{qty\_oz} \times 1000)$) |
| **Strategy Rules** | Existing | **Locked #1 Merged Super-Champion** (0.85x SL, 180m Time Exit, 40R Trail) |
| **Storage Mode** | Existing | **RAM Ring Buffer (0 MB Disk Usage)** |

---

## 2. Fast Step-by-Step Deployment Commands

### Step 1: Connect to your Hostinger VPS via SSH
Open your terminal (PowerShell or Bash) and run:
```bash
ssh root@62.72.31.29
```

---

### Step 2: Create the Dedicated Directory
```bash
mkdir -p /var/www/delta_gold_bot
cd /var/www/delta_gold_bot
```

---

### Step 3: Upload the Bot Code & Live Journal from Windows
From your local Windows PowerShell terminal:
```powershell
scp "c:\Users\USER\OneDrive\Desktop\Agents Team\hostinger_delta_gold_live.py" root@62.72.31.29:/var/www/delta_gold_bot/
scp "c:\Users\USER\OneDrive\Desktop\Agents Team\live_journal.html" root@62.72.31.29:/var/www/delta_gold_bot/
scp "c:\Users\USER\OneDrive\Desktop\Agents Team\.env" root@62.72.31.29:/var/www/delta_gold_bot/
scp "c:\Users\USER\OneDrive\Desktop\Agents Team\delta_gold_bot.service" root@62.72.31.29:/etc/systemd/system/
```

---

### Step 4: Configure Credentials (`.env`)
On the VPS inside `/var/www/delta_gold_bot`:
```bash
cat << 'EOF' > /var/www/delta_gold_bot/.env
DELTA_API_KEY="YOUR_DELTA_API_KEY"
DELTA_API_SECRET="YOUR_DELTA_API_SECRET"
DELTA_ACCOUNT_ID="74634658"
PORT=5055
LEVERAGE=50
FIXED_RISK_USD=5.0
MAX_HOLD_MINS=180
EOF
```
*(Replace `YOUR_DELTA_API_KEY` and `YOUR_DELTA_API_SECRET` with your real Delta Exchange India keys)*.

---

### Step 5: Enable Firewall for Port 5055
```bash
sudo ufw allow 5055/tcp
sudo ufw reload
```

---

### Step 6: Start the Background Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable delta_gold_bot
sudo systemctl restart delta_gold_bot
sudo systemctl status delta_gold_bot
```

---

## 3. Verify Both Dashboards

Once started, both dashboards are simultaneously accessible in your browser:
1. **Existing Bot**: [http://62.72.31.29:5050/](http://62.72.31.29:5050/)
2. **New Delta Gold 50x Bot**: [http://62.72.31.29:5055/](http://62.72.31.29:5055/)

---

## 4. Useful Management Commands

- **View Live Logs**:
  ```bash
  journalctl -u delta_gold_bot -f
  ```
- **Restart Bot**:
  ```bash
  sudo systemctl restart delta_gold_bot
  ```
- **Stop Bot**:
  ```bash
  sudo systemctl stop delta_gold_bot
  ```
