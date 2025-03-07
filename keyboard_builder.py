from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from typing import Optional
from aiogram.filters.callback_data import CallbackData

class NumbersCallbackFactory(CallbackData, prefix="fabnum"):
    action: str
    value: Optional[int] = None
    
def get_keyboard_week(date_from_week):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=date_from_week, callback_data=NumbersCallbackFactory(action="None")
    )
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
    builder.adjust(1, 2, 1, 1, 1)
    return builder.as_markup()

def get_keyboard_day(date_from_day):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=date_from_day, callback_data=NumbersCallbackFactory(action="None")
    )
    builder.button(
        text="<", callback_data=NumbersCallbackFactory(action="back_day", value=-1)
    )
    builder.button(
        text=">", callback_data=NumbersCallbackFactory(action="back_day", value=+1)
    )
    builder.button(text='Изменить', callback_data=NumbersCallbackFactory(action='change'))
    builder.button(
        text="Назад", callback_data=NumbersCallbackFactory(action="cancel"))
    builder.adjust(1, 2, 1, 1)
    return builder.as_markup()
