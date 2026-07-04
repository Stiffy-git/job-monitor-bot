#!/bin/bash
# ============================================
# SSH-туннель для Avito
# Запускать на СВОЁМ ПК (не на сервере!)
# ============================================

SERVER_USER="${1:-root}"
SERVER_HOST="${2:-YOUR_SERVER_IP}"
LOCAL_PORT="${3:-1080}"

echo "🔧 Настройка SSH-туннеля для Avito..."
echo "   Сервер: ${SERVER_USER}@${SERVER_HOST}"
echo "   Локальный порт: ${LOCAL_PORT}"
echo ""

# Проверяем SSH
if ! command -v ssh &> /dev/null; then
    echo "❌ SSH не найден. Установите OpenSSH."
    exit 1
fi

# Запускаем туннель
echo "🚀 Запуск туннеля (работает в фоне)..."
ssh -D "${LOCAL_PORT}" -N -f "${SERVER_USER}@${SERVER_HOST}"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Туннель активен!"
    echo ""
    echo "Теперь на СЕРВЕРЕ в config.yaml добавьте:"
    echo "  proxy:"
    echo "    avito: \"socks5://127.0.0.1:${LOCAL_PORT}\""
    echo ""
    echo "⚠️  ВНИМАНИЕ: Чтобы туннель работал для Avito,"
    echo "   нужно сделать обратный проброс порта с сервера."
    echo ""
    echo "   На сервере выполните:"
    echo "   ssh -R ${LOCAL_PORT}:127.0.0.1:${LOCAL_PORT} ${SERVER_USER}@${SERVER_HOST}"
    echo ""
    echo "   Или используйте reverse-tunnel.sh"
    echo ""
    echo "Для остановки: kill \$(cat /tmp/avito-tunnel.pid 2>/dev/null) 2>/dev/null"
    echo "Или: pkill -f 'ssh -D ${LOCAL_PORT}'"
else
    echo "❌ Ошибка запуска туннеля"
    exit 1
fi
