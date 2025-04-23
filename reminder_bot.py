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

    await callback.message.edit_text(text=str(reminders), reply_markup=reminders_main())

@reminder_router.message(Command('reminders'))
async def reminders_main(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    logger.info(f"Пользователь {callback.from_user.id} перешел к уведомлениям")
    user_id = callback.from_user.id
    if user_id not in cont.get_remindes():
        reminders = JobList(user_id, db)
        cont.get_remindes()[user_id] = reminders
        reminders.load_reminders()
    else:
        reminders = cont.get_remindes()[user_id]

    await callback.message.edit_text(text=str(reminders), reply_markup=reminders_main())

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
         prompt_message += "Формат: <число> <единица> (например: 5 минут, 1 час, 2 дня)"
    elif trigger_type_id == 2: # Сложный интервал (CRON)
         prompt_message += "Формат: CRON-выражение (например: * */1 * * *)"
    elif trigger_type_id == 3: # Точная дата
         prompt_message += "Формат: ДД.ММ.ГГГГ ЧЧ:ММ"
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

    # Теперь у вас есть:
    # - trigger_type (тип напоминания, который выбрал пользователь)
    # - user_input_string (строка, которую ввел пользователь)

    # Сохраняем введенную строку в контексте состояния, если нужно для следующего шага
    # или для обработки после завершения FSM
    await state.update_data(reminder_input_string=user_input_string)

    # Удаляем сообщение пользователя для чистоты диалога
    await message.delete()

    # --- Здесь должна быть логика парсинга и валидации user_input_string ---
    # В зависимости от trigger_type, вы парсите user_input_string.
    # Например:
    # parsed_data = None
    # is_valid = False
    # if trigger_type == 1: # Простой интервал
    #     try:
    #         parsed_data = parse_simple_interval(user_input_string) # Ваша функция парсинга
    #         is_valid = True
    #     except ValueError:
    #         is_valid = False # Неверный формат для простого интервала
    # # ... аналогично для типов 2 и 3
    #
    # --- Обработка результата валидации ---
    # if is_valid:
    #     # Ввод корректен, можно создавать объект напоминания или переходить к следующему шагу
    #     # ...
    #     await message.answer(...)
    #     await state.clear()
    # else:
    #     # Ввод некорректен
    #     # ... (сообщить об ошибке формата)
    #     await message.answer(...)
    #     await state.clear() # Или оставить в состоянии, чтобы пользователь мог повторить
    # --- Конец блока валидации и обработки ---


    # В соответствии с вашим запросом, пока просто подтверждаем получение и очищаем состояние.
    # Логика парсинга и создания объекта напоминания будет добавлена позже.
    await message.answer(f"Получен ввод для напоминания типа {trigger_type}: '{user_input_string}'.")

    # Очищаем состояние после получения ввода
    await state.clear()

@reminder_router.callback_query(NumbersCallbackFactory.filter(F.action == 'add__todolist'))
async def reminders_todolist(callback: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    user_id = callback.from_user.id
    todolist = cont.get_todolist()[user_id]
    await callback.message.edit_text(text=str(todolist), reply_markup=choose_keyboard_from_todolist())