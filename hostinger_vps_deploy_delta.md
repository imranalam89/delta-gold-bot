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

## 2. Fast 1-Step Deployment via GitHub (Automated)

### Step 1: Connect to your Hostinger VPS via SSH
Open your terminal (PowerShell or Bash) and run:
```bash
ssh root@62.72.31.29
```

---

### Step 2: Clone from GitHub & Run Automated Setup
Just like your previous `agent-brain` setup, you don't need to type or bash any manual `.env` commands!

```bash
# 1. Clone the repository into its dedicated directory
git clone https://github.com/imranalam89/delta-gold-bot.git /var/www/delta_gold_bot
cd /var/www/delta_gold_bot

# 2. Run the 1-step automated setup script
bash setup_hostinger.sh
```

`setup_hostinger.sh` automatically:
- Installs Python dependencies if missing
- Copies `.env.example` to `.env` (no manual bash typing needed)
- Configures and starts `delta_gold_bot.service` (Port 5055)
- Configures firewall rules for port 5055

---

### Step 3: Routine Updates via GitHub
Whenever you push new updates from your Windows machine:
```bash
cd /var/www/delta_gold_bot
git pull origin main
systemctl restart delta_gold_bot
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
