# Job Monitor Bot — Android (Termux)

Запуск бота на Android-телефоне как сервер.

## Быстрый старт

### 1. Установите Termux

Скачайте **Termux** и **Termux:Boot** из F-Droid:
- [Termux](https://f-droid.org/packages/com.termux/)
- [Termux:Boot](https://f-droid.org/packages/com.termux.boot/)
- [Termux:API](https://f-droid.org/packages/com.termux.api/) (опционально)
- [Termux:Widget](https://f-droid.org/packages/com.termux.widget/) (опционально)

> **Важно:** Скачивайте только из F-Droid, не из Google Play (там устаревшая версия).

### 2. Запустите установку

Откройте Termux и выполните:

```bash
# Скачайте скрипт установки
curl -O https://raw.githubusercontent.com/Stiffy-git/job-monitor-bot/main/android/setup-termux.sh

# Запустите установку
bash setup-termux.sh
```

Или вручную:

```bash
pkg update -y && pkg upgrade -y
pkg install -y python git
pip install -r requirements.txt
pip install playwright
playwright install chromium
git clone https://github.com/Stiffy-git/job-monitor-bot.git
cd job-monitor-bot
```

### 3. Настройте бота

Отредактируйте `config.yaml`:

```bash
nano ~/job-monitor-bot/config.yaml
```

Вставьте:
```yaml
telegram:
  bot_token: "ВАШ_ТОКЕН"
  channel_id: "@ваш_канал"
```

### 4. Запустите бота

```bash
bash ~/start-bot.sh
```

### 5. Автозапуск

1. Установите **Termux:Boot** из F-Droid
2. Откройте Termux:Boot один раз
3. Перезагрузите телефон
4. Бот запустится автоматически

## Виджеты (опционально)

Установите **Termux:Widget** из F-Droid:

```bash
bash ~/job-monitor-bot/android/widget.sh
```

Добавьте виджет на рабочий стол:
- Длинное нажатие → Виджеты → Termux:Widget
- Выберите скрипт запуска/остановки

## Мониторинг

Бот работает в фоне. Для уведомлений:

```bash
# Запустите мониторинг (в отдельной сессии Termux)
bash ~/job-monitor-bot/android/monitor.sh
```

Бот будет автоматически перезапускаться при падении.

## Управление

```bash
# Запуск
bash ~/start-bot.sh

# Остановка
bash ~/stop-bot.sh

# Статус
pgrep -f "python3 main.py" && echo "Работает" || echo "Остановлен"

# Логи
tail -f ~/job-monitor-bot/bot.log
```

## Экономия батареи

1. **Termux:WakeLock** — предотвращает засыпание:
   ```bash
   termux-wake-lock
   ```

2. **Батарея:** Настройки → Батарея → Оптимизация → Termux → Не оптимизировать

3. **Фоновый режим:** Termux работает в фоне даже при закрытом приложении

## Проблемы

**Бот останавливается:**
- Проверьте🔋батарею: отключите оптимизацию для Termux
- Убедитесь, что termux-wake-lock активен

**Playwright не работает:**
```bash
playwright install chromium
playwright install-deps chromium
```

**Нет интернета:**
```bash
ping google.com
```
