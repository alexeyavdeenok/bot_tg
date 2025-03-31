from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import Message, CallbackQuery
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class UserData:
    """Класс для хранения данных пользователя."""
    user_schedules: Dict[int, Any] = None
    user_todolist: Dict[int, Any] = None
    show_completed: bool = False

    def __post_init__(self):
        if self.user_schedules is None:
            self.user_schedules = {}
        if self.user_todolist is None:
            self.user_todolist = {}

class UserMiddleware(BaseMiddleware):
    """Мидлвари для добавления данных пользователя в контекст."""
    async def __call__(self, handler, event: Message | CallbackQuery, data: Dict[str, Any]) -> Any:
        # Инициализация данных пользователя
        user_id = event.from_user.id
        if "user_data" not in data:
            data["user_data"] = UserData()
        return await handler(event, data)

def setup_middlewares(dp: Dispatcher):
    """Регистрация мидлвари в диспетчере."""
    dp.message.outer_middleware(UserMiddleware())
    dp.callback_query.outer_middleware(UserMiddleware())