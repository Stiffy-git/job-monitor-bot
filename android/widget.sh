#!/data/data/com.termux/files/usr/bin/bash
# ============================================
# Termux Widget — Быстрый запуск бота
# ============================================

# Установите Termux:Widget из F-Droid
# https://f-droid.org/packages/com.termux.widget/

# Создайте папку для виджетов
mkdir -p ~/.termux/widget

# Скрипт запуска
cat > ~/.termux/widget/start-bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/job-monitor-bot
python3 main.py &
termux-notification --id bot --title "Job Monitor Bot" --content "Работает" --ongoing
EOF
chmod +x ~/.termux/widget/start-bot.sh

# Скрипт остановки
cat > ~/.termux/widget/stop-bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
pkill -f "python3 main.py"
termux-notification --remove bot
termux-notification --title "Job Monitor Bot" --content "Остановлен"
EOF
chmod +x ~/.termux/widget/stop-bot.sh

# Скрипт статуса
cat > ~/.termux/widget/status-bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
if pgrep -f "python3 main.py" > /dev/null; then
    PID=$(pgrep -f "python3 main.py")
    termux-notification --title "Job Monitor Bot" --content "Работает (PID: $PID)"
else
    termux-notification --title "Job Monitor Bot" --content "Остановлен"
fi
EOF
chmod +x ~/.termux/widget/status-bot.sh

# Скрипт перезапуска
cat > ~/.termux/widget/restart-bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
pkill -f "python3 main.py"
sleep 2
cd ~/job-monitor-bot
python3 main.py &
termux-notification --id bot --title "Job Monitor Bot" --content "Перезапущен" --ongoing
EOF
chmod +x ~/.termux/widget/restart-bot.sh

echo "✅ Виджеты созданы!"
echo "Установите Termux:Widget и добавьте виджет на рабочий стол"
