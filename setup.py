#!/usr/bin/env python3
"""
Скрипт для быстрой установки и настройки торгового робота
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ошибка: {e.stderr}")
        return False

def check_python_version():
    """Проверяет версию Python"""
    print("🐍 Проверка версии Python...")
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def install_dependencies():
    """Устанавливает зависимости"""
    return run_command("pip install -r requirements.txt", "Установка зависимостей")

def check_ollama():
    """Проверяет наличие Ollama"""
    print("🤖 Проверка Ollama...")
    try:
        result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama установлен")
            return True
        else:
            print("❌ Ollama не найден")
            return False
    except FileNotFoundError:
        print("❌ Ollama не найден")
        return False

def install_ollama():
    """Устанавливает Ollama"""
    print("📥 Установка Ollama...")
    if sys.platform == "linux":
        return run_command("curl -fsSL https://ollama.ai/install.sh | sh", "Установка Ollama")
    elif sys.platform == "darwin":
        return run_command("brew install ollama", "Установка Ollama через Homebrew")
    else:
        print("❌ Автоматическая установка Ollama не поддерживается для вашей ОС")
        print("📖 Установите Ollama вручную: https://ollama.ai/download")
        return False

def start_ollama():
    """Запускает Ollama"""
    print("🚀 Запуск Ollama...")
    try:
        # Проверяем, запущен ли уже Ollama
        result = subprocess.run("ollama list", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama уже запущен")
            return True
        else:
            print("⚠️ Ollama не запущен. Запустите вручную: ollama serve")
            return False
    except:
        print("⚠️ Не удалось проверить статус Ollama")
        return False

def download_gemma_model():
    """Загружает модель Gemma"""
    return run_command("ollama pull gemma2:9b", "Загрузка модели Gemma2:9b")

def create_env_file():
    """Создает файл .env из примера"""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ Файл .env уже существует")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Создан файл .env из .env.example")
        print("⚠️ Не забудьте заполнить API ключи в файле .env")
        return True
    else:
        print("❌ Файл .env.example не найден")
        return False

def test_imports():
    """Тестирует импорт основных модулей"""
    print("🧪 Тестирование импортов...")
    try:
        import langchain
        import langgraph
        import ccxt
        import pandas
        import numpy
        print("✅ Все основные модули импортированы успешно")
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def main():
    """Основная функция установки"""
    print("🤖 Установка торгового робота с ИИ-агентом")
    print("=" * 50)
    
    success = True
    
    # Проверка Python
    if not check_python_version():
        success = False
    
    # Установка зависимостей
    if not install_dependencies():
        success = False
    
    # Проверка/установка Ollama
    if not check_ollama():
        if not install_ollama():
            success = False
        else:
            if not start_ollama():
                success = False
    
    # Загрузка модели
    if not download_gemma_model():
        success = False
    
    # Создание .env файла
    if not create_env_file():
        success = False
    
    # Тестирование импортов
    if not test_imports():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Установка завершена успешно!")
        print("\n📋 Следующие шаги:")
        print("1. Отредактируйте файл .env и добавьте ваши API ключи Bybit")
        print("2. Убедитесь, что Ollama запущен: ollama serve")
        print("3. Запустите робота: python main.py")
        print("\n⚠️ ВАЖНО: Начните с тестовой сети (BYBIT_TESTNET=true)")
    else:
        print("❌ Установка завершена с ошибками")
        print("📖 Проверьте сообщения выше и исправьте ошибки")
        print("📚 Дополнительная помощь в README.md")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())