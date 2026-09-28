#!/bin/bash
# ============================================
# Bode Hardware 网站一键部署脚本
# 用法: bash deploy.sh 你的域名.com
# 例如: bash deploy.sh bodehardware.com
# ============================================
set -e

# 域名参数（默认 bodehardware.com）
DOMAIN="${1:-bodehardware.com}"
REPO="https://github.com/wallavant8-ops/bode-website.git"
APP_DIR="/opt/bode-website"

echo "=========================================="
echo "  Bode Hardware 网站部署"
echo "  域名: $DOMAIN"
echo "=========================================="

# ---------- 1. 系统依赖 ----------
echo "[1/7] 安装系统依赖..."
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx

# ---------- 2. 拉取代码 ----------
echo "[2/7] 拉取代码..."
if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR"
    sudo git pull
else
    sudo rm -rf "$APP_DIR"
    sudo git clone "$REPO" "$APP_DIR"
    sudo chown -R "$USER:$USER" "$APP_DIR"
fi

# ---------- 3. 安装依赖 ----------
echo "[3/7] 安装 Python 依赖..."
cd "$APP_DIR"
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# ---------- 4. systemd 服务（开机自启 + 崩溃自动重启） ----------
echo "[4/7] 配置 systemd 服务..."
sudo tee /etc/systemd/system/bode-website.service > /dev/null << EOF
[Unit]
Description=Bode Hardware Website
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn app:app --bind 127.0.0.1:8000 --workers 2 --timeout 120
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable bode-website
sudo systemctl restart bode-website
echo "  ✅ 服务已启动"

# ---------- 5. Nginx 反代 ----------
echo "[5/7] 配置 Nginx..."
sudo tee /etc/nginx/sites-available/bode-website > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias $APP_DIR/static/;
        expires 30d;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/bode-website /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
echo "  ✅ Nginx 配置完成"

# ---------- 6. SSL 证书 ----------
echo "[6/7] 申请 SSL 证书（HTTPS）..."
sudo certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email --redirect || \
sudo certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --redirect
echo "  ✅ HTTPS 已启用"

# ---------- 7. 完成 ----------
echo "[7/7] 部署完成！"
echo ""
echo "=========================================="
echo "  ✅ 网站已上线"
echo "  网址: https://$DOMAIN"
echo "  后台: https://$DOMAIN/admin"
echo "=========================================="
echo ""
echo "后续更新代码: cd $APP_DIR && git pull && sudo systemctl restart bode-website"
echo "后台传图/改字: 直接访问 https://$DOMAIN/admin"
