#!/bin/bash

set -e

BOT_DIR="/opt/invitor-bot"
SERVICE_FILE="/etc/systemd/system/invitor-bot.service"
PYTHON_BIN="/usr/bin/python3"

echo "📦 Установка системных зависимостей..."
dnf update -y
dnf install -y python3 python3-pip git redis unzip

echo "🚀 Запуск Redis..."
systemctl enable --now redis

echo "📁 Копирование проекта в $BOT_DIR..."
mkdir -p "$BOT_DIR"
cp -r . "$BOT_DIR"

echo "📁 Переход в каталог проекта..."
cd "$BOT_DIR"

if [ ! -f ".env" ]; then
  echo "⚠️ Файл .env не найден. Создаю шаблон..."
  cat <<EOF > .env
BOT_TOKEN=xxx:your_bot_token
OWNER_USERNAME=flekks
OWNER_ID=463722824
ADMIN_IDS=439516148,463722824
CHANNEL_ID=1002666650526
REDIS_HOST=localhost
REDIS_PORT=6379
USE_REDIS=True
EOF
  echo "⚠️ Заполни .env вручную: nano $BOT_DIR/.env"
fi

echo "📜 Создание requirements.txt (если нет)..."
cat <<EOF > requirements.txt
aiogram==3.4.1
aiosqlite
redis
python-dotenv
EOF

echo "📦 Установка Python-зависимостей..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

echo "🛠️ Создание systemd-сервиса..."
cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Telegram Bot - Invitor
After=network.target redis.service

[Service]
User=root
WorkingDirectory=$BOT_DIR
ExecStart=$PYTHON_BIN $BOT_DIR/main.py
Restart=always
EnvironmentFile=$BOT_DIR/.env
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Перезагрузка systemd и запуск бота..."
systemctl daemon-reexec
systemctl daemon-reload
systemctl enable invitor-bot
systemctl restart invitor-bot

echo "✅ Установка завершена. Статус бота:"
systemctl status invitor-bot --no-pager
