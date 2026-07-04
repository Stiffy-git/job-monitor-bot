#!/bin/bash
# ============================================
# Job Monitor Bot — Установка (Linux/macOS)
# ============================================

echo "🔧 Установка Job Monitor Bot..."
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите:"
    echo "   Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "   macOS: brew install python3"
    exit 1
fi

PYTHON=$(command -v python3)
echo "✅ Python: $($PYTHON --version)"

# Проверка pip
if ! $PYTHON -m pip --version &> /dev/null; then
    echo "❌ pip не найден. Установите:"
    echo "   $PYTHON -m ensurepip --upgrade"
    exit 1
fi

echo ""
echo "📦 Установка зависимостей..."
$PYTHON -m pip install -r requirements.txt --quiet

echo ""
echo "🌐 Установка Playwright..."
$PYTHON -m playwright install chromium
$PYTHON -m playwright install-deps chromium 2>/dev/null

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "   1. Отредактируйте config.yaml (вставьте bot_token и channel_id)"
echo "   2. Запустите: $PYTHON main.py"
echo ""
echo "💡 Для автозапуска:"
echo "   cp job-monitor.service /etc/systemd/system/"
echo "   sudo systemctl enable job-monitor"
echo "   sudo systemctl start job-monitor"
