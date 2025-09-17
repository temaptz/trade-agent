"""
Скрипт развертывания торгового бота
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def create_systemd_service():
    """Создание systemd сервиса для Linux"""
    service_content = f"""[Unit]
Description=Trading Bot AI Agent
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'ubuntu')}
WorkingDirectory={os.getcwd()}
ExecStart={sys.executable} {os.path.join(os.getcwd(), 'main.py')} continuous 30
Restart=always
RestartSec=10
Environment=PYTHONPATH={os.getcwd()}

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path("/etc/systemd/system/trading-bot.service")
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        print(f"✅ Systemd сервис создан: {service_file}")
        return True
    except PermissionError:
        print("❌ Нет прав для создания systemd сервиса")
        print("Запустите с sudo или создайте сервис вручную")
        return False
    except Exception as e:
        print(f"❌ Ошибка создания сервиса: {e}")
        return False

def create_dockerfile():
    """Создание Dockerfile"""
    dockerfile_content = """FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Установка Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Установка рабочей директории
WORKDIR /app

# Копирование файлов
COPY requirements.txt .
COPY . .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Создание пользователя
RUN useradd -m -u 1000 trader
RUN chown -R trader:trader /app
USER trader

# Запуск Ollama в фоне и бота
CMD ["sh", "-c", "ollama serve & python main.py continuous 30"]
"""
    
    try:
        with open("Dockerfile", 'w') as f:
            f.write(dockerfile_content)
        print("✅ Dockerfile создан")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания Dockerfile: {e}")
        return False

def create_docker_compose():
    """Создание docker-compose.yml"""
    compose_content = """version: '3.8'

services:
  trading-bot:
    build: .
    ports:
      - "11434:11434"  # Ollama
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./.env:/app/.env
    environment:
      - OLLAMA_BASE_URL=http://localhost:11434
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:11434/api/tags')"]
      interval: 30s
      timeout: 10s
      retries: 3
"""
    
    try:
        with open("docker-compose.yml", 'w') as f:
            f.write(compose_content)
        print("✅ docker-compose.yml создан")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания docker-compose.yml: {e}")
        return False

def create_nginx_config():
    """Создание конфигурации Nginx для мониторинга"""
    nginx_content = """server {
    listen 80;
    server_name trading-bot.local;

    location / {
        proxy_pass http://localhost:11434;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /logs {
        alias /path/to/trading-bot/logs;
        autoindex on;
    }
}
"""
    
    try:
        with open("nginx.conf", 'w') as f:
            f.write(nginx_content)
        print("✅ nginx.conf создан")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания nginx.conf: {e}")
        return False

def create_monitoring_script():
    """Создание скрипта мониторинга"""
    script_content = """#!/bin/bash
# Скрипт мониторинга торгового бота

LOG_FILE="trading_bot.log"
ALERT_EMAIL="admin@example.com"

# Проверка статуса процесса
check_process() {
    if pgrep -f "main.py" > /dev/null; then
        echo "✅ Торговый бот работает"
        return 0
    else
        echo "❌ Торговый бот не работает"
        return 1
    fi
}

# Проверка логов на ошибки
check_errors() {
    if [ -f "$LOG_FILE" ]; then
        ERROR_COUNT=$(tail -n 100 "$LOG_FILE" | grep -c "ERROR")
        if [ "$ERROR_COUNT" -gt 5 ]; then
            echo "⚠️  Много ошибок в логах: $ERROR_COUNT"
            return 1
        fi
    fi
    return 0
}

# Проверка использования ресурсов
check_resources() {
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    
    if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
        echo "⚠️  Высокое использование CPU: $CPU_USAGE%"
        return 1
    fi
    
    if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
        echo "⚠️  Высокое использование памяти: $MEMORY_USAGE%"
        return 1
    fi
    
    return 0
}

# Основная функция мониторинга
main() {
    echo "🔍 Проверка торгового бота - $(date)"
    
    STATUS=0
    
    if ! check_process; then
        STATUS=1
    fi
    
    if ! check_errors; then
        STATUS=1
    fi
    
    if ! check_resources; then
        STATUS=1
    fi
    
    if [ $STATUS -eq 0 ]; then
        echo "✅ Все проверки пройдены"
    else
        echo "❌ Обнаружены проблемы"
        # Здесь можно добавить отправку уведомлений
    fi
    
    return $STATUS
}

main "$@"
"""
    
    try:
        with open("monitor.sh", 'w') as f:
            f.write(script_content)
        
        # Делаем скрипт исполняемым
        os.chmod("monitor.sh", 0o755)
        print("✅ Скрипт мониторинга создан: monitor.sh")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания скрипта мониторинга: {e}")
        return False

def create_backup_script():
    """Создание скрипта резервного копирования"""
    script_content = """#!/bin/bash
# Скрипт резервного копирования торгового бота

BACKUP_DIR="/backup/trading-bot"
DATE=$(date +%Y%m%d_%H%M%S)
SOURCE_DIR="$(pwd)"

# Создание директории для бэкапа
mkdir -p "$BACKUP_DIR"

# Создание архива
tar -czf "$BACKUP_DIR/trading-bot-backup-$DATE.tar.gz" \\
    --exclude="__pycache__" \\
    --exclude="*.pyc" \\
    --exclude=".git" \\
    --exclude="venv" \\
    --exclude="data/trading_history.json" \\
    "$SOURCE_DIR"

# Удаление старых бэкапов (старше 7 дней)
find "$BACKUP_DIR" -name "trading-bot-backup-*.tar.gz" -mtime +7 -delete

echo "✅ Резервная копия создана: $BACKUP_DIR/trading-bot-backup-$DATE.tar.gz"
"""
    
    try:
        with open("backup.sh", 'w') as f:
            f.write(script_content)
        
        os.chmod("backup.sh", 0o755)
        print("✅ Скрипт резервного копирования создан: backup.sh")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания скрипта резервного копирования: {e}")
        return False

def create_deployment_guide():
    """Создание руководства по развертыванию"""
    guide_content = """# Руководство по развертыванию торгового бота

## 🚀 Быстрый старт

### 1. Локальное развертывание
```bash
# Установка
python setup.py

# Настройка API ключей в .env
nano .env

# Запуск
python main.py
```

### 2. Развертывание с Docker
```bash
# Сборка образа
docker build -t trading-bot .

# Запуск контейнера
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

### 3. Развертывание на сервере

#### Ubuntu/Debian
```bash
# Установка зависимостей
sudo apt update
sudo apt install python3-pip python3-venv nginx

# Создание пользователя
sudo useradd -m -s /bin/bash trader
sudo usermod -aG sudo trader

# Клонирование и настройка
sudo -u trader git clone <repository-url> /home/trader/trading-bot
cd /home/trader/trading-bot
sudo -u trader python3 setup.py

# Создание systemd сервиса
sudo python3 deploy.py --systemd

# Запуск сервиса
sudo systemctl enable trading-bot
sudo systemctl start trading-bot

# Проверка статуса
sudo systemctl status trading-bot
```

#### CentOS/RHEL
```bash
# Установка зависимостей
sudo yum install python3-pip nginx

# Остальные шаги аналогичны Ubuntu
```

## 📊 Мониторинг

### 1. Логи
```bash
# Просмотр логов в реальном времени
tail -f trading_bot.log

# Поиск ошибок
grep "ERROR" trading_bot.log

# Анализ производительности
python -c "from monitoring import TradingMonitor; print(TradingMonitor().generate_performance_report())"
```

### 2. Системные метрики
```bash
# Использование ресурсов
htop

# Сетевые соединения
netstat -tulpn | grep python

# Дисковое пространство
df -h
```

### 3. Автоматический мониторинг
```bash
# Добавление в crontab
crontab -e

# Проверка каждые 5 минут
*/5 * * * * /path/to/trading-bot/monitor.sh
```

## 🔧 Обслуживание

### 1. Обновление
```bash
# Остановка сервиса
sudo systemctl stop trading-bot

# Обновление кода
git pull origin main

# Установка новых зависимостей
pip install -r requirements.txt

# Запуск сервиса
sudo systemctl start trading-bot
```

### 2. Резервное копирование
```bash
# Создание бэкапа
./backup.sh

# Восстановление из бэкапа
tar -xzf /backup/trading-bot/trading-bot-backup-YYYYMMDD_HHMMSS.tar.gz
```

### 3. Масштабирование
```bash
# Горизонтальное масштабирование с Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.yml trading-bot

# Вертикальное масштабирование
# Увеличьте ресурсы сервера и перезапустите сервис
```

## ⚠️ Безопасность

### 1. Firewall
```bash
# Настройка UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. SSL/TLS
```bash
# Установка Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. API ключи
- Храните API ключи в переменных окружения
- Используйте разные ключи для тестирования и продакшена
- Регулярно ротируйте ключи

## 🐛 Устранение неполадок

### 1. Бот не запускается
```bash
# Проверка логов
journalctl -u trading-bot -f

# Проверка конфигурации
python -c "from config import settings; print(settings.bybit_api_key)"
```

### 2. Ошибки API
- Проверьте правильность API ключей
- Убедитесь в наличии интернет-соединения
- Проверьте лимиты API

### 3. Проблемы с Ollama
```bash
# Проверка статуса
ollama list

# Перезапуск
sudo systemctl restart ollama
```

## 📈 Оптимизация

### 1. Производительность
- Увеличьте интервал между циклами при высокой нагрузке
- Используйте SSD для логов и данных
- Настройте мониторинг ресурсов

### 2. Надежность
- Настройте автоматические перезапуски
- Используйте health checks
- Реализуйте graceful shutdown

### 3. Масштабируемость
- Разделите компоненты на отдельные сервисы
- Используйте очереди сообщений
- Настройте балансировку нагрузки
"""
    
    try:
        with open("DEPLOYMENT.md", 'w') as f:
            f.write(guide_content)
        print("✅ Руководство по развертыванию создано: DEPLOYMENT.md")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания руководства: {e}")
        return False

def main():
    """Главная функция развертывания"""
    print("🚀 Создание файлов для развертывания торгового бота")
    print("=" * 60)
    
    success = True
    
    # Создаем файлы для развертывания
    if not create_dockerfile():
        success = False
    
    if not create_docker_compose():
        success = False
    
    if not create_nginx_config():
        success = False
    
    if not create_monitoring_script():
        success = False
    
    if not create_backup_script():
        success = False
    
    if not create_deployment_guide():
        success = False
    
    # Создаем systemd сервис (только на Linux)
    if sys.platform == "linux":
        if not create_systemd_service():
            print("⚠️  Systemd сервис не создан, но это не критично")
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Файлы для развертывания созданы успешно!")
        print("\n📋 Созданные файлы:")
        print("- Dockerfile")
        print("- docker-compose.yml")
        print("- nginx.conf")
        print("- monitor.sh")
        print("- backup.sh")
        print("- DEPLOYMENT.md")
        if sys.platform == "linux":
            print("- /etc/systemd/system/trading-bot.service")
        
        print("\n📖 Следующие шаги:")
        print("1. Изучите DEPLOYMENT.md для подробных инструкций")
        print("2. Настройте API ключи в .env")
        print("3. Выберите способ развертывания (локально/Docker/сервер)")
        print("4. Запустите бота и настройте мониторинг")
    else:
        print("⚠️  Некоторые файлы не были созданы")
        print("Проверьте права доступа и попробуйте снова")

if __name__ == "__main__":
    main()