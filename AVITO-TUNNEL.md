# Настройка Avito через SSH-туннель

## Зачем
Avito блокирует IP датацентров. Туннель направляет запросы Avito через твой домашний IP.

## Схема

```
┌─────────────┐      SSH       ┌─────────────┐      ┌─────────┐
│   Сервер    │ ◄────────────── │  Твой ПК    │ ──── │  Avito  │
│   (бот)     │   reverse      │  (домашний  │      │         │
│             │   tunnel       │     IP)     │      │         │
└─────────────┘                └─────────────┘      └─────────┘
     │                               │
     │ socks5://127.0.0.1:1080       │
     └───────────────────────────────┘
```

## Пошаговая настройка

### Шаг 1: Подготовка сервера

На сервере разрешить reverse-туннели:

```bash
# Отредактируйте /etc/ssh/sshd_config
sudo nano /etc/ssh/sshd_config

# Добавьте или измените:
GatewayPorts no
AllowTcpForwarding yes
ClientAliveInterval 60
ClientAliveCountMax 3

# Перезапустите SSH
sudo systemctl restart sshd
```

### Шаг 2: Запуск туннеля на ПК

**Linux/macOS:**
```bash
chmod +x reverse-tunnel.sh
./reverse-tunnel.sh root ВАШ_IP_СЕРВЕРА
```

**Windows (PowerShell):**
```powershell
ssh -R 1080:127.0.0.1:1080 -N -o ServerAliveInterval=60 root@ВАШ_IP_СЕРВЕРА
```

**Windows (двойной клик):**
Запустите `reverse-tunnel.bat` (измените IP в файле)

### Шаг 3: Настройка бота на сервере

Отредактируйте `config.yaml`:

```yaml
proxy:
  avito: "socks5://127.0.0.1:1080"
```

### Шаг 4: Перезапуск бота

```bash
cd /opt/mimo-code/upload/job-monitor-bot
python3 main.py
```

## Автозапуск туннеля

### Linux (systemd)

Создайте файл `~/.config/systemd/user/avito-tunnel.service`:

```ini
[Unit]
Description=Avito SSH Tunnel
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/ssh -R 1080:127.0.0.1:1080 -N -o ServerAliveInterval=60 root@ВАШ_IP_СЕРВЕРА
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

```bash
systemctl --user enable avito-tunnel
systemctl --user start avito-tunnel
```

### Windows (автозагрузка)

1. Создайте ярлык для `reverse-tunnel.bat`
2. Нажмите Win+R → `shell:startup`
3. Переместите ярлык в папку автозагрузки

## Проверка

На сервере:
```bash
# Проверяем что туннель работает
curl --socks5 127.0.0.1:1080 http://httpbin.org/ip

# Должен показать IP твоего ПК, а не сервера
```

## Устранение проблем

**Туннель не подключается:**
- Проверь SSH-доступ к серверу: `ssh root@IP`
- Проверь что порт 1080 не занят

**Avito всё ещё блокирует:**
- Проверь что туннель работает: `curl --socks5 127.0.0.1:1080 http://httpbin.org/ip`
- IP должен быть домашний, не серверный

**Бот не видит прокси:**
- Проверь `config.yaml`: `proxy.avito: "socks5://127.0.0.1:1080"`
- Перезапусти бота
