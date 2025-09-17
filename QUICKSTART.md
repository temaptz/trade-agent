# 🚀 Быстрый старт AI Trading Bot

## Установка за 5 минут

### 1. Автоматическая установка
```bash
# Клонируйте репозиторий и запустите установку
./install.sh
```

### 2. Ручная установка
```bash
# Установите зависимости
pip install -r requirements.txt

# Установите Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Запустите Ollama
ollama serve

# Загрузите модель (в другом терминале)
ollama pull gemma2:9b

# Настройте конфигурацию
cp .env.example .env
nano .env  # Отредактируйте API ключи
```

### 3. Проверка установки
```bash
python check_setup.py
```

## Запуск

### Тестирование
```bash
python test_bot.py
```

### Одиночный цикл торговли
```bash
python main.py single
```

### Непрерывная торговля
```bash
python main.py continuous 30  # каждые 30 минут
```

### Планировщик
```bash
python main.py scheduled
```

## Конфигурация

Отредактируйте `.env` файл:

```env
# Bybit API (получите на bybit.com)
BYBIT_API_KEY=your_api_key_here
BYBIT_SECRET_KEY=your_secret_key_here
BYBIT_TESTNET=true

# Торговые параметры
TRADING_PAIR=BTCUSDT
MAX_POSITION_SIZE=0.1
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=3.0
RISK_PER_TRADE=0.02
```

## Мониторинг

### Просмотр логов
```bash
tail -f logs/trading_bot.log
tail -f logs/trading_decisions.log
```

### Генерация отчета
```bash
python monitor.py --report --days 7
```

## Безопасность

⚠️ **ВАЖНО:**
- Начните с тестовой сети (testnet=true)
- Используйте малые суммы
- Регулярно проверяйте логи
- Не делитесь API ключами

## Устранение неполадок

### Ollama не запускается
```bash
ollama serve
ollama list
ollama pull gemma2:9b
```

### Ошибки API
- Проверьте API ключи в .env
- Убедитесь, что включена тестовая сеть
- Проверьте права API ключа

### Ошибки зависимостей
```bash
pip install -r requirements.txt
python check_setup.py
```

## Примеры использования

```bash
# Запуск примеров
python examples.py

# Проверка здоровья системы
python utils.py
```

## Поддержка

- 📖 Полная документация: README.md
- 🧪 Тестирование: test_bot.py
- 📊 Мониторинг: monitor.py
- 🔧 Утилиты: utils.py

---

**Удачной торговли! 🎯**