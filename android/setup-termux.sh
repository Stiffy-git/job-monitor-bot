#!/bin/bash
# ============================================
# Job Monitor Bot — Установка в Termux
# ============================================

echo "🔧 Установка Job Monitor Bot в Termux"
echo ""

# Обновление пакетов
echo "📦 Обновление пакетов..."
pkg update -y && pkg upgrade -y

# Установка зависимостей
echo "📦 Установка Python и зависимостей..."
pkg install -y python git openssh

# Установка pip модулей
echo "📦 Установка Python модулей..."
pip install --upgrade pip
pip install -r requirements.txt

# Установка Playwright
echo "🌐 Установка Playwright..."
pip install playwright
playwright install chromium

# Клонирование репозитория
echo "📥 Загрузка бота..."
cd ~
if [ -d "job-monitor-bot" ]; then
    echo "Папка уже существует, обновляю..."
    cd job-monitor-bot
    git pull
else
    git clone https://github.com/Stiffy-git/job-monitor-bot.git
    cd job-monitor-bot
fi

# Настройка Termux для работы в фоне
echo "⚙️ Настройка Termux..."

# Установка Termux:Boot (автозапуск)
echo ""
echo "📱 Установите Termux:Boot из F-Droid:"
echo "   https://f-droid.org/packages/com.termux.boot/"
echo ""

# Установка Termux:API (для уведомлений)
echo "📱 Установите Termux:API из F-Droid:"
echo "   https://f-droid.org/packages/com.termux.api/"
echo ""

# Создание скрипта автозапуска
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start-bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/job-monitor-bot
python3 main.py &
EOF
chmod +x ~/.termux/boot/start-bot.sh

# Создание скрипта запуска
cat > ~/start-bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/job-monitor-bot
echo "🚀 Запуск Job Monitor Bot..."
python3 main.py
EOF
chmod +x ~/start-bot.sh

# Создание скрипта остановки
cat > ~/stop-bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
pkill -f "python3 main.py"
echo "⏹ Бот остановлен"
EOF
chmod +x ~/stop-bot.sh

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "   1. Отредактируйте ~/job-monitor-bot/config.yaml"
echo "      (вставьте bot_token и channel_id)"
echo ""
echo "   2. Запустите бота:"
echo "      bash ~/start-bot.sh"
echo ""
echo "   3. Для автозапуска при включении телефона:"
echo "      - Установите Termux:Boot из F-Droid"
echo "      - Откройте Termux:Boot один раз"
echo "      - Бот будет запускаться автоматически"
echo ""
echo "   4. Для остановки:"
echo "      bash ~/stop-bot.sh"
