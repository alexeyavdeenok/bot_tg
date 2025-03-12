from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from typing import Optional
from aiogram.filters.callback_data import CallbackData

empty_star = "☆"   
filled_star = "★"  

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
        text="Назад", callback_data=NumbersCallbackFactory(action="cancel"))
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
        text="Назад", callback_data=NumbersCallbackFactory(action="cancel"))
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()

def get_keyboard_week_first():
    builder = InlineKeyboardBuilder()
    builder.button(
        text=">", callback_data=NumbersCallbackFactory(action="back_week", value=-1)
    )
    builder.button(
        text="Текущий день", callback_data=NumbersCallbackFactory(action="today")
    )
    builder.button(
        text="Выбрать день", callback_data=NumbersCallbackFactory(action="choose_day")
    )
    builder.button(
        text="Назад", callback_data=NumbersCallbackFactory(action="cancel"))
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
    builder.button(text='Назад', callback_data=NumbersCallbackFactory(action='cancel_to_menu'))
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
            builder.button(text=f'{filled_star}', callback_data=NumbersCallbackFactory(action='not_important', value=i))
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
    pass
