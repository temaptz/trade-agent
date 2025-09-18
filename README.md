# Bitcoin Trading Agent

ИИ агент для автоматической торговли биткойном на Bybit с использованием LangGraph, LangChain, Ollama и Gemma3.

## Возможности

- **Анализ рынка**: Технические индикаторы (RSI, MACD, Bollinger Bands, Moving Averages)
- **Анализ новостей**: Поиск и анализ новостей через DuckDuckGo
- **ИИ анализ**: Использование Ollama с моделью Gemma3 для принятия решений
- **Торговые стратегии**: Множественные стратегии на основе технического анализа и настроений
- **Управление рисками**: Автоматическое управление позициями и стоп-лоссами
- **LangGraph агент**: Интеллектуальный агент с инструментами для торговли

## Технологии

- **Python 3.8+**
- **LangChain & LangGraph**: Фреймворк для ИИ агентов
- **Ollama**: Локальная LLM с Gemma3
- **CCXT**: Торговые API для Bybit
- **DuckDuckGo Search**: Поиск новостей
- **TA-Lib**: Технические индикаторы
- **Pandas & NumPy**: Обработка данных

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd bitcoin-trading-agent
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Установка Ollama

```bash
# Установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Запуск Ollama
ollama serve

# Установка модели Gemma3
ollama pull gemma2:9b
```

### 4. Настройка конфигурации

```bash
# Копирование файла конфигурации
cp .env.example .env

# Редактирование конфигурации
nano .env
```

Заполните следующие параметры в `.env`:

```env
# Bybit API credentials
BYBIT_API_KEY=your_bybit_api_key_here
BYBIT_SECRET_KEY=your_bybit_secret_key_here
BYBIT_TESTNET=true

# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2:9b

# Trading configuration
TRADING_SYMBOL=BTCUSDT
TRADING_INTERVAL=1h
MAX_POSITION_SIZE=0.1
RISK_PERCENTAGE=2.0
```

## Использование

### Запуск агента

```bash
# Одиночный анализ
python main.py single

# Получение сводки рынка
python main.py summary

# Непрерывная торговля
python main.py continuous
```

### Программное использование

```python
import asyncio
from trading_agent import BitcoinTradingAgent

async def main():
    agent = BitcoinTradingAgent()
    
    # Запуск анализа
    result = await agent.run_analysis_cycle()
    print(result)

asyncio.run(main())
```

## Архитектура

### Компоненты системы

1. **BybitClient**: Интеграция с Bybit API для торговли
2. **MarketAnalyzer**: Анализ рыночных данных и технических индикаторов
3. **NewsAnalyzer**: Поиск и анализ новостей через DuckDuckGo
4. **OllamaClient**: Интеграция с Ollama для ИИ анализа
5. **TradingAgent**: LangGraph агент с инструментами
6. **TradingStrategies**: Торговые стратегии и управление рисками

### LangGraph Workflow

```
analyze_market → analyze_news → llm_analysis → make_decision → execute_trade
```

### Торговые стратегии

1. **Технический анализ**:
   - RSI стратегия (перекупленность/перепроданность)
   - MACD стратегия (пересечения)
   - Bollinger Bands стратегия
   - Moving Average стратегия

2. **Анализ настроений**:
   - Анализ новостей
   - Рыночные настроения
   - Комбинированный анализ

3. **Управление рисками**:
   - Автоматический расчет размера позиции
   - Стоп-лоссы и тейк-профиты
   - Ограничения по риску

## Конфигурация

### Параметры торговли

- `TRADING_SYMBOL`: Торговая пара (по умолчанию BTCUSDT)
- `TRADING_INTERVAL`: Таймфрейм для анализа (1h, 4h, 1d)
- `MAX_POSITION_SIZE`: Максимальный размер позиции (0.1 = 10%)
- `RISK_PERCENTAGE`: Процент риска на сделку (2.0%)

### Параметры анализа

- `NEWS_UPDATE_INTERVAL`: Интервал обновления новостей (300 сек)
- `MARKET_ANALYSIS_INTERVAL`: Интервал анализа рынка (60 сек)

## Безопасность

⚠️ **ВАЖНО**: Этот агент предназначен для образовательных целей. Торговля криптовалютами связана с высокими рисками.

### Рекомендации по безопасности

1. **Используйте тестовую сеть**: Начните с `BYBIT_TESTNET=true`
2. **Ограничьте размер позиций**: Установите `MAX_POSITION_SIZE=0.01` (1%)
3. **Мониторинг**: Регулярно проверяйте логи и результаты
4. **Резервные копии**: Сохраняйте конфигурацию и логи

## Мониторинг

### Логи

Логи сохраняются в файл `trading_bot.log` с ротацией каждый день.

```bash
# Просмотр логов
tail -f trading_bot.log

# Поиск ошибок
grep "ERROR" trading_bot.log
```

### Метрики

Агент отслеживает:
- Количество выполненных анализов
- Успешность торговых решений
- Время выполнения операций
- Ошибки и исключения

## Тестирование

```bash
# Запуск тестов
pytest test_trading_agent.py -v

# Запуск с покрытием
pytest test_trading_agent.py --cov=. --cov-report=html
```

## Разработка

### Структура проекта

```
bitcoin-trading-agent/
├── main.py                 # Главный файл
├── config.py              # Конфигурация
├── bybit_client.py        # Bybit API клиент
├── market_analyzer.py     # Анализ рынка
├── news_analyzer.py        # Анализ новостей
├── ollama_client.py       # Ollama клиент
├── trading_agent.py       # LangGraph агент
├── trading_strategies.py  # Торговые стратегии
├── test_trading_agent.py  # Тесты
├── requirements.txt        # Зависимости
├── .env.example          # Пример конфигурации
└── README.md             # Документация
```

### Добавление новых стратегий

```python
class CustomStrategy:
    def analyze_signals(self, market_data, indicators):
        # Ваша логика анализа
        return signals
```

### Добавление новых инструментов

```python
def custom_tool(self, parameter):
    """Описание инструмента"""
    # Логика инструмента
    return result
```

## Устранение неполадок

### Частые проблемы

1. **Ошибка подключения к Ollama**:
   ```bash
   # Проверьте, что Ollama запущен
   curl http://localhost:11434/api/tags
   ```

2. **Ошибка Bybit API**:
   - Проверьте API ключи
   - Убедитесь, что тестовая сеть включена

3. **Ошибки зависимостей**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

## Лицензия

MIT License

## Поддержка

Для вопросов и поддержки создайте issue в репозитории.

---

**Отказ от ответственности**: Этот проект предназначен только для образовательных целей. Автор не несет ответственности за любые финансовые потери, связанные с использованием данного программного обеспечения.