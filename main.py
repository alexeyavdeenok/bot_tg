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

# Инициализация бота
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_schedules = {}

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
                         '\n/schedule - расписание (пока не работает)'
                         '\n/todo - TODO лист (пока не работает)'
                         '\n/game - играть (пока не работает)'
                         '\n/notifications - уведомления (пока не работает)')

@dp.message(Command('schedule'))
async def cmd_schedule(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил команду /schedule")
    user_id = message.from_user.id
    
    # Проверяем, есть ли расписание пользователя в словаре
    if user_id not in user_schedules:
        # Если нет, создаем новое расписание и загружаем его из базы данных
        schedule = Schedule(user_id, db)
        await schedule.load_events()
        user_schedules[user_id] = schedule
    else:
        # Если есть, используем существующее расписание
        schedule = user_schedules[user_id]

    await message.answer(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_day())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'today'))
async def callback_numbers(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    await callback.message.edit_text(f'Тест кнопок', reply_markup=get_keyboard_day())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'change'))
async def callback_numbers(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    schedule = user_schedules[callback.from_user.id]
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_change_day(schedule.day_to_show.list_events))

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'back_day'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    value = callback_data.value
    schedule = user_schedules[callback.from_user.id]
    if value == -1:
        schedule.prev_day()
    else:
        schedule.next_day()
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_day())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'cancel_to_week'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    """
    добавить проверку недели или возвращаться всегда к текущей как вариант 
    """
    schedule = user_schedules[callback.from_user.id]
    schedule.return_to_current_day()
    await callback.message.edit_text(f'{str(schedule.week_to_show)}', reply_markup=get_keyboard_week())

    
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