"""
Скрипт установки и настройки торгового бота
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"Текущая версия: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} - OK")
    return True

def install_requirements():
    """Установка зависимостей"""
    try:
        print("📦 Установка зависимостей...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Зависимости установлены")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False

def check_ollama():
    """Проверка установки Ollama"""
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama установлен: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama не найден")
            return False
    except FileNotFoundError:
        print("❌ Ollama не установлен")
        return False

def install_ollama():
    """Установка Ollama"""
    try:
        print("📥 Установка Ollama...")
        if platform.system() == "Linux":
            subprocess.run(["curl", "-fsSL", "https://ollama.ai/install.sh"], shell=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["curl", "-fsSL", "https://ollama.ai/install.sh"], shell=True)
        elif platform.system() == "Windows":
            print("Пожалуйста, установите Ollama вручную с https://ollama.ai")
            return False
        else:
            print("Неподдерживаемая операционная система")
            return False
        
        print("✅ Ollama установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки Ollama: {e}")
        return False

def start_ollama_service():
    """Запуск сервиса Ollama"""
    try:
        print("🚀 Запуск сервиса Ollama...")
        # Запускаем в фоне
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Сервис Ollama запущен")
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска Ollama: {e}")
        return False

def download_gemma_model():
    """Загрузка модели Gemma2"""
    try:
        print("📥 Загрузка модели Gemma2...")
        subprocess.check_call(["ollama", "pull", "gemma2:9b"])
        print("✅ Модель Gemma2 загружена")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        return False

def create_env_file():
    """Создание файла .env"""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ Файл .env уже существует")
        return True
    
    try:
        print("📝 Создание файла .env...")
        with open(".env", "w", encoding="utf-8") as f:
            f.write("""# Bybit API Configuration
BYBIT_API_KEY=your_bybit_api_key_here
BYBIT_SECRET_KEY=your_bybit_secret_key_here
BYBIT_TESTNET=true

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma2:9b

# Alpha Vantage API (для исторических данных)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Trading Configuration
TRADING_SYMBOL=BTCUSDT
MAX_POSITION_SIZE=0.1
RISK_PERCENTAGE=2.0
STOP_LOSS_PERCENTAGE=5.0
TAKE_PROFIT_PERCENTAGE=10.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=trading_bot.log
""")
        print("✅ Файл .env создан")
        print("⚠️  Не забудьте настроить API ключи в файле .env")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания .env файла: {e}")
        return False

def create_directories():
    """Создание необходимых директорий"""
    try:
        print("📁 Создание директорий...")
        directories = ["logs", "data", "reports"]
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
        print("✅ Директории созданы")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания директорий: {e}")
        return False

def test_installation():
    """Тестирование установки"""
    try:
        print("🧪 Тестирование установки...")
        
        # Тестируем импорты
        import langgraph
        import langchain
        import pybit
        import pandas
        import numpy
        import ta
        from duckduckgo_search import DDGS
        
        print("✅ Все модули импортированы успешно")
        
        # Тестируем конфигурацию
        from config import settings
        print("✅ Конфигурация загружена")
        
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def main():
    """Главная функция установки"""
    print("🤖 Установка торгового бота с ИИ агентом")
    print("=" * 50)
    
    # Проверяем Python
    if not check_python_version():
        sys.exit(1)
    
    # Устанавливаем зависимости
    if not install_requirements():
        sys.exit(1)
    
    # Создаем директории
    if not create_directories():
        sys.exit(1)
    
    # Создаем .env файл
    if not create_env_file():
        sys.exit(1)
    
    # Проверяем Ollama
    if not check_ollama():
        print("📥 Ollama не найден. Устанавливаем...")
        if not install_ollama():
            print("❌ Не удалось установить Ollama")
            print("Пожалуйста, установите Ollama вручную с https://ollama.ai")
            sys.exit(1)
    
    # Запускаем Ollama
    if not start_ollama_service():
        print("⚠️  Не удалось запустить Ollama автоматически")
        print("Пожалуйста, запустите 'ollama serve' вручную")
    
    # Загружаем модель
    if not download_gemma_model():
        print("⚠️  Не удалось загрузить модель Gemma2")
        print("Пожалуйста, выполните 'ollama pull gemma2:9b' вручную")
    
    # Тестируем установку
    if not test_installation():
        print("❌ Тестирование не прошло")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Установка завершена успешно!")
    print("\n📋 Следующие шаги:")
    print("1. Настройте API ключи в файле .env")
    print("2. Убедитесь, что Ollama запущен: ollama serve")
    print("3. Запустите бота: python main.py")
    print("\n⚠️  ВАЖНО: Начните с testnet режима!")
    print("=" * 50)

if __name__ == "__main__":
    main()