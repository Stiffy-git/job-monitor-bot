#!/data/data/com.termux/files/usr/bin/bash
# ============================================
# Мониторинг бота + уведомления
# ============================================

BOT_PROCESS="python3 main.py"
CHECK_INTERVAL=300  # 5 минут

check_bot() {
    if pgrep -f "$BOT_PROCESS" > /dev/null; then
        return 0  # Работает
    else
        return 1  # Остановлен
    fi
}

restart_bot() {
    cd ~/job-monitor-bot
    python3 main.py &
    sleep 2
    if check_bot; then
        termux-notification --id bot --title "Job Monitor Bot" --content "Перезапущен автоматически" --ongoing
        termux-vibrate -f
    fi
}

# Бесконечный цикл мониторинга
while true; do
    if check_bot; then
        # Бот работает — уведомление не обновляем
        : 
    else
        # Бот остановлен — перезапускаем
        termux-notification --id bot --title "Job Monitor Bot" --content "Перезапуск..." --ongoing
        restart_bot
    fi
    
    sleep $CHECK_INTERVAL
done
