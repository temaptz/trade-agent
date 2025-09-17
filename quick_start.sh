#!/bin/bash

# Быстрый запуск торгового робота
# Автор: AI Assistant
# Версия: 1.0

echo "🤖 Торговый робот с ИИ-агентом - Быстрый запуск"
echo "================================================"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода цветного текста
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Проверка Python
print_info "Проверка Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        print_status "Python $PYTHON_VERSION найден"
    else
        print_error "Требуется Python 3.8 или выше"
        exit 1
    fi
else
    print_error "Python3 не найден"
    exit 1
fi

# Проверка pip
print_info "Проверка pip..."
if command -v pip3 &> /dev/null; then
    print_status "pip3 найден"
else
    print_error "pip3 не найден"
    exit 1
fi

# Установка зависимостей
print_info "Установка зависимостей..."
if pip3 install -r requirements.txt; then
    print_status "Зависимости установлены"
else
    print_error "Ошибка установки зависимостей"
    exit 1
fi

# Проверка Ollama
print_info "Проверка Ollama..."
if command -v ollama &> /dev/null; then
    print_status "Ollama найден"
    
    # Проверка, запущен ли Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_status "Ollama запущен"
        
        # Проверка модели Gemma
        if ollama list | grep -q "gemma2:9b"; then
            print_status "Модель Gemma2:9b найдена"
        else
            print_warning "Модель Gemma2:9b не найдена, загружаем..."
            if ollama pull gemma2:9b; then
                print_status "Модель Gemma2:9b загружена"
            else
                print_error "Ошибка загрузки модели"
                exit 1
            fi
        fi
    else
        print_warning "Ollama не запущен, запускаем..."
        nohup ollama serve > /dev/null 2>&1 &
        sleep 5
        
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            print_status "Ollama запущен"
        else
            print_error "Не удалось запустить Ollama"
            exit 1
        fi
    fi
else
    print_error "Ollama не найден. Установите Ollama: https://ollama.ai/download"
    exit 1
fi

# Проверка файла конфигурации
print_info "Проверка конфигурации..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_warning "Файл .env не найден, создаем из .env.example"
        cp .env.example .env
        print_warning "ВАЖНО: Отредактируйте файл .env и добавьте ваши API ключи Bybit"
    else
        print_error "Файл .env.example не найден"
        exit 1
    fi
else
    print_status "Файл .env найден"
fi

# Запуск тестов
print_info "Запуск тестов системы..."
if python3 test_system.py; then
    print_status "Тесты пройдены"
else
    print_warning "Некоторые тесты провалены, но продолжаем..."
fi

# Меню запуска
echo ""
echo "🚀 Готово к запуску!"
echo "==================="
echo "Выберите действие:"
echo "1. Запустить робота"
echo "2. Показать статус системы"
echo "3. Запустить примеры"
echo "4. Сгенерировать отчет"
echo "5. Выход"

read -p "Введите номер (1-5): " choice

case $choice in
    1)
        print_info "Запуск торгового робота..."
        python3 main.py
        ;;
    2)
        print_info "Статус системы..."
        python3 monitor.py --status
        ;;
    3)
        print_info "Запуск примеров..."
        python3 examples.py
        ;;
    4)
        print_info "Генерация отчета..."
        python3 monitor.py --report
        ;;
    5)
        print_info "Выход"
        exit 0
        ;;
    *)
        print_error "Неверный выбор"
        exit 1
        ;;
esac

print_status "Скрипт завершен"