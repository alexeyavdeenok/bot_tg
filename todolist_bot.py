from aiogram import Router, types
from aiogram.filters import Command
from todolist import *
from database2 import db
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.callback_data import CallbackData
from logger import logger
from aiogram import F
import re
from keyboard_builder import *

todolist_router = Router()
user_todolist = {}
show_completed = False

@todolist_router.message(Command('todo'))
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

@todolist_router.callback_query(NumbersCallbackFactory.filter(F.action == 'TODO_list'))
async def show_todo_list(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    if callback.from_user.id not in user_todolist:
        user_todolist[callback.from_user.id] = Todolist('TODO лист', db, show_completed)
        todolist1 = user_todolist[callback.from_user.id]
    else:
        todolist1 = user_todolist[callback.from_user.id]
        await todolist1.load_tasks(callback.from_user.id)
    await callback.message.edit_text(str(todolist1), reply_markup=get_todolist_keyboard())

@todolist_router.callback_query(NumbersCallbackFactory.filter(F.action == 'cancel_todolist'))
async def show_todo_list(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    await callback.message.edit_text(str(user_todolist[callback.from_user.id]), reply_markup=get_todolist_keyboard())

# Определяем состояния для добавления задачи (одно состояние, как в расписании)
class AddTaskStates(StatesGroup):
    waiting_for_task_details = State()

# Хендлер для начала добавления задачи в TODO-лист
@todolist_router.callback_query(NumbersCallbackFactory.filter(F.action == 'add_task'))
async def start_adding_task(callback: types.CallbackQuery, state: FSMContext):
    message_to_delete = await callback.message.edit_text(
        "Введите задачу в формате: дд.мм название или дд.мм.гггг название",
        reply_markup=get_cancel_keyboard()  # Используем клавиатуру TODO-листа
    )
    await state.update_data(message_to_delete=message_to_delete)
    await state.set_state(AddTaskStates.waiting_for_task_details)

# Хендлер для обработки ввода задачи в TODO-лист
@todolist_router.message(AddTaskStates.waiting_for_task_details)
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
@todolist_router.callback_query(NumbersCallbackFactory.filter(F.action == 'change_deadline'))
async def start_editing_deadline(callback: types.CallbackQuery, state: FSMContext):
    message_to_delete = await callback.message.edit_text(
        "Введите новый дедлайн в формате: дд.мм или дд.мм.гггг",
        reply_markup=get_cancel_keyboard()  # Используем клавиатуру TODO-листа
    )
    await state.update_data(message_to_delete=message_to_delete)
    await state.set_state(EditTaskDeadlineStates.waiting_for_new_deadline)

# Хендлер для обработки ввода нового дедлайна
@todolist_router.message(EditTaskDeadlineStates.waiting_for_new_deadline)
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
    
@todolist_router.callback_query(NumbersCallbackFactory.filter(F.action == 'priority'))
async def choose_priority_kboard(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    value = callback_data.value
    todolist1 = user_todolist[callback.from_user.id]
    if value == 2:
        await callback.message.edit_text(str(todolist1), reply_markup=get_todolist_keyboard())
    else:
        todolist1.current_task.change_priority(value)
        await db.update_task_priority(todolist1.current_task.task_id, value)
        await callback.message.edit_text(str(todolist1), reply_markup=get_todolist_keyboard())
    
@todolist_router.callback_query(NumbersCallbackFactory.filter(F.action == 'to_complete_task'))
async def choose_completed_task(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    todolist1 = user_todolist[callback.from_user.id]
    await callback.message.edit_text(str(todolist1), reply_markup=show_tasks_complete(todolist1.tasks))
    
@todolist_router.callback_query(NumbersCallbackFactory.filter(F.action == 'complete_task'))
async def completed_task(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    todolist1 = user_todolist[callback.from_user.id]
    value = callback_data.value
    todolist1.set_current_task(value)
    todolist1.complete_task(value)
    await db.delete_task(todolist1.current_task.task_id)
    await callback.message.edit_text(str(todolist1), reply_markup=show_tasks_complete(todolist1.tasks))

@todolist_router.callback_query(NumbersCallbackFactory.filter(F.action == 'change_task'))
async def change_task(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    todolist1 = user_todolist[callback.from_user.id]
    await callback.message.edit_text(str(todolist1), reply_markup=show_tasks_keyboard(todolist1.tasks))

@todolist_router.callback_query(NumbersCallbackFactory.filter(F.action == 'show_task'))
async def change_task(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    index = callback_data.value
    todolist1 = user_todolist[callback.from_user.id]
    todolist1.set_current_task(index)
    text_to_output = f'Изменение задачи\n{'~' * 25}\n{str(todolist1.current_task)}'
    await callback.message.edit_text(text_to_output, reply_markup=change_task_keyboard(todolist1.current_task.priority))

@todolist_router.callback_query(NumbersCallbackFactory.filter(F.action == 'priority_choose'))
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

@todolist_router.callback_query(NumbersCallbackFactory.filter(F.action == 'delete_task'))
async def delete_task(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    todolist1 = user_todolist[callback.from_user.id]
    todolist1.delete_task()
    await db.delete_task(todolist1.current_task.task_id)
    await callback.message.edit_text(str(todolist1), reply_markup=show_tasks_keyboard(todolist1.tasks))
