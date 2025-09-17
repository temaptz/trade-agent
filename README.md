# Bitcoin Trading Agent

Продвинутый AI агент для торговли Bitcoin на Bybit с использованием LangGraph, LangChain и Ollama.

## 🚀 Возможности

- **Комплексный анализ рынка**: Технические индикаторы, анализ настроений, новости
- **AI-принятие решений**: Использует локальную LLM через Ollama для анализа
- **Управление рисками**: Продвинутая система управления рисками и позициями
- **Мониторинг в реальном времени**: Полное логирование и отслеживание производительности
- **Модульная архитектура**: Легко расширяемая система на LangGraph

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Market Data   │    │   News Analysis │    │  Sentiment AI   │
│   Analyzer      │    │   (DuckDuckGo)  │    │   (Ollama)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     LangGraph Workflow    │
                    │   (Trading Decisions)     │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     Risk Manager          │
                    │   (Position Management)   │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     Bybit API            │
                    │   (Trade Execution)      │
                    └───────────────────────────┘
```

## 📋 Требования

- Python 3.8+
- Ollama с моделью llama3.1:8b
- Bybit API ключи
- 4GB+ RAM для LLM

## 🛠️ Установка

1. **Клонируйте репозиторий**
```bash
git clone <repository-url>
cd bitcoin-trading-agent
```

2. **Установите зависимости**
```bash
pip install -r requirements.txt
```

3. **Настройте Ollama**
```bash
# Установите Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Запустите Ollama
ollama serve

# Загрузите модель
ollama pull llama3.1:8b
```

4. **Настройте конфигурацию**
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими API ключами
```

5. **Создайте директории для логов**
```bash
mkdir -p logs
```

## ⚙️ Конфигурация

### Переменные окружения (.env)

```env
# Bybit API Configuration
BYBIT_API_KEY=your_api_key_here
BYBIT_SECRET_KEY=your_secret_key_here
BYBIT_TESTNET=true

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Trading Configuration
TRADING_PAIR=BTCUSDT
MAX_POSITION_SIZE=0.1
RISK_PERCENTAGE=2.0
STOP_LOSS_PERCENTAGE=3.0
TAKE_PROFIT_PERCENTAGE=6.0

# News Analysis
NEWS_UPDATE_INTERVAL=300
SENTIMENT_THRESHOLD=0.6

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/trading_agent.log
```

## 🚀 Запуск

### Основной режим
```bash
python main.py
```

### Тестовый режим (с testnet)
```bash
# Убедитесь, что BYBIT_TESTNET=true в .env
python main.py
```

## 📊 Мониторинг

### Логи
- `logs/trading_agent.log` - Основные логи
- `logs/performance.log` - Метрики производительности
- `logs/errors.log` - Ошибки системы

### Метрики
- `logs/performance.json` - JSON данные о производительности
- `logs/health.json` - Статус здоровья системы

### Отчеты
```python
from monitoring import TradingMonitor

monitor = TradingMonitor()
report = monitor.generate_report()
print(report)
```

## 🔧 Компоненты системы

### 1. Market Analyzer (`market_analyzer.py`)
- Технические индикаторы (RSI, MACD, Bollinger Bands, SMA, EMA)
- Анализ структуры рынка
- Оценка волатильности и трендов

### 2. News Analyzer (`news_analyzer.py`)
- Поиск новостей через DuckDuckGo
- Анализ контента статей
- Оценка релевантности и настроений

### 3. Sentiment Analyzer (`sentiment_analyzer.py`)
- AI-анализ настроений через Ollama
- Комплексная оценка рыночных факторов
- Генерация торговых решений

### 4. Trading Workflow (`trading_workflow.py`)
- LangGraph workflow для принятия решений
- Последовательный анализ всех факторов
- Интеграция всех компонентов

### 5. Risk Manager (`risk_manager.py`)
- Управление рисками и позициями
- Расчет максимальных размеров позиций
- Stop-loss и take-profit уровни

### 6. Monitoring (`monitoring.py`)
- Логирование всех операций
- Отслеживание производительности
- Мониторинг здоровья системы

## 📈 Стратегия торговли

### Анализ факторов
1. **Технический анализ** (40% веса)
   - RSI, MACD, Bollinger Bands
   - Moving Averages, Volume analysis
   - Support/Resistance levels

2. **Анализ настроений** (30% веса)
   - AI-анализ новостей через Ollama
   - Оценка рыночных настроений
   - Confidence scoring

3. **Новостной анализ** (30% веса)
   - Поиск релевантных новостей
   - Анализ контента
   - Влияние на цену

### Управление рисками
- Максимальный размер позиции: 10% от баланса
- Stop-loss: 3% (с учетом волатильности)
- Take-profit: 6% (с учетом тренда)
- Максимальная дневная потеря: 2%
- Максимум сделок в день: 10

## 🛡️ Безопасность

- Все API ключи в переменных окружения
- Testnet режим по умолчанию
- Комплексная система управления рисками
- Полное логирование всех операций

## 📝 Примеры использования

### Запуск анализа
```python
from trading_workflow import TradingWorkflow

workflow = TradingWorkflow()
result = await workflow.run_analysis()
print(f"Signal: {result.trading_decision.signal}")
```

### Получение статуса
```python
from main import BitcoinTradingAgent

agent = BitcoinTradingAgent()
status = agent.get_status()
print(status)
```

### Экспорт данных
```python
from monitoring import TradingMonitor

monitor = TradingMonitor()
export_file = monitor.export_data("my_export.json")
```

## 🔍 Отладка

### Проверка компонентов
```python
from main import BitcoinTradingAgent

agent = BitcoinTradingAgent()
await agent._test_components()
```

### Логи в реальном времени
```bash
tail -f logs/trading_agent.log
```

### Проверка Ollama
```bash
ollama list
ollama run llama3.1:8b "Hello, how are you?"
```

## ⚠️ Предупреждения

- **Это экспериментальная система** - используйте только на testnet
- **Управление рисками критично** - настройте лимиты под ваши нужды
- **Мониторинг обязателен** - следите за производительностью
- **API ключи** - храните в безопасности

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE

## 📞 Поддержка

- Создайте Issue для багов
- Используйте Discussions для вопросов
- Проверьте Wiki для документации

---

**⚠️ Дисклеймер**: Этот проект предназначен только для образовательных целей. Торговля криптовалютами связана с высокими рисками. Используйте на свой страх и риск.