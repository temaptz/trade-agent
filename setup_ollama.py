"""
Скрипт для настройки Ollama с моделью Gemma3
"""
import subprocess
import sys
import time
from loguru import logger

def run_command(command, description):
    """Выполнить команду и обработать результат"""
    try:
        logger.info(f"Выполняем: {description}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.success(f"Успешно: {description}")
            if result.stdout:
                logger.info(f"Вывод: {result.stdout}")
            return True
        else:
            logger.error(f"Ошибка: {description}")
            logger.error(f"Код ошибки: {result.returncode}")
            if result.stderr:
                logger.error(f"Ошибка: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Исключение при выполнении '{description}': {e}")
        return False

def check_ollama_installed():
    """Проверить, установлен ли Ollama"""
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Ollama уже установлен: {result.stdout.strip()}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False

def install_ollama():
    """Установить Ollama"""
    logger.info("Устанавливаем Ollama...")
    
    # Команда для установки Ollama на Linux
    install_command = """
    curl -fsSL https://ollama.ai/install.sh | sh
    """
    
    return run_command(install_command, "Установка Ollama")

def start_ollama_service():
    """Запустить сервис Ollama"""
    logger.info("Запускаем сервис Ollama...")
    
    # Запускаем Ollama в фоновом режиме
    start_command = "ollama serve &"
    return run_command(start_command, "Запуск сервиса Ollama")

def pull_gemma_model():
    """Загрузить модель Gemma3"""
    logger.info("Загружаем модель Gemma3...")
    
    # Пробуем разные варианты модели Gemma
    models_to_try = [
        "gemma2:9b",
        "gemma2:2b", 
        "gemma:7b",
        "gemma:2b"
    ]
    
    for model in models_to_try:
        logger.info(f"Пробуем загрузить модель: {model}")
        pull_command = f"ollama pull {model}"
        
        if run_command(pull_command, f"Загрузка модели {model}"):
            logger.success(f"Модель {model} успешно загружена")
            return model
        else:
            logger.warning(f"Не удалось загрузить модель {model}")
    
    logger.error("Не удалось загрузить ни одну модель Gemma")
    return None

def test_ollama_connection():
    """Протестировать подключение к Ollama"""
    logger.info("Тестируем подключение к Ollama...")
    
    test_command = "ollama list"
    if run_command(test_command, "Проверка списка моделей"):
        return True
    else:
        logger.error("Не удалось подключиться к Ollama")
        return False

def main():
    """Основная функция настройки"""
    logger.info("Начинаем настройку Ollama с Gemma3...")
    
    # Проверяем, установлен ли Ollama
    if not check_ollama_installed():
        logger.info("Ollama не установлен, начинаем установку...")
        if not install_ollama():
            logger.error("Не удалось установить Ollama")
            return False
        
        # Ждем немного после установки
        time.sleep(5)
    else:
        logger.info("Ollama уже установлен")
    
    # Запускаем сервис Ollama
    if not start_ollama_service():
        logger.error("Не удалось запустить сервис Ollama")
        return False
    
    # Ждем запуска сервиса
    logger.info("Ждем запуска сервиса Ollama...")
    time.sleep(10)
    
    # Тестируем подключение
    if not test_ollama_connection():
        logger.error("Не удалось подключиться к Ollama")
        return False
    
    # Загружаем модель Gemma
    model_name = pull_gemma_model()
    if not model_name:
        logger.error("Не удалось загрузить модель Gemma")
        return False
    
    logger.success(f"Настройка завершена! Модель {model_name} готова к использованию")
    
    # Создаем файл конфигурации
    config_content = f"""
# Конфигурация Ollama
OLLAMA_MODEL={model_name}
OLLAMA_BASE_URL=http://localhost:11434
"""
    
    with open(".env.ollama", "w") as f:
        f.write(config_content)
    
    logger.info("Конфигурация сохранена в .env.ollama")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        logger.success("Настройка Ollama завершена успешно!")
        sys.exit(0)
    else:
        logger.error("Настройка Ollama завершилась с ошибками!")
        sys.exit(1)