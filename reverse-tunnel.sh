#!/bin/bash
# ============================================
# Reverse SSH-туннель для Avito
# Запускать на СВОЁМ ПК!
#
# Как это работает:
# 1. Твой ПК подключается к серверу
# 2. Пробрасывает порт: сервер:1080 → твой_ПК:1080
# 3. Бот на сервере ходит на Avito через socks5://127.0.0.1:1080
# 4. Трафик идёт через твой домашний IP
# ============================================

SERVER_USER="${1:-root}"
SERVER_HOST="${2:-YOUR_SERVER_IP}"
TUNNEL_PORT="${3:-1080}"

echo "🔧 Reverse SSH-туннель для Avito"
echo "   Сервер: ${SERVER_USER}@${SERVER_HOST}"
echo "   Порт на сервере: ${TUNNEL_PORT}"
echo ""

# Создаём SOCKS-прокси на локальном порту
# и пробрасываем его на сервер
echo "🚀 Запуск reverse-туннеля..."
echo "   Сервер:${TUNNEL_PORT} → 127.0.0.1:${TUNNEL_PORT} (твой ПК)"
echo ""

ssh -R "${TUNNEL_PORT}:127.0.0.1:${TUNNEL_PORT}" \
    -N \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    "${SERVER_USER}@${SERVER_HOST}"

echo "Туннель закрыт"
