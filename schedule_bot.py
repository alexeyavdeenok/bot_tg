from aiogram import Router, types
from aiogram.filters import Command
from schedule import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import re
from aiogram import F
from keyboard_builder import *
from aiogram.filters.callback_data import CallbackData
from logger import logger
from keyboard_builder import *
from database2 import db
from container import cont

schedule_router = Router()
user_schedules = cont.get_schedule()


class AddEventStates(StatesGroup):
    waiting_for_event_details = State()


@schedule_router.callback_query(NumbersCallbackFactory.filter(F.action == "add"))
async def start_adding_event(callback: types.CallbackQuery, state: FSMContext):
    message_to_delete = await callback.message.edit_text("Введите событие в формате: 00:00 - 00:01 название", reply_markup=get_user_event())
    await state.update_data(message_to_delete=message_to_delete)
    await state.set_state(AddEventStates.waiting_for_event_details)

@schedule_router.message(AddEventStates.waiting_for_event_details)
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

@schedule_router.callback_query(NumbersCallbackFactory.filter(F.action == 'back_to_change'))
async def callback_numbers(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    schedule = user_schedules[callback.from_user.id]
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_change_day(schedule.day_to_show.list_events))

@schedule_router.message(Command('schedule'))
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


@schedule_router.callback_query(NumbersCallbackFactory.filter(F.action == 'today'))
async def callback_numbers(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    schedule = user_schedules[callback.from_user.id]
    schedule.return_to_current_day()
    schedule.return_to_current_week()
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_day())

@schedule_router.callback_query(NumbersCallbackFactory.filter(F.action == 'change'))
async def callback_numbers(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    schedule = user_schedules[callback.from_user.id]
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_change_day(schedule.day_to_show.list_events))

@schedule_router.callback_query(NumbersCallbackFactory.filter(F.action == 'back_day'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    value = callback_data.value
    schedule = user_schedules[callback.from_user.id]
    if value == -1:
        schedule.prev_day()
    else:
        schedule.next_day()
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_day())

@schedule_router.callback_query(NumbersCallbackFactory.filter(F.action == 'cancel_to_week'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    schedule = user_schedules[callback.from_user.id]
    schedule.return_to_current_day()
    await callback.message.edit_text(f'{str(schedule.week_to_show)}', reply_markup=get_keyboard_week(), parse_mode='HTML')

@schedule_router.callback_query(NumbersCallbackFactory.filter(F.action == 'choose_day'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    schedule = user_schedules[callback.from_user.id]
    await callback.message.edit_text(f'{str(schedule.week_to_show)}', reply_markup=get_keyboard_choose_day(schedule.week_to_show.list_days), parse_mode='HTML')

@schedule_router.callback_query(NumbersCallbackFactory.filter(F.action == 'back_week'))
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

@schedule_router.callback_query(NumbersCallbackFactory.filter(F.action == 'choose'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    value = callback_data.value
    schedule = user_schedules[callback.from_user.id]
    schedule.choose_day(value)
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_day())

@schedule_router.callback_query(NumbersCallbackFactory.filter(F.action == 'delete'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    value = callback_data.value
    schedule = user_schedules[callback.from_user.id]
    event_to_delete = schedule.day_to_show.list_events[value]
    await db.delete_schedule_event(event_to_delete.event_id)
    schedule.delete_event(value)
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_change_day(schedule.day_to_show.list_events))

@schedule_router.callback_query(NumbersCallbackFactory.filter(F.action == 'important'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    value = callback_data.value
    schedule = user_schedules[callback.from_user.id]
    event_to_change = schedule.day_to_show.list_events[value]
    schedule.change_important(value)
    await db.update_event_important(event_to_change.event_id, event_to_change.is_important)
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_change_day(schedule.day_to_show.list_events))

@schedule_router.callback_query(NumbersCallbackFactory.filter(F.action == 'cancel_to_day'))
async def callback_days(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    schedule = user_schedules[callback.from_user.id]
    await callback.message.edit_text(f'{str(schedule.day_to_show)}', reply_markup=get_keyboard_day())

@schedule_router.callback_query(NumbersCallbackFactory.filter(F.action == 'to_schedule'))
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