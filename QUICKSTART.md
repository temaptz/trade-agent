# 🚀 Быстрый старт торгового бота

## Установка за 5 минут

### 1. Автоматическая установка
```bash
# Клонируйте репозиторий
git clone <repository-url>
cd trading-bot

# Запустите автоматическую установку
python setup.py
```

### 2. Настройка API ключей
```bash
# Отредактируйте файл .env
nano .env

# Заполните ваши API ключи:
BYBIT_API_KEY=your_api_key_here
BYBIT_SECRET_KEY=your_secret_key_here
BYBIT_TESTNET=true  # Начните с testnet!
```

### 3. Запуск
```bash
# Интерактивный режим (рекомендуется)
python main.py

# Или один цикл
python main.py single

# Или непрерывная торговля
python main.py continuous 30
```

## 🔧 Что нужно настроить

### Обязательно:
- ✅ API ключи Bybit (получите на bybit.com)
- ✅ Ollama с моделью Gemma2 (устанавливается автоматически)

### Опционально:
- 🔹 Alpha Vantage API ключ (для исторических данных)
- 🔹 Настройка торговых параметров в .env

## ⚠️ Важные предупреждения

1. **НАЧНИТЕ С TESTNET** - установите `BYBIT_TESTNET=true`
2. **НЕ ИНВЕСТИРУЙТЕ БОЛЬШЕ, ЧЕМ МОЖЕТЕ ПОТЕРЯТЬ**
3. **МОНИТОРЬТЕ РАБОТУ БОТА** - проверяйте логи и результаты
4. **ТЕСТИРУЙТЕ НАСТРОЙКИ** - используйте небольшие суммы

## 📊 Мониторинг

```bash
# Просмотр логов
tail -f trading_bot.log

# Проверка статуса
python -c "from monitoring import TradingMonitor; print(TradingMonitor().get_system_status())"

# Отчет о производительности
python -c "from monitoring import TradingMonitor; print(TradingMonitor().generate_performance_report())"
```

## 🆘 Если что-то не работает

### Ollama не запускается:
```bash
ollama serve
ollama pull gemma2:9b
```

### Ошибки API:
- Проверьте правильность ключей в .env
- Убедитесь, что используете testnet для начала

### Низкая производительность:
- Увеличьте интервал между циклами
- Проверьте интернет-соединение

## 📚 Дополнительно

- Полная документация: `README.md`
- Руководство по развертыванию: `DEPLOYMENT.md`
- Примеры использования: `python examples.py`
- Тесты: `python test_bot.py`

---

**Удачной торговли! 🎯**