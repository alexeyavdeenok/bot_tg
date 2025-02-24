# logger.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = "my_bot", log_file: str = "bot.log") -> logging.Logger:
    """
    Настройка логгера с ротацией файлов
    :param name: Имя логгера
    :param log_file: Путь к файлу логов
    :return: Объект логгера
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Форматирование
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Ротация логов
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Консольный вывод
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Инициализируем логгер по умолчанию
logger = setup_logger()