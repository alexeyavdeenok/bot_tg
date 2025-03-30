import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from logger import logger  # Импортируем наш логгер
from database import *
from keyboard_builder import *
from aiogram import F
from dotenv import load_dotenv
import os
from schedule import *
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import re
from todolist import *
from schedule_bot import *
from todolist_bot import *

# Инициализация бота
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ZZ = os.getenv('ZZ')
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage, parse_mode="HTML")
user_schedules = {}
user_todolist = {}
show_completed = False
dp.include_router(todolist_router)
dp.include_router(schedule_router)

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Добавляем пользователя в базу данных
    await db.add_user(user_id, username)
    
    # Создаем начальное расписание для пользователя
    schedule = Schedule(user_id, db)
    
    # Сохраняем расписание в базе данных
    schedule.save_to_database()
    
    logger.info(f"Пользователь {user_id} запустил бота и создал расписание")
    await message.answer('Привет! Я простой бот. Твое расписание создано.')




@dp.message(Command('help'))
async def cmd_help(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил команду /help")
    await message.answer('Список команд:\n/start - запуск бота,\n/help- список команд'
                         '\n/schedule - расписание'
                         '\n/todo - TODO лист'
                         '\n/game - играть (пока не работает)'
                         '\n/notifications - уведомления (пока не работает)')


@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'cancel_to_menu'))
async def show_menu(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    await callback.message.edit_text('Меню', reply_markup=get_menu())


@dp.message((F.text.lower() == 'z') | (F.text.lower() == 'zov'))
async def echo_1(message: types.Message):
    await message.answer(ZZ)


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
        #user = await db.get_user(847687859)
        await bot_shutdown(dp)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Ошибка в главном цикле: {e}", exc_info=True)