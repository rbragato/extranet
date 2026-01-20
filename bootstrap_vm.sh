#!/usr/bin/env bash
set -e

APP_DIR="$HOME/extranet"

echo "[1/4] Install Docker if missing..."
if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl gnupg

  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  sudo usermod -aG docker "$USER"
  echo "Docker installed. Running with sudo for this session (no logout needed)."
fi

echo "[2/4] Go to project dir..."
cd "$APP_DIR"

echo "[3/4] Creating .env if missing..."

if [ ! -f ".env" ]; then
cat > .env <<EOF
# Flask
SECRET_KEY=dev-secret-key

# MySQL
MYSQL_HOST=db
MYSQL_PORT=3306
MYSQL_DATABASE=extranet
MYSQL_USER=extranet_user
MYSQL_PASSWORD=extranet_pass
MYSQL_ROOT_PASSWORD=rootpass

# Seed admin
SEED_ADMIN_EMAIL=admin@local
SEED_ADMIN_PASSWORD=Admin123!
SEED_ADMIN_FIRSTNAME=Admin
SEED_ADMIN_LASTNAME=Local
EOF
echo ".env generated"
fi


echo "[4/4] Build + run..."
sudo docker compose up -d --build

IP="$(hostname -I | awk '{print $1}')"
echo "OK:"
echo " - App:        http://$IP:5000"
echo " - phpMyAdmin: http://$IP:8080"
