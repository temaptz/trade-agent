# Руководство по развертыванию ИИ агента торговли биткойном

## 🚀 Быстрый старт

### 1. Автоматическая установка
```bash
# Клонирование и переход в директорию
git clone <repository-url>
cd bitcoin-trading-bot

# Автоматическая настройка
python setup.py
```

### 2. Ручная установка
```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt

# Установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull gemma2:9b

# Настройка конфигурации
cp .env.example .env
# Отредактируйте .env файл
```

## ⚙️ Конфигурация

### Обязательные настройки в .env:
```env
# API ключи Bybit (ОБЯЗАТЕЛЬНО)
BYBIT_API_KEY=your_api_key_here
BYBIT_SECRET_KEY=your_secret_key_here

# Режим тестирования (рекомендуется для начала)
BYBIT_TESTNET=True
```

### Дополнительные настройки:
```env
# Торговые параметры
TRADING_PAIR=BTCUSDT
TRADE_AMOUNT=0.001
MAX_RISK_PERCENT=2.0
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=4.0

# Интервалы (в секундах)
NEWS_UPDATE_INTERVAL=300
MARKET_ANALYSIS_INTERVAL=60
```

## 🏃‍♂️ Запуск

### Основные команды:
```bash
# Запуск в обычном режиме
python run_bot.py

# Запуск в режиме отладки
python run_bot.py --debug

# Тестовый режим (один цикл)
python run_bot.py --test

# Проверка статуса
python run_bot.py --status

# Настройка системы
python run_bot.py --setup
```

### Запуск в фоновом режиме:
```bash
# Linux/macOS
nohup python run_bot.py > trading_bot.log 2>&1 &

# Windows (PowerShell)
Start-Process python -ArgumentList "run_bot.py" -WindowStyle Hidden
```

### Остановка:
```bash
# Найти процесс
ps aux | grep "python run_bot.py"

# Остановить
kill <PID>

# Или использовать скрипт
./stop_bot.sh
```

## 🐳 Docker развертывание

### Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Копирование файлов
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Запуск Ollama и бота
CMD ["sh", "-c", "ollama serve & python run_bot.py"]
```

### docker-compose.yml:
```yaml
version: '3.8'

services:
  trading-bot:
    build: .
    environment:
      - BYBIT_API_KEY=${BYBIT_API_KEY}
      - BYBIT_SECRET_KEY=${BYBIT_SECRET_KEY}
      - BYBIT_TESTNET=true
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

### Запуск с Docker:
```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## ☁️ Облачное развертывание

### AWS EC2:
```bash
# Подключение к инстансу
ssh -i your-key.pem ubuntu@your-instance-ip

# Установка зависимостей
sudo apt update
sudo apt install python3-pip python3-venv git

# Клонирование и настройка
git clone <repository-url>
cd bitcoin-trading-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull gemma2:9b

# Настройка systemd сервиса
sudo nano /etc/systemd/system/trading-bot.service
```

### systemd сервис:
```ini
[Unit]
Description=Bitcoin Trading Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bitcoin-trading-bot
Environment=PATH=/home/ubuntu/bitcoin-trading-bot/venv/bin
ExecStart=/home/ubuntu/bitcoin-trading-bot/venv/bin/python run_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Управление сервисом:
```bash
# Включение автозапуска
sudo systemctl enable trading-bot

# Запуск
sudo systemctl start trading-bot

# Проверка статуса
sudo systemctl status trading-bot

# Просмотр логов
sudo journalctl -u trading-bot -f
```

## 🔧 Мониторинг и обслуживание

### Логи:
```bash
# Просмотр логов в реальном времени
tail -f logs/trading_$(date +%Y-%m-%d).log

# Поиск ошибок
grep -i error logs/trading_*.log

# Анализ производительности
grep "PnL" logs/trading_*.log
```

### База данных:
```bash
# Просмотр базы данных
sqlite3 trading_data.db

# Экспорт данных
python -c "
import asyncio
from utils import DataExporter
asyncio.run(DataExporter.export_trading_data('trading_data.db'))
"

# Резервное копирование
cp trading_data.db backups/trading_data_$(date +%Y%m%d_%H%M%S).db
```

### Мониторинг системы:
```bash
# Проверка процессов
ps aux | grep python

# Использование памяти
free -h

# Использование диска
df -h

# Сетевые соединения
netstat -tulpn | grep python
```

## 🛡️ Безопасность

### Рекомендации:
1. **Используйте тестовую сеть** для начала
2. **Ограничьте размер позиций** на начальном этапе
3. **Регулярно создавайте резервные копии**
4. **Мониторьте логи** на подозрительную активность
5. **Используйте отдельный аккаунт** для торговли

### Настройка файрвола:
```bash
# Ubuntu/Debian
sudo ufw allow ssh
sudo ufw allow 11434  # Ollama
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-port=11434/tcp
sudo firewall-cmd --reload
```

### Мониторинг безопасности:
```bash
# Проверка подозрительной активности
grep -i "error\|failed\|exception" logs/trading_*.log

# Мониторинг сетевых соединений
ss -tulpn | grep python

# Проверка целостности файлов
sha256sum *.py
```

## 📊 Масштабирование

### Горизонтальное масштабирование:
```yaml
# docker-compose.yml для множественных инстансов
version: '3.8'

services:
  trading-bot-1:
    build: .
    environment:
      - INSTANCE_ID=1
      - TRADING_PAIR=BTCUSDT
    volumes:
      - ./data/instance1:/app/data
    restart: unless-stopped

  trading-bot-2:
    build: .
    environment:
      - INSTANCE_ID=2
      - TRADING_PAIR=ETHUSDT
    volumes:
      - ./data/instance2:/app/data
    restart: unless-stopped
```

### Вертикальное масштабирование:
```bash
# Увеличение ресурсов для Ollama
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=2

# Оптимизация Python
export PYTHONOPTIMIZE=1
export PYTHONUNBUFFERED=1
```

## 🔄 Обновления

### Обновление кода:
```bash
# Создание резервной копии
cp -r . ../backup-$(date +%Y%m%d)

# Обновление из репозитория
git pull origin main

# Обновление зависимостей
pip install -r requirements.txt --upgrade

# Перезапуск сервиса
sudo systemctl restart trading-bot
```

### Обновление модели Ollama:
```bash
# Обновление модели
ollama pull gemma2:9b

# Перезапуск Ollama
pkill ollama
ollama serve &
```

## 🚨 Устранение неполадок

### Частые проблемы:

1. **Ollama не отвечает:**
```bash
# Проверка статуса
curl http://localhost:11434/api/tags

# Перезапуск
pkill ollama
ollama serve &
```

2. **Ошибки API Bybit:**
```bash
# Проверка ключей
python -c "from config import settings; print('API Key:', settings.bybit_api_key[:10] + '...')"

# Проверка тестовой сети
python -c "from config import settings; print('Testnet:', settings.bybit_testnet)"
```

3. **Проблемы с базой данных:**
```bash
# Проверка файла
ls -la trading_data.db

# Восстановление из бэкапа
cp backups/trading_data_*.db trading_data.db
```

4. **Высокое использование памяти:**
```bash
# Мониторинг памяти
htop

# Ограничение памяти для Ollama
export OLLAMA_MAX_LOADED_MODELS=1
```

### Логи для диагностики:
```bash
# Полные логи
tail -f logs/trading_$(date +%Y-%m-%d).log

# Только ошибки
grep -i error logs/trading_*.log

# Анализ производительности
grep "cycle" logs/trading_*.log | tail -20
```

## 📞 Поддержка

### Полезные команды:
```bash
# Проверка статуса системы
python run_bot.py --status

# Тестовый запуск
python run_bot.py --test

# Проверка конфигурации
python -c "from config import settings; print(settings.__dict__)"

# Экспорт данных
python -c "
import asyncio
from utils import DataExporter
asyncio.run(DataExporter.export_trading_data('trading_data.db'))
"
```

### Контакты:
- GitHub Issues: [Создать issue](https://github.com/your-repo/issues)
- Email: support@example.com
- Telegram: @your_support_bot

---

**Удачного развертывания! 🚀**