#!/bin/bash
# ==============================================================================
# 🏛️ DELTA GOLD 50x LIVE BOT | AUTONOMOUS 24/7 DEPLOYMENT (HOSTINGER VPS)
# Target Host: 62.72.31.29 (Port 5055 Dedicated — Port 5050 Untouched)
# Strategy: 👑 #1 Merged Super-Champion (≥4/6 + 15m Sniper)
# ==============================================================================

set -e

echo "=================================================================="
echo "  🏛️ DELTA GOLD 50x BOT 24/7 DEPLOYMENT — HOSTINGER VPS         "
echo "  Strategy: #1 Merged Super-Champion (≥4/6 + 15m Sniper)         "
echo "  Port: 5055 (Zero conflict with existing port 5050 bot)        "
echo "=================================================================="

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📍 Application Directory: $APP_DIR"

# 1. Check Python 3
echo "📦 Step 1: Checking Python 3..."
if command -v python3 &>/dev/null; then
    echo "✅ Python 3 is installed: $(python3 --version)"
else
    echo "Installing Python 3..."
    dnf install -y python3 python3-pip 2>/dev/null || (apt-get update && apt-get install -y python3 python3-pip)
fi

# 2. Check for .env file (Automatic copy just like agent-brain)
echo "🔑 Step 2: Checking environment configuration..."
if [ ! -f "$APP_DIR/.env" ]; then
    echo "⚠️ .env file not found. Auto-generating from .env.example..."
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo "✅ .env created. If you have custom API keys, you can edit $APP_DIR/.env"
else
    echo "✅ Existing .env found."
fi

# 3. Install Systemd Service for 24/7 Delta Gold Bot
echo "⚙️ Step 3: Installing 24/7 systemd service (delta_gold_bot.service)..."
cat << EOF > /etc/systemd/system/delta_gold_bot.service
[Unit]
Description=Delta Exchange India XAUTUSD 50x Live Bot (Port 5055)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/python3 $APP_DIR/hostinger_delta_gold_live.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PORT=5055
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# 4. Open Firewall Port 5055
echo "🛡️ Step 4: Configuring firewall for dedicated Port 5055..."
if command -v ufw &>/dev/null; then
    ufw allow 5055/tcp 2>/dev/null || true
    ufw reload 2>/dev/null || true
elif command -v firewall-cmd &>/dev/null; then
    firewall-cmd --permanent --add-port=5055/tcp 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
fi

# CSF Firewall support if installed
if [ -f /etc/csf/csf.conf ]; then
    if ! grep -q "5055" /etc/csf/csf.conf; then
        sed -i 's/TCP_IN = "/TCP_IN = "5055,/g' /etc/csf/csf.conf
        csf -r 2>/dev/null || true
    fi
fi

# 5. Reload & Start Service
echo "🚀 Step 5: Reloading systemd and restarting delta_gold_bot service..."
systemctl daemon-reload
systemctl enable delta_gold_bot.service
systemctl restart delta_gold_bot.service

echo ""
echo "=================================================================="
echo "  ✅ DELTA GOLD 50x BOT SUCCESSFULLY DEPLOYED & RUNNING 24/7!     "
echo "=================================================================="
echo "  📊 Live Journal Cockpit:  http://62.72.31.29:5055"
echo "  🤖 Check Status:          systemctl status delta_gold_bot"
echo "  📋 Live Journal Logs:     journalctl -u delta_gold_bot -f"
echo "  🌐 Existing Port 5050:    100% UNTOUCHED & CONTINUOUS"
echo "=================================================================="
