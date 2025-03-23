from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from typing import Optional
from aiogram.filters.callback_data import CallbackData

empty_star = "☆"   
filled_star = "★"  
priority_dict = {1: '🟨', 2: '🟧', 3: '🟥'}

class NumbersCallbackFactory(CallbackData, prefix="fabnum"):
    action: str
    value: Optional[int] = None
    
def get_keyboard_week():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="<", callback_data=NumbersCallbackFactory(action="back_week", value=-1)
    )
    
    builder.button(
        text=">", callback_data=NumbersCallbackFactory(action="back_week", value=+1)
    )
    builder.button(
        text="Текущий день", callback_data=NumbersCallbackFactory(action="today")
    )
    builder.button(
        text="Выбрать день", callback_data=NumbersCallbackFactory(action="choose_day")
    )
    builder.button(
        text="В меню", callback_data=NumbersCallbackFactory(action="cancel_to_menu"))
    builder.adjust(2, 1, 1, 1)
    return builder.as_markup()

def get_keyboard_week_last():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="<", callback_data=NumbersCallbackFactory(action="back_week", value=-1)
    )
    builder.button(
        text="Текущий день", callback_data=NumbersCallbackFactory(action="today")
    )
    builder.button(
        text="Выбрать день", callback_data=NumbersCallbackFactory(action="choose_day")
    )
    builder.button(
        text="В меню", callback_data=NumbersCallbackFactory(action="cancel_to_menu"))
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()

def get_keyboard_week_first():
    builder = InlineKeyboardBuilder()
    builder.button(
        text=">", callback_data=NumbersCallbackFactory(action="back_week", value=+1)
    )
    builder.button(
        text="Текущий день", callback_data=NumbersCallbackFactory(action="today")
    )
    builder.button(
        text="Выбрать день", callback_data=NumbersCallbackFactory(action="choose_day")
    )
    builder.button(
        text="В меню", callback_data=NumbersCallbackFactory(action="cancel_to_menu"))
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()

def get_keyboard_day():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="<", callback_data=NumbersCallbackFactory(action="back_day", value=-1)
    )
    builder.button(
        text=">", callback_data=NumbersCallbackFactory(action="back_day", value=+1)
    )
    builder.button(text='Изменить', callback_data=NumbersCallbackFactory(action='change'))
    builder.button(
        text="Расписание на неделю", callback_data=NumbersCallbackFactory(action="cancel_to_week"))
    builder.button(text='В меню', callback_data=NumbersCallbackFactory(action='cancel_to_menu'))
    builder.adjust(2, 1, 1, 1)
    return builder.as_markup()

def get_keyboard_change_day(list_events):
    builder = InlineKeyboardBuilder()
    for i in range(len(list_events)):
        builder.button(
            text='-', callback_data=NumbersCallbackFactory(action='delete', value=i)
        )
        builder.button(text=list_events[i].title, callback_data=NumbersCallbackFactory(action='None'))
        if list_events[i].is_important:
            builder.button(text=f'{filled_star}', callback_data=NumbersCallbackFactory(action='important', value=i))
        else:
            builder.button(text=f'{empty_star}', callback_data=NumbersCallbackFactory(action='important', value=i))    
    builder.button(text='Добавить', callback_data=NumbersCallbackFactory(action='add'))
    builder.button(text='Назад', callback_data=NumbersCallbackFactory(action='cancel_to_day'))
    builder.adjust(3)
    return builder.as_markup()

def get_keyboard_choose_day(list_days):
    builder = InlineKeyboardBuilder()
    for i in range(len(list_days)):
        builder.button(
            text=f'{list_days[i].date_.strftime("%d.%m.%Y")} {list_days[i].weekday_name}', callback_data=NumbersCallbackFactory(action='choose', value=i))
    builder.button(text='Назад', callback_data=NumbersCallbackFactory(action='cancel_to_week'))
    builder.adjust(1)
    return builder.as_markup()

def get_user_event():
    builder = InlineKeyboardBuilder()
    builder.button(text='Назад', callback_data=NumbersCallbackFactory(action='back_to_change'))
    return builder.as_markup()

def get_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text='Расписание', callback_data=NumbersCallbackFactory(action='to_schedule'))
    builder.button(text='TODO лист', callback_data=NumbersCallbackFactory(action='TODO_list'))
    builder.button(text='Информация', callback_data=NumbersCallbackFactory(action='info'))
    builder.button(text='Настройки', callback_data=NumbersCallbackFactory(action='settings'))
    builder.adjust(1)
    return builder.as_markup()

def get_todolist_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text='Выполнено', callback_data=NumbersCallbackFactory(action='complete_task'))
    builder.button(text='Добавить', callback_data=NumbersCallbackFactory(action='add_task'))
    builder.button(text='Изменить задачу', callback_data=NumbersCallbackFactory(action='change_task'))
    builder.button(text='Назад', callback_data=NumbersCallbackFactory(action='cancel_to_menu'))
    builder.adjust(1)
    return builder.as_markup()

def get_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text='Назад', callback_data=NumbersCallbackFactory(action='cancel_todolist'))
    return builder.as_markup()

def get_priority_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text=f'{priority_dict[1]} - Низкий', callback_data=NumbersCallbackFactory(action='priority', value=1))
    builder.button(text=f'{priority_dict[2]} - Средний', callback_data=NumbersCallbackFactory(action='priority', value=2))
    builder.button(text=f'{priority_dict[3]} - Высокий', callback_data=NumbersCallbackFactory(action='priority', value=3))
    builder.adjust(3)
    return builder.as_markup()

def change_task_keyboard(priority):
    builder = InlineKeyboardBuilder()
    builder.button(text=f'{priority_dict[1] + ('✅' if priority == 1 else '')}', callback_data=NumbersCallbackFactory(action='priority_choose', value=1))
    builder.button(text=f'{priority_dict[2] + ('✅' if priority == 2 else '')}', callback_data=NumbersCallbackFactory(action='priority_choose', value=2))
    builder.button(text=f'{priority_dict[3] + ("✅" if priority == 3 else "")}', callback_data=NumbersCallbackFactory(action='priority_choose', value=3))
    builder.button(text='Изменить дедлайн', callback_data=NumbersCallbackFactory(action='change_deadline'))
    builder.button(text='Удалить', callback_data=NumbersCallbackFactory(action='delete_task'))
    builder.button(text='Назад', callback_data=NumbersCallbackFactory(action='cancel_to_todolist'))
    builder.adjust(3, 1, 1, 1)
    return builder.as_markup()
    
def show_tasks_keyboard(tasks_list):
    builder = InlineKeyboardBuilder()
    for i in range(len(tasks_list)):
        builder.button(text=str(tasks_list[i]), callback_data=NumbersCallbackFactory(action='show_task', value=i))
    builder.button(text='Назад', callback_data=NumbersCallbackFactory(action='cancel_to_todolist'))
    builder.adjust(1)
    return builder.as_markup()
