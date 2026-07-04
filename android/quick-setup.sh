#!/data/data/com.termux/files/usr/bin/bash
# ============================================
# Быстрая установка (одна команда)
# ============================================

echo "🚀 Быстрая установка Job Monitor Bot"
echo ""

# Установка зависимостей
pkg update -y -q
pkg install -y -q python git

# Клонирование и установка
cd ~
git clone --depth 1 https://github.com/Stiffy-git/job-monitor-bot.git 2>/dev/null || cd job-monitor-bot && git pull
cd job-monitor-bot

pip install -q -r requirements.txt
pip install -q playwright
playwright install chromium 2>/dev/null

# Настройка автозапуска
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start-bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/job-monitor-bot
python3 main.py &
EOF
chmod +x ~/.termux/boot/start-bot.sh

# Скрипты управления
cat > ~/start-bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/job-monitor-bot
python3 main.py
EOF
chmod +x ~/start-bot.sh

cat > ~/stop-bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
pkill -f "python3 main.py"
echo "⏹ Остановлен"
EOF
chmod +x ~/stop-bot.sh

echo ""
echo "✅ Готово!"
echo "Настройте: nano ~/job-monitor-bot/config.yaml"
echo "Запуск: bash ~/start-bot.sh"
