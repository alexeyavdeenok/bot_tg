from aiogram import Router, types
from aiogram.filters import Command
from schedule import *
from todolist import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import re
from job import *
from aiogram import F
from keyboard_builder import *
from aiogram.filters.callback_data import CallbackData
from logger import logger
from keyboard_builder import *
from database2 import db
from container import cont
from init_database import *
from datetime import date

reminder_router = Router()

@reminder_router.callback_query(NumbersCallbackFactory.filter(F.action == 'reminders'))
async def reminders_main(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    logger.info(f"Пользователь {callback.from_user.id} перешел к уведомлениям")
    user_id = callback.from_user.id
    if user_id not in cont.get_remindes():
        reminders = JobList(user_id, db)
        cont.get_remindes()[user_id] = reminders
        reminders.load_reminders()
    else:
        reminders = cont.get_remindes()[user_id]

    await callback.message.edit_text(text=str(reminders), reply_markup=reminders_main_keyboard())

@reminder_router.message(Command('notifications'))
async def reminders_main(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} перешел к уведомлениям")
    user_id = message.from_user.id
    if user_id not in cont.get_remindes():
        reminders = JobList(user_id, db)
        cont.get_remindes()[user_id] = reminders
        reminders.load_reminders()
    else:
        reminders = cont.get_remindes()[user_id]

    await message.answer(text=str(reminders), reply_markup=reminders_main_keyboard())

class AddReminderStates(StatesGroup):
    waiting_for_reminder_input = State()

@reminder_router.callback_query(NumbersCallbackFactory.filter(F.action == 'choose_trigger'))
async def process_trigger_selection(
    callback: types.CallbackQuery,
    callback_data: NumbersCallbackFactory,
    state: FSMContext
):
    """
    Обрабатывает выбор типа напоминания пользователем
    и переводит FSM в состояние ожидания ввода информации.
    """
    trigger_type_id = callback_data.value # Получаем id выбранного типа напоминания

    # Сохраняем выбранный тип напоминания в контексте состояния
    await state.update_data(trigger_type=trigger_type_id)

    # Формируем сообщение-подсказку для пользователя в зависимости от типа
    prompt_message = "Пожалуйста, введите информацию для напоминания:\n"
    if trigger_type_id == 1: # Простой интервал
         prompt_message += "Формат: <текст напоминания>; <число> <единица измерения> (например: 5 минут, 1 час, 2 дня)\n после текста напоминания введите ; (субботник; 4 часа)"
    elif trigger_type_id == 2: # Сложный интервал (CRON)
         prompt_message += "Формат: <текст напоминания>; <дни недели> <время> (дни недели могут быть перечислены через , или можно указать промежуток через - (например понедельник-среда == понедельник, вторник, среда))"
    elif trigger_type_id == 3: # Точная дата
         prompt_message += "Формат: <текст напоминания>; <время> <дата> (дата в формате день.месяц.год)"
    else:
         prompt_message += "Неизвестный тип напоминания. Введите данные." # Fallback

    # Редактируем сообщение с клавиатурой выбора типа на сообщение-подсказку
    # и сохраняем его, чтобы потом удалить
    message_to_delete = await callback.message.edit_text(
        prompt_message,
        reply_markup=get_cancel_keyboard() # Добавляем кнопку отмены
    )
    await state.update_data(message_to_delete=message_to_delete)

    # Устанавливаем состояние ожидания ввода информации
    await state.set_state(AddReminderStates.waiting_for_reminder_input)

    # Отвечаем на колбек (обязательно)
    await callback.answer()

@reminder_router.message(AddReminderStates.waiting_for_reminder_input)
async def handle_reminder_input(message: types.Message, state: FSMContext):
    """
    Обрабатывает сообщение пользователя с информацией для напоминания.
    Получает сохраненный тип напоминания и введенную строку.
    """
    data = await state.get_data()
    message_to_delete = data.get('message_to_delete')
    trigger_type = data.get('trigger_type') # Получаем ранее сохраненный тип

    # Удаляем предыдущее сообщение бота (подсказку)
    if message_to_delete is not None:
        try:
            await message_to_delete.delete()
        except Exception as e:
            # Логируем ошибку, если не удалось удалить сообщение (например, оно уже было удалено)
            # logger.error(f"Не удалось удалить сообщение: {e}")
            pass # Для примера просто пропускаем ошибку

    # Получаем введенную пользователем строку
    user_input_string = message.text.strip()

    await state.update_data(reminder_input_string=user_input_string)

    # Удаляем сообщение пользователя для чистоты диалога
    await message.delete()

    await message.answer(f"Получен ввод для напоминания типа {trigger_type}: '{user_input_string}'.")
    try:
        name, trigger_time = user_input_string.split(';')
        test_job = Job(name, trigger_type, trigger_time)
        user_id = message.from_user.id
        joblist = cont.get_remindes()[user_id]
        await joblist.add_job(name, trigger_type, trigger_time)
        await message.answer(text=str(joblist), reply_markup=reminders_main_keyboard())
    except Exception as e:
        await message.answer(text=str(e), reply_markup=get_cancel_reminders())

    # Очищаем состояние после получения ввода
    await state.clear()

@reminder_router.callback_query(NumbersCallbackFactory.filter(F.action == 'add__todolist'))
async def reminders_todolist(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    user_id = callback.from_user.id
    todolist = cont.get_todolist()[user_id]
    todolist_to_show = [i for i in todolist.tasks if (i.deadline - date.today()).days > 0]
    await callback.message.edit_text(text='Выберите задачу для напоминания\n' + str(todolist), reply_markup=choose_keyboard_from_todolist(todolist_to_show))

@reminder_router.callback_query(NumbersCallbackFactory.filter(F.action == 'add_reminder'))
async def reminders_input(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    await callback.message.edit_text(text='Добавьте напоминание вручную или выберите существующее событие', reply_markup=add_reminder_keyboard())

@reminder_router.callback_query(NumbersCallbackFactory.filter(F.action == 'add_reminder_input'))
async def reminders_input(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    await callback.message.edit_text(text='Выберите периодичность напоминаний', reply_markup=add_reminder_input_keyboard())

@reminder_router.callback_query(NumbersCallbackFactory.filter(F.action == 'delete_reminder'))
async def reminders_delete(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    user_id = callback.from_user.id
    joblist = cont.get_remindes()[user_id]
    await callback.message.edit_text(text='Нажмите на уведомление чтобы его удалить', reply_markup=change_reminders(joblist.job_list))

@reminder_router.callback_query(NumbersCallbackFactory.filter(F.action == 'delete_rem'))
async def reminders_delete(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    index = callback_data.value
    user_id = callback.from_user.id
    joblist = cont.get_remindes()[user_id]
    await joblist.delete_job(index)
    await callback.message.edit_text(text='Нажмите на уведомление чтобы его удалить', reply_markup=change_reminders(joblist.job_list))

@reminder_router.callback_query(NumbersCallbackFactory.filter(F.action == 'cancel_to_reminder_keyboard'))
async def reminders_cancel(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    reminders = cont.get_remindes()[callback.from_user.id]
    await callback.message.edit_text(text=str(reminders), reply_markup=reminders_main_keyboard())

@reminder_router.callback_query(NumbersCallbackFactory.filter(F.action == 'add_reminder_todolist'))
async def reminders_add_todolist(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    user_id = callback.from_user.id
    index = callback_data.value
    todolist = cont.get_todolist()[user_id]
    todolist_to_show = [i for i in todolist.tasks if (i.deadline - date.today()).days > 0]
    task = todolist_to_show[index]
    joblist = cont.get_remindes()[user_id]
    await joblist.import_job_from_todolist(task)
    await callback.message.edit_text(text=str(joblist), reply_markup=reminders_main_keyboard())

def get_important_events_after_today(schedule):
    today = date.today()  # Получаем текущую дату
    important_events = []

    # Проходим по всем неделям в Schedule
    for week in schedule.weeks:
        # Проходим по всем дням в текущей неделе
        for day in week.list_days:
            # Проверяем, что дата дня >= сегодняшней дате
            if day.date_ >= today:
                # Проходим по всем событиям в текущем дне
                for event in day.list_events:
                    # Если событие важное, добавляем его в список
                    if event.is_important:
                        important_events.append(
                            f"{event.title}  {event.start} {day.date_.strftime('%Y-%m-%d')}"
                        )
    return important_events