"""
Скрипт установки и настройки ИИ агента торговли биткойном
"""
import os
import sys
import subprocess
import asyncio
from pathlib import Path
from loguru import logger

class SetupManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        
    def check_python_version(self):
        """Проверка версии Python"""
        if sys.version_info < (3, 8):
            logger.error("Требуется Python 3.8 или выше")
            return False
        logger.info(f"Python версия: {sys.version}")
        return True
    
    def create_virtual_environment(self):
        """Создание виртуального окружения"""
        try:
            if self.venv_path.exists():
                logger.info("Виртуальное окружение уже существует")
                return True
            
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)], check=True)
            logger.info("Виртуальное окружение создано")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка создания виртуального окружения: {e}")
            return False
    
    def install_dependencies(self):
        """Установка зависимостей"""
        try:
            pip_path = self.venv_path / "bin" / "pip" if os.name != "nt" else self.venv_path / "Scripts" / "pip.exe"
            
            subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
            logger.info("Зависимости установлены")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка установки зависимостей: {e}")
            return False
    
    def create_directories(self):
        """Создание необходимых директорий"""
        directories = ["logs", "exports", "backups", "data"]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
            logger.info(f"Директория создана: {directory}")
    
    def create_env_file(self):
        """Создание файла .env"""
        env_path = self.project_root / ".env"
        env_example_path = self.project_root / ".env.example"
        
        if env_path.exists():
            logger.info("Файл .env уже существует")
            return True
        
        if env_example_path.exists():
            import shutil
            shutil.copy2(env_example_path, env_path)
            logger.info("Файл .env создан из примера")
            logger.warning("ВАЖНО: Отредактируйте файл .env с вашими API ключами!")
            return True
        else:
            logger.error("Файл .env.example не найден")
            return False
    
    def check_ollama_installation(self):
        """Проверка установки Ollama"""
        try:
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Ollama установлен: {result.stdout.strip()}")
                return True
            else:
                logger.warning("Ollama не найден. Установите Ollama: https://ollama.ai/")
                return False
        except FileNotFoundError:
            logger.warning("Ollama не найден. Установите Ollama: https://ollama.ai/")
            return False
    
    async def setup_ollama_model(self):
        """Настройка модели Ollama"""
        try:
            # Проверка доступных моделей
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if "gemma2:9b" in result.stdout:
                logger.info("Модель gemma2:9b уже установлена")
                return True
            
            logger.info("Установка модели gemma2:9b...")
            subprocess.run(["ollama", "pull", "gemma2:9b"], check=True)
            logger.info("Модель gemma2:9b установлена")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка установки модели: {e}")
            return False
    
    def test_configuration(self):
        """Тестирование конфигурации"""
        try:
            from config import settings
            
            # Проверка обязательных параметров
            if not settings.bybit_api_key:
                logger.warning("BYBIT_API_KEY не установлен")
            if not settings.bybit_secret_key:
                logger.warning("BYBIT_SECRET_KEY не установлен")
            
            logger.info("Конфигурация загружена успешно")
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            return False
    
    def create_startup_script(self):
        """Создание скрипта запуска"""
        startup_script = """#!/bin/bash
# Скрипт запуска ИИ агента торговли биткойном

# Активация виртуального окружения
source venv/bin/activate

# Запуск агента
python main.py
"""
        
        script_path = self.project_root / "start_bot.sh"
        with open(script_path, "w") as f:
            f.write(startup_script)
        
        # Делаем скрипт исполняемым
        os.chmod(script_path, 0o755)
        logger.info("Скрипт запуска создан: start_bot.sh")
    
    def create_stop_script(self):
        """Создание скрипта остановки"""
        stop_script = """#!/bin/bash
# Скрипт остановки ИИ агента торговли биткойном

# Поиск и остановка процесса
pkill -f "python main.py"

echo "Агент остановлен"
"""
        
        script_path = self.project_root / "stop_bot.sh"
        with open(script_path, "w") as f:
            f.write(stop_script)
        
        os.chmod(script_path, 0o755)
        logger.info("Скрипт остановки создан: stop_bot.sh")
    
    async def run_setup(self):
        """Запуск полной настройки"""
        logger.info("Начинаем настройку ИИ агента торговли биткойном...")
        
        # Проверка Python
        if not self.check_python_version():
            return False
        
        # Создание виртуального окружения
        if not self.create_virtual_environment():
            return False
        
        # Установка зависимостей
        if not self.install_dependencies():
            return False
        
        # Создание директорий
        self.create_directories()
        
        # Создание .env файла
        if not self.create_env_file():
            return False
        
        # Проверка Ollama
        ollama_installed = self.check_ollama_installation()
        
        if ollama_installed:
            # Настройка модели
            await self.setup_ollama_model()
        
        # Тестирование конфигурации
        self.test_configuration()
        
        # Создание скриптов
        self.create_startup_script()
        self.create_stop_script()
        
        logger.info("Настройка завершена!")
        logger.info("Следующие шаги:")
        logger.info("1. Отредактируйте файл .env с вашими API ключами")
        logger.info("2. Запустите агента: ./start_bot.sh")
        logger.info("3. Для остановки: ./stop_bot.sh")
        
        return True

async def main():
    """Главная функция настройки"""
    setup = SetupManager()
    success = await setup.run_setup()
    
    if success:
        logger.info("✅ Настройка завершена успешно!")
    else:
        logger.error("❌ Ошибка настройки")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())