import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from logger import logger  # Импортируем наш логгер
from database import *
from keyboard_builder import *
from aiogram import F
from dotenv import load_dotenv
import os

# Инициализация бота
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    await db.add_user(message.from_user.id, message.from_user.username)
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    await message.answer('Привет! Я простой бот.')

@dp.message(Command('help'))
async def cmd_help(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил команду /help")
    await message.answer('Список команд:\n/start - запуск бота,\n/help- список команд'
                         '\n/schedule - расписание (пока не работает)'
                         '\n/todo - TODO лист (пока не работает)'
                         '\n/game - играть (пока не работает)'
                         '\n/notifications - уведомления (пока не работает)')

@dp.message(Command('schedule'))
async def cmd_schedule(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил команду /schedule")
    await message.answer(f'Тест кнопок           ', reply_markup=get_keyboard_week('03.03.2025 - 09.03.2025'))

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'today'))
async def callback_numbers(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    await callback.message.edit_text(f'Тест кнопок', reply_markup=get_keyboard_day('05.03.2025'))

@dp.message((F.text.lower() == 'z') | (F.text.lower() == 'zov'))
async def echo_1(message: types.Message):
    await message.answer('СЛАВА Z🙏❤️СЛАВА Z🙏❤️АНГЕЛА ХРАНИТЕЛЯ Z КАЖДОМУ ИЗ ВАС🙏❤️БОЖЕ ХРАНИ Z🙏❤️СПАСИБО ВАМ НАШИ Z🙏🏼❤️🇷🇺 ХРОНИ Z✊🇷🇺💯Слава Богу Z🙏❤️СЛАВА Z🙏❤️СЛАВА Z🙏❤️АНГЕЛА ХРАНИТЕЛЯ Z КАЖДОМУ')


@dp.message()
async def echo(message: types.Message):
    logger.info(f"Сообщение от {message.from_user.id}: {message.text}")
    await message.answer(f'Вы написали: {message.text}')

async def bot_shutdown(dp: Dispatcher):
    logger.warning("Завершение работы...")
    await db.disconnect()
    await bot.session.close()

async def main():
    global db
    try:
        db = Database()
        await db.connect()
        logger.info("Бот запущен")  # Используем везде наш логгер
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
    finally:
        user = await db.get_user(847687859)
        await bot_shutdown(dp)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Ошибка в главном цикле: {e}", exc_info=True)