import asyncio
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import logging
from logging.handlers import RotatingFileHandler

# Настройка логгера
logger = logging.getLogger("my_bot")
logger.setLevel(logging.INFO)

# Формат записей
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Ротация логов: максимум 5 файлов по 1 МБ каждый
file_handler = RotatingFileHandler(
    filename="bot.log",
    maxBytes=1024 * 1024,  # 1 МБ
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Также выводим логи в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Инициализация бота
bot = Bot(token='*')
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} (@{message.from_user.username}) запустил бота")
    await message.answer('Привет! Я простой бот.')

# Обработчик текстовых сообщений
@dp.message()
async def echo(message: types.Message):
    logger.info(
        f"Получено сообщение от {message.from_user.id} (@{message.from_user.username}): {message.text}"
    )
    await message.answer(f'Вы написали: {message.text}')

async def shutdown(dp: Dispatcher):
    logger.warning("Завершение работы...")
    await bot.session.close()

async def main():
    try:
        logger.info("Бот запущен")
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        await shutdown(dp)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Ошибка в главном цикле: {e}", exc_info=True)
