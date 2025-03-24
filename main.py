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

# Инициализация бота
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage, parse_mode="HTML")
user_schedules = {}
user_todolist = {}
show_completed = False

class AddEventStates(StatesGroup):
    waiting_for_event_details = State()


@dp.callback_query(NumbersCallbackFactory.filter(F.action == "add"))
async def start_adding_event(callback: types.CallbackQuery, state: FSMContext):
    message_to_delete = await callback.message.edit_text("Введите событие в формате: 00:00 - 00:01 название", reply_markup=get_user_event())
    await state.update_data(message_to_delete=message_to_delete)
    await state.set_state(AddEventStates.waiting_for_event_details)
    
@dp.message(AddEventStates.waiting_for_event_details)
async def handle_event_details(message: types.Message, state: FSMContext):
    # Регулярное выражение для парсинга строки: время начала, время окончания и название события
    data = await state.get_data()
    if data:
        message_to_delete = data.get('message_to_delete')
    else: message_to_delete = None
    if message_to_delete is not None:
        await message_to_delete.delete()
    pattern = r"(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})\s+(.+)"
    match = re.match(pattern, message.text)
    if match:
        start_time, end_time, event_title = match.groups()
        await message.delete()  # Удаляем сообщение пользователя для чистоты диалога
        await state.clear()  # Очищаем состояние после получения данных
        schedule = user_schedules[message.from_user.id]
        try:
            Schedule.validate_event_time(start_time, end_time)
            even_id = await db.add_schedule_event(message.from_user.id, schedule.day_to_show.date_, start_time, end_time, event_title)
            schedule.add_event(start_time, end_time, event_title, True, even_id)
            await message.answer(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_change_day(schedule.day_to_show.list_events))
        except Exception as e:
            logger.error(f"Ошибка при добавлении события: {e}", exc_info=True)
            await message.answer("Невозможно добавить событие. Проверьте время и название.\nВремя начала должно быть раньше времени конца. Нажмите назад и поробуйте снова.", reply_markup=get_user_event())
    else:
        await message.answer("Неверный формат. Ожидаемый формат ввода: 00:00 - 00:01 название\nНажмите назад и поробуйте снова.", reply_markup=get_user_event())
        await state.clear()

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'back_to_change'))
async def callback_numbers(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    schedule = user_schedules[callback.from_user.id]
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_change_day(schedule.day_to_show.list_events))

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

@dp.message(Command('todo'))
async def cmd_todo(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил команду /todo")
    user_id = message.from_user.id
    
    # Проверяем, есть ли расписание пользователя в словаре
    if user_id not in user_todolist:
        # Если нет, создаем новое расписание и загружаем его из базы данных
        todolist = Todolist('TODO лист', db, show_completed)
        await todolist.load_tasks(user_id)
        user_todolist[user_id] = todolist
    else:
        # Если есть, используем существующее расписание
        todolist = user_todolist[user_id]
    
    await message.answer(f'{str(todolist)}', reply_markup=get_todolist_keyboard())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'today'))
async def callback_numbers(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    schedule = user_schedules[callback.from_user.id]
    schedule.return_to_current_day()
    schedule.return_to_current_week()
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_day())

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
    schedule = user_schedules[callback.from_user.id]
    schedule.return_to_current_day()
    await callback.message.edit_text(f'{str(schedule.week_to_show)}', reply_markup=get_keyboard_week(), parse_mode='HTML')

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'choose_day'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    schedule = user_schedules[callback.from_user.id]
    await callback.message.edit_text(f'{str(schedule.week_to_show)}', reply_markup=get_keyboard_choose_day(schedule.week_to_show.list_days), parse_mode='HTML')

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'back_week'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    value = callback_data.value
    schedule = user_schedules[callback.from_user.id]
    if value == -1:
        schedule.prev_week()
    else:
        schedule.next_week()
    if schedule.weeks.index(schedule.week_to_show) == 0:
        await callback.message.edit_text(f'{str(schedule.week_to_show)}', reply_markup=get_keyboard_week_first(), parse_mode='HTML')
    elif schedule.weeks.index(schedule.week_to_show) == len(schedule.weeks) - 1:
        await callback.message.edit_text(f'{str(schedule.week_to_show)}', reply_markup=get_keyboard_week_last(), parse_mode='HTML')
    else:
        await callback.message.edit_text(f'{str(schedule.week_to_show)}', reply_markup=get_keyboard_week(), parse_mode='HTML')

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'choose'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    value = callback_data.value
    schedule = user_schedules[callback.from_user.id]
    schedule.choose_day(value)
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_day())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'delete'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    value = callback_data.value
    schedule = user_schedules[callback.from_user.id]
    event_to_delete = schedule.day_to_show.list_events[value]
    await db.delete_schedule_event(event_to_delete.event_id)
    schedule.delete_event(value)
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_change_day(schedule.day_to_show.list_events))

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'important'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    value = callback_data.value
    schedule = user_schedules[callback.from_user.id]
    event_to_change = schedule.day_to_show.list_events[value]
    schedule.change_important(value)
    await db.update_event_important(event_to_change.event_id, event_to_change.is_important)
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_change_day(schedule.day_to_show.list_events))

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'cancel_to_day'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    schedule = user_schedules[callback.from_user.id]
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_day())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'to_schedule'))
async def show_schedule(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    logger.info(f"Пользователь {callback.message.from_user.id} запустил команду /schedule")
    user_id = callback.from_user.id
    
    # Проверяем, есть ли расписание пользователя в словаре
    if user_id not in user_schedules:
        # Если нет, создаем новое расписание и загружаем его из базы данных
        schedule = Schedule(user_id, db)
        await schedule.load_events()
        user_schedules[user_id] = schedule
    else:
        # Если есть, используем существующее расписание
        schedule = user_schedules[user_id]
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_day())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'cancel_to_menu'))
async def show_menu(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    await callback.message.edit_text('Меню', reply_markup=get_menu())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'TODO_list'))
async def show_todo_list(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    if callback.from_user.id not in user_todolist:
        user_todolist[callback.from_user.id] = Todolist('TODO лист', db, show_completed)
        todolist1 = user_todolist[callback.from_user.id]
    else:
        todolist1 = user_todolist[callback.from_user.id]
        await todolist1.load_tasks(callback.from_user.id)
    await callback.message.edit_text(str(todolist1), reply_markup=get_todolist_keyboard())

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'cancel_todolist'))
async def show_todo_list(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    await callback.message.edit_text(str(user_todolist[callback.from_user.id]), reply_markup=get_todolist_keyboard())

# Определяем состояния для добавления задачи (одно состояние, как в расписании)
class AddTaskStates(StatesGroup):
    waiting_for_task_details = State()

# Хендлер для начала добавления задачи в TODO-лист
@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'add_task'))
async def start_adding_task(callback: types.CallbackQuery, state: FSMContext):
    message_to_delete = await callback.message.edit_text(
        "Введите задачу в формате: дд.мм название или дд.мм.гггг название",
        reply_markup=get_cancel_keyboard()  # Используем клавиатуру TODO-листа
    )
    await state.update_data(message_to_delete=message_to_delete)
    await state.set_state(AddTaskStates.waiting_for_task_details)

# Хендлер для обработки ввода задачи в TODO-лист
@dp.message(AddTaskStates.waiting_for_task_details)
async def handle_task_details(message: types.Message, state: FSMContext):
    data = await state.get_data()
    message_to_delete = data.get('message_to_delete')
    if message_to_delete is not None:
        await message_to_delete.delete()

    task_input = message.text.strip()
    pattern = r"(\d{1,2}\.\d{1,2}(?:\.\d{4})?)\s+(.+)"  # Формат дд.мм или дд.мм.гггг
    match = re.match(pattern, task_input)
    
    if match:
        deadline, task_text = match.groups()
        await message.delete()  # Удаляем сообщение пользователя
        
        # Используем дедлайн как есть, без форматирования
        try:
            user_id = message.from_user.id
            
            # Проверяем и инициализируем TODO-лист
            if user_id not in user_todolist:
                user_todolist[user_id] = Todolist('TODO лист', db, show_completed)
            todolist = user_todolist[user_id]
            
            # Добавляем задачу с приоритетом по умолчанию (можно настроить позже)
            await todolist.add_task(task_text, deadline, priority=2, user_id=user_id)
            
            await message.answer(
                'Выберите приоритет задачи',
                reply_markup=get_priority_keyboard()
            )
            await state.clear()
        except ValueError as e:
            logger.error(f"Ошибка при добавлении задачи: {e}", exc_info=True)
            await message.answer(
                "Неверная дата. Проверьте формат: дд.мм или дд.мм.гггг.",
                reply_markup=get_cancel_keyboard()
            )
            await state.clear()
    else:
        await message.answer(
            "Неверный формат. Ожидаемый формат ввода: дд.мм название или дд.мм.гггг название",
            reply_markup=get_cancel_keyboard()
        )
        await state.clear()
    
# Определяем состояния для изменения дедлайна задачи
class EditTaskDeadlineStates(StatesGroup):
    waiting_for_new_deadline = State()

# Хендлер для начала изменения дедлайна
@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'change_deadline'))
async def start_editing_deadline(callback: types.CallbackQuery, state: FSMContext):
    message_to_delete = await callback.message.edit_text(
        "Введите новый дедлайн в формате: дд.мм или дд.мм.гггг",
        reply_markup=get_cancel_keyboard()  # Используем клавиатуру TODO-листа
    )
    await state.update_data(message_to_delete=message_to_delete)
    await state.set_state(EditTaskDeadlineStates.waiting_for_new_deadline)

# Хендлер для обработки ввода нового дедлайна
@dp.message(EditTaskDeadlineStates.waiting_for_new_deadline)
async def handle_new_deadline(message: types.Message, state: FSMContext):
    data = await state.get_data()
    message_to_delete = data.get('message_to_delete')
    if message_to_delete is not None:
        await message_to_delete.delete()

    new_deadline = message.text.strip()
    pattern = r"(\d{1,2}\.\d{1,2}(?:\.\d{4})?)"  # Формат дд.мм или дд.мм.гггг
    match = re.match(pattern, new_deadline)
    
    if match:
        deadline = match.group(1)
        await message.delete()  # Удаляем сообщение пользователя
        
        todolist1 = user_todolist[message.from_user.id]
        try:
            todolist1.change_deadline(deadline)
            await db.update_task_deadline(todolist1.current_task.task_id, deadline)
        except ValueError as e:
            logger.error(f"Ошибка при обновлении дедлайна: {e}", exc_info=True)
            await message.answer(
                "Неверная дата. Проверьте формат: дд.мм или дд.мм.гггг.",
                reply_markup=get_cancel_keyboard()
            )
            await state.clear()
            return
        
        text_to_output = f'Изменение задачи\n{'~' * 25}\n{str(todolist1.current_task)}'
        await message.answer(text_to_output, reply_markup=change_task_keyboard(todolist1.current_task.priority))
        await state.clear()
    else:
        await message.answer(
            "Неверный формат. Ожидаемый формат ввода: дд.мм или дд.мм.гггг",
            reply_markup=get_cancel_keyboard()
        )
        await state.clear()
    
@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'priority'))
async def choose_priority_kboard(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    value = callback_data.value
    todolist1 = user_todolist[callback.from_user.id]
    if value == 2:
        await callback.message.edit_text(str(todolist1), reply_markup=get_todolist_keyboard())
    else:
        todolist1.current_task.change_priority(value)
        await db.update_task_priority(todolist1.current_task.task_id, value)
        await callback.message.edit_text(str(todolist1), reply_markup=get_todolist_keyboard())
    
@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'to_complete_task'))
async def choose_completed_task(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    todolist1 = user_todolist[callback.from_user.id]
    await callback.message.edit_text(str(todolist1), reply_markup=show_tasks_complete(todolist1.tasks))
    
@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'complete_task'))
async def completed_task(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    todolist1 = user_todolist[callback.from_user.id]
    value = callback_data.value
    todolist1.set_current_task(value)
    todolist1.complete_task(value)
    await db.delete_task(todolist1.current_task.task_id)
    await callback.message.edit_text(str(todolist1), reply_markup=show_tasks_complete(todolist1.tasks))

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'change_task'))
async def change_task(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    todolist1 = user_todolist[callback.from_user.id]
    await callback.message.edit_text(str(todolist1), reply_markup=show_tasks_keyboard(todolist1.tasks))

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'show_task'))
async def change_task(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    index = callback_data.value
    todolist1 = user_todolist[callback.from_user.id]
    todolist1.set_current_task(index)
    text_to_output = f'Изменение задачи\n{'~' * 25}\n{str(todolist1.current_task)}'
    await callback.message.edit_text(text_to_output, reply_markup=change_task_keyboard(todolist1.current_task.priority))

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'priority_choose'))
async def change_priority(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    priority = callback_data.value
    todolist1 = user_todolist[callback.from_user.id]
    if priority == todolist1.current_task.priority:
        pass
    else:
        todolist1.current_task.change_priority(priority)
        await db.update_task_priority(todolist1.current_task.task_id, priority)
    text_to_output = f'Изменение задачи\n{'~' * 25}\n{str(todolist1.current_task)}'
    await callback.message.edit_text(text_to_output, reply_markup=change_task_keyboard(todolist1.current_task.priority))

@dp.callback_query(NumbersCallbackFactory.filter(F.action == 'delete_task'))
async def delete_task(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    todolist1 = user_todolist[callback.from_user.id]
    todolist1.delete_task()
    await db.delete_task(todolist1.current_task.task_id)
    await callback.message.edit_text(str(todolist1), reply_markup=show_tasks_keyboard(todolist1.tasks))

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
        #user = await db.get_user(847687859)
        await bot_shutdown(dp)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Ошибка в главном цикле: {e}", exc_info=True)