#!/bin/bash

# Скрипт для запуска торгового робота
# Использование: ./run_robot.sh [single|continuous] [interval]

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_message() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    print_warning "Виртуальное окружение не найдено. Создаем..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        print_error "Ошибка создания виртуального окружения"
        exit 1
    fi
fi

# Активация виртуального окружения
print_message "Активируем виртуальное окружение..."
source venv/bin/activate

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    print_warning "Файл .env не найден. Копируем из .env.example..."
    cp .env.example .env
    print_warning "Пожалуйста, отредактируйте файл .env и добавьте ваши API ключи"
    exit 1
fi

# Проверка установки зависимостей
print_message "Проверяем зависимости..."
pip install -r requirements.txt > /dev/null 2>&1
if [ $? -ne 0 ]; then
    print_error "Ошибка установки зависимостей"
    exit 1
fi

# Проверка Ollama
print_message "Проверяем Ollama..."
if ! command -v ollama &> /dev/null; then
    print_warning "Ollama не установлен. Запускаем установку..."
    python setup_ollama.py
    if [ $? -ne 0 ]; then
        print_error "Ошибка установки Ollama"
        exit 1
    fi
fi

# Проверка запуска Ollama сервиса
print_message "Проверяем сервис Ollama..."
if ! pgrep -f "ollama serve" > /dev/null; then
    print_warning "Сервис Ollama не запущен. Запускаем..."
    ollama serve &
    sleep 5
fi

# Создание директории для логов
mkdir -p logs

# Определение параметров запуска
MODE=${1:-"single"}
INTERVAL=${2:-30}

print_message "Запускаем торговый робот в режиме: $MODE"
if [ "$MODE" = "continuous" ]; then
    print_message "Интервал между циклами: $INTERVAL минут"
fi

# Запуск робота
if [ "$MODE" = "single" ]; then
    python main.py --mode single
elif [ "$MODE" = "continuous" ]; then
    python main.py --mode continuous --interval $INTERVAL
else
    print_error "Неверный режим. Используйте 'single' или 'continuous'"
    exit 1
fi

print_message "Торговый робот завершил работу"