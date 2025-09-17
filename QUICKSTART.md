# 🚀 Быстрый старт торгового робота

## 1. Установка (5 минут)

```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Настройте Ollama с Gemma3
python setup_ollama.py

# 3. Скопируйте и настройте конфигурацию
cp .env.example .env
# Отредактируйте .env файл с вашими API ключами
```

## 2. Получение API ключей

### Bybit API (обязательно)
1. Зарегистрируйтесь на [bybit.com](https://www.bybit.com/)
2. API Management → Create New Key
3. Скопируйте API Key и Secret Key в `.env`

### Alpha Vantage API (обязательно)
1. Зарегистрируйтесь на [alphavantage.co](https://www.alphavantage.co/support/#api-key)
2. Получите бесплатный API ключ
3. Вставьте в `.env`

## 3. Тестирование

```bash
# Проверьте настройку
python test_setup.py

# Запустите один тестовый цикл
python main.py --mode single
```

## 4. Запуск торговли

```bash
# Один цикл
python main.py --mode single

# Непрерывная торговля каждые 30 минут
python main.py --mode continuous --interval 30

# Или используйте скрипт
./run_robot.sh single
./run_robot.sh continuous 30
```

## ⚠️ Важно!

- **Начните с тестового режима** (`BYBIT_TESTNET=true` в .env)
- **Используйте небольшие суммы** для начала
- **Мониторьте логи** в папке `logs/`
- **Проверьте баланс** перед запуском

## 🆘 Проблемы?

1. **Ollama не работает**: `ollama serve`
2. **Ошибки API**: Проверьте ключи в `.env`
3. **Нет данных**: Проверьте Alpha Vantage ключ
4. **Логи**: Смотрите в папке `logs/`

## 📊 Мониторинг

Робот выводит:
- Текущую цену BTC
- Анализ тренда
- Новостной фон
- Торговые решения
- Результаты операций

Удачи в торговле! 🎯