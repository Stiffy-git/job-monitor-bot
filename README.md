# Job Monitor Bot

Telegram-бот для мониторинга вакансий ИТ-руководителей на 4 площадках.

## Возможности

- 🔴 hh.ru — вакансии с полными данными
- 💎 SuperJob — вакансии с зарплатами
- ⚡ Habr Career — вакансии с компаниями
- 🪙 Zarplata.ru — вакансии с деталями
- 📋 Автоматическая публикация каждый час (7:00-23:30)
- 📊 Дневной отчёт в 22:30
- 🔄 Ротация площадок —公平ное представительство
- 🚫 Без повторов в течение дня

## Установка

### Windows

1. Скачайте и установите Python 3.10+ с [python.org](https://www.python.org/downloads/)
   - **Обязательно** поставьте галочку "Add Python to PATH"

2. Скачайте папку `job-monitor-bot`

3. Запустите `install.bat`

4. Отредактируйте `config.yaml`:
   ```yaml
   telegram:
     bot_token: "ВАШ_ТОКЕН"
     channel_id: "@ваш_канал"
   ```

5. Запустите `start.bat`

### Linux (Ubuntu/Debian)

```bash
# 1. Установите Python
sudo apt update
sudo apt install python3 python3-pip

# 2. Перейдите в папку бота
cd /path/to/job-monitor-bot

# 3. Запустите установку
chmod +x install.sh
./install.sh

# 4. Настройте config.yaml
nano config.yaml

# 5. Запустите
python3 main.py
```

### Автозапуск (Linux systemd)

```bash
# Скопируйте сервисный файл
sudo cp job-monitor.service /etc/systemd/system/

# Отредактируйте путь
sudo nano /etc/systemd/system/job-monitor.service
# Измените WorkingDirectory на ваш путь

# Включите и запустите
sudo systemctl daemon-reload
sudo systemctl enable job-monitor
sudo systemctl start job-monitor

# Проверьте статус
sudo systemctl status job-monitor

# Логи
journalctl -u job-monitor -f
```

### Автозапуск (Windows)

1. Нажмите `Win+R`, введите `shell:startup`
2. Скопируйте `start.bat` в открывшуюся папку
3. Бот будет запускаться при входе в систему

## Настройка (config.yaml)

### Telegram

```yaml
telegram:
  bot_token: "123456:ABC-DEF..."  # От @BotFather
  channel_id: "@my_channel"       # Имя канала или chat_id
```

### Поисковые запросы

```yaml
search_queries:
  - "CIO"
  - "CTO"
  - "PMO"
  - "Product Manager IT"
  # ... добавьте свои
```

### Исключения

```yaml
filters:
  exclude_keywords:
    - "разработчик"    # Чистые разработчики
    - "developer"
    - "аналитик"       # Чистые аналитики
    - "analyst"
```

### Расписание

```yaml
monitoring:
  check_interval: 3600  # Интервал (сек)
  # Публикация: 7:00-23:30
  # Дневной отчёт: 22:30
```

## Формат постов

### Часовой пост

```
📋 Вакансии • 25 новых

🔴 hh (10)
  Технический директор / CTO — ООО Вайт Код
    Стратегия
  AI/ML Lead — Яндекс
    AI/ML

💎 SJ (5)
  Руководитель IT-проектов
    Управление

⚡ Habr (5)
  Руководитель команды разработки — VK
    Управление

🪙 ZP (5)
  Директор по ИТ — ООО Тест
    Цифровизация
```

### Дневной отчёт (22:30)

```
📊 Итоги дня — 03.07.2026

В базе: 435 • Показано: 25

🔴 hh (12)
  • Технический директор / CTO — ООО Вайт Код
  • AI/ML Lead — Яндекс
  ...+10 ещё

⚡ Habr (8)
  • Руководитель команды разработки — VK
  ...+6 ещё
```

## Тroubleshooting

### Бот не запускается

```bash
# Проверьте Python
python3 --version

# Проверьте зависимости
python3 -m pip install -r requirements.txt

# Проверьте Playwright
python3 -m playwright install chromium
```

### Telegram не работает

1. Проверьте token в `config.yaml`
2. Убедитесь, что бот добавлен в канал как админ
3. Для `channel_id` используйте `@channel_name` или `chat_id`

### Avito не работает

Avito блокирует IP датацентров. Используйте SSH-туннель:

```bash
# На вашем ПК:
ssh -R 1080:127.0.0.1:1080 user@server

# В config.yaml:
proxy:
  avito: "socks5://127.0.0.1:1080"
```

Подробнее: [AVITO-TUNNEL.md](AVITO-TUNNEL.md)

## Android (Termux)

Бот можно запустить на Android-телефоне через Termux:

```bash
# Установите Termux из F-Droid, затем:
pkg install python git
git clone https://github.com/Stiffy-git/job-monitor-bot.git
cd job-monitor-bot
pip install -r requirements.txt
pip install playwright && playwright install chromium
nano config.yaml  # настройте токен
python3 main.py
```

Подробнее: [android/README.md](android/README.md)
