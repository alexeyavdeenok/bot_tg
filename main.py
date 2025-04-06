import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from logger import logger  # Импортируем наш логгер
from database2 import *
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
from init_database import init_db
from container import cont

# Инициализация бота
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ZZ = os.getenv('ZZ')
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage, parse_mode="HTML")

info_dict = {1: 'Исполоьзуйте < > для отображение следующего(предыдущего) дня или недели\nдля добавления события необходимо выбрать день и приступить к его изменению'
                '\nсобытия, обозначенные ★, отображаются в расписании недели, события, обозначенные ☆, отображаются только в расписании дня'
                '\n для удаления события из дня нажимте "-" во время изменения дня',
             2: 'Добавьте задачу. Для отметки о том, что задача выполнена, нажмите "Выполнено" и выберите выполненные задачи'
                '\n Выполненные задачи по умолчанию удаляются сразу после выполнения, в настройках можно включить отображение выполненных задач.'
                ' Выполненные задачи будут отображаться до следующего вызова команды "todo" или выбора пункта TODO в меню',
             3: 'Информация про напоминания', 
             4: 'Информация про игры'}

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

@dp.message(Command('menu'))
async def cmd_menu(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил команду /menu")
    await message.answer(f'Меню\n{'_' * 30}', reply_markup=get_menu())

@dp.message(Command('help'))
async def cmd_help(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил команду /help")
    await message.answer(text='Выберите команду для ознакомления с функциями бота', reply_markup=info_keyboard())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'info'))
async def show_info_k(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    await callback.message.edit_text(text='Выберите команду для ознакомления с функциями бота', reply_markup=info_keyboard())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'info_command'))
async def show_info(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    value = callback_data.value
    info_text = info_dict[value]
    await callback.message.edit_text(text=info_text, reply_markup=info_keyboard_cancel())  

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'cancel_to_info'))
async def to_info(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    await callback.message.edit_text(text='Выберите команду для ознакомления с функциями бота', reply_markup=info_keyboard())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'cancel_to_menu'))
async def show_menu(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    await callback.message.edit_text(f'Меню\n{'_' * 30}', reply_markup=get_menu())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'settings'))
async def show_settings(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    await callback.message.edit_text(f'Настройки\n {"_" * 30}', reply_markup=get_settings_keyboard())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'settings_command'))
async def change_settings(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    value = callback_data.value
    show_complete = cont.user_todolist[callback.from_user.id].show_completed
    if value == 2:
        await callback.message.edit_text(text=f'TODO лист\n{'~' * 25}', reply_markup=settings_todolist(show_complete))

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'settings_todolist'))
async def change_settings2(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    user_id = callback.from_user.id
    todolist_ = cont.user_todolist[user_id]
    if todolist_.show_completed == False:
        todolist_.show_completed = True
    else: 
        todolist_.show_completed = False
    show_complete = todolist_.show_completed
    await callback.message.edit_text(text=f'TODO лист\n{'~' * 25}', reply_markup=settings_todolist(show_complete))



@dp.message((F.text.lower() == 'z') | (F.text.lower() == 'zov'))
async def echo_1(message: types.Message):
    await message.answer(ZZ)

'''
@dp.message()
async def echo(message: types.Message):
    logger.info(f"Сообщение от {message.from_user.id}: {message.text}")
    await message.answer(f'Вы написали: {message.text}')
'''
async def bot_shutdown(dp: Dispatcher):
    logger.warning("Завершение работы...")
    await db.disconnect()
    await bot.session.close()

async def main():
    try:
        await init_db()
        logger.info("Бот запущен")  # Используем везде наш логгер
        dp.include_router(todolist_router)
        dp.include_router(schedule_router)
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