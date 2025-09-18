# ИИ Агент для Торговли Биткойном на Bybit

Продвинутый ИИ агент для автоматической торговли биткойном на бирже Bybit, использующий технологии Python, LangGraph, LangChain, Ollama и Gemma3.

## 🚀 Возможности

- **Автоматический анализ рынка** с использованием 20+ технических индикаторов
- **ИИ анализ** с помощью модели Gemma3 через Ollama
- **Поиск и анализ новостей** через DuckDuckGo
- **Управление рисками** с автоматическими стоп-лоссами и тейк-профитами
- **Мониторинг в реальном времени** с оповещениями
- **База данных** для хранения истории торговли
- **Экспорт данных** и генерация отчетов

## 📋 Требования

- Python 3.8+
- Ollama с моделью Gemma3
- API ключи Bybit
- Интернет соединение

## 🛠 Установка

1. **Клонирование репозитория:**
```bash
git clone <repository-url>
cd bitcoin-trading-bot
```

2. **Установка зависимостей:**
```bash
pip install -r requirements.txt
```

3. **Установка Ollama:**
```bash
# Установка Ollama (Linux/macOS)
curl -fsSL https://ollama.ai/install.sh | sh

# Запуск Ollama
ollama serve

# Установка модели Gemma3
ollama pull gemma2:9b
```

4. **Настройка конфигурации:**
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими API ключами
```

## ⚙️ Конфигурация

Создайте файл `.env` на основе `.env.example`:

```env
# Bybit API Configuration
BYBIT_API_KEY=your_api_key_here
BYBIT_SECRET_KEY=your_secret_key_here
BYBIT_TESTNET=True

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2:9b

# Trading Configuration
TRADING_PAIR=BTCUSDT
TRADE_AMOUNT=0.001
MAX_RISK_PERCENT=2.0
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=4.0

# Intervals
NEWS_UPDATE_INTERVAL=300
MARKET_ANALYSIS_INTERVAL=60
```

## 🚀 Запуск

### Основной запуск:
```bash
python main.py
```

### Запуск в фоновом режиме:
```bash
nohup python main.py > trading_bot.log 2>&1 &
```

### Остановка:
```bash
# Найти процесс
ps aux | grep python main.py

# Остановить
kill <PID>

## 🧭 Визуализация графа агента

Сгенерировать диаграмму Mermaid и PNG (если установлен mermaid-cli):

```bash
python render_graph.py --out graph
# Получите файлы: graph.mmd и (при наличии mmdc) graph.png
```
```

## 📊 Архитектура

### Основные компоненты:

1. **TradingAgent** - Главный агент на базе LangGraph
2. **BybitClient** - Клиент для работы с Bybit API
3. **MarketAnalyzer** - Анализатор рыночных данных
4. **NewsAnalyzer** - Анализатор новостей
5. **OllamaClient** - Клиент для работы с ИИ
6. **RiskManager** - Управление рисками
7. **SystemMonitor** - Мониторинг системы

### Поток данных:

```
Рыночные данные → Технический анализ → Новости → ИИ анализ → Принятие решения → Торговля
```

## 🔧 Настройка торговли

### Параметры риска:
- `MAX_RISK_PERCENT` - Максимальный риск на сделку (%)
- `STOP_LOSS_PERCENT` - Стоп-лосс (%)
- `TAKE_PROFIT_PERCENT` - Тейк-профит (%)
- `TRADE_AMOUNT` - Размер базовой позиции

### Интервалы:
- `MARKET_ANALYSIS_INTERVAL` - Интервал анализа рынка (сек)
- `NEWS_UPDATE_INTERVAL` - Интервал обновления новостей (сек)

## 📈 Мониторинг

### Логи:
- `logs/trading_YYYY-MM-DD.log` - Основные логи
- `logs/errors_YYYY-MM-DD.log` - Логи ошибок

### База данных:
- `trading_data.db` - SQLite база с историей торговли
- Таблицы: trading_events, market_data, alerts, performance

### Экспорт данных:
```python
from utils import DataExporter
await DataExporter.export_trading_data("trading_data.db")
```

## 🛡️ Безопасность

### Рекомендации:
1. **Используйте тестовую сеть** для начала (`BYBIT_TESTNET=True`)
2. **Ограничьте размер позиций** на начальном этапе
3. **Регулярно проверяйте логи** на ошибки
4. **Создавайте резервные копии** базы данных
5. **Не храните API ключи** в открытом виде

### Управление рисками:
- Автоматические стоп-лоссы
- Ограничение максимального риска
- Мониторинг просадки
- Аварийная остановка

## 📊 Анализ производительности

### Метрики:
- Общая доходность
- Процент выигрышных сделок
- Максимальная просадка
- Коэффициент Шарпа
- Волатильность

### Отчеты:
```python
from utils import DataExporter
report_path = await DataExporter.generate_report()
```

## 🔧 Разработка

### Структура проекта:
```
├── main.py                 # Главный файл
├── trading_agent.py        # Торговый агент
├── bybit_client.py         # Клиент Bybit
├── market_analyzer.py      # Анализатор рынка
├── news_analyzer.py        # Анализатор новостей
├── ollama_client.py        # Клиент Ollama
├── risk_manager.py         # Управление рисками
├── monitor.py              # Мониторинг
├── utils.py                # Утилиты
├── config.py               # Конфигурация
└── requirements.txt        # Зависимости
```

### Добавление новых индикаторов:
```python
# В market_analyzer.py
def calculate_custom_indicator(self, df):
    # Ваш код индикатора
    return indicator_values
```

### Добавление новых источников новостей:
```python
# В news_analyzer.py
async def get_custom_news(self):
    # Ваш код получения новостей
    return news_items
```

## 🐛 Устранение неполадок

### Частые проблемы:

1. **Ошибка подключения к Ollama:**
   ```bash
   # Проверить статус
   curl http://localhost:11434/api/tags
   
   # Перезапустить
   ollama serve
   ```

2. **Ошибки API Bybit:**
   - Проверить API ключи
   - Убедиться в правильности тестовой сети
   - Проверить лимиты API

3. **Проблемы с базой данных:**
   ```bash
   # Проверить файл
   ls -la trading_data.db
   
   # Пересоздать при необходимости
   rm trading_data.db
   ```

### Логи для диагностики:
```bash
# Просмотр логов в реальном времени
tail -f logs/trading_$(date +%Y-%m-%d).log

# Поиск ошибок
grep -i error logs/trading_*.log
```

## 📞 Поддержка

### Мониторинг системы:
```python
from main import BitcoinTradingBot
bot = BitcoinTradingBot()
status = await bot.get_status()
print(status)
```

### Экстренная остановка:
```python
await bot.emergency_stop()
```

## ⚠️ Отказ от ответственности

Этот бот предназначен для образовательных целей. Торговля криптовалютами связана с высокими рисками. Автор не несет ответственности за возможные убытки. Используйте на свой страх и риск.

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.

## 🤝 Вклад в проект

Приветствуются pull requests и issues. Пожалуйста, убедитесь, что:
1. Код соответствует стилю проекта
2. Добавлены тесты для новых функций
3. Обновлена документация

---

**Удачной торговли! 🚀**