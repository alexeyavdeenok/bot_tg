from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from keyboard_builder import get_invite_keyboard, get_invite_action_keyboard
from database2 import db
from uuid import uuid4
from keyboard_builder import *
from logger import logger
from aiogram import F
from container import cont

game_router = Router()

# Обработчик кнопки "Пригласить пользователя"
@game_router.callback_query(NumbersCallbackFactory.filter(F.action == "invite"))
async def handle_invite(callback: CallbackQuery):
    """
    Генерация уникальной ссылки для приглашения.
    """
    inviter_id = callback.from_user.id
    game_id = str(uuid4())[:8]  # Уникальный ID игры

    # Генерация ссылки
    bot_username = (await callback.bot.me()).username
    invite_link = f"https://t.me/{bot_username}?start=invite:{game_id}:{inviter_id}"

    await callback.message.answer(
        f"Отправьте эту ссылку пользователю, чтобы пригласить его:\n\n{invite_link}"
    )

# Обработчик команды /start с параметрами
@game_router.message(Command('start'))
async def cmd_start_with_args(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    args = message.get_args()

    if not args:
        # Если параметров нет, проверяем регистрацию
        if not await db.is_user_registered(user_id):
            await db.add_user(user_id, username)
            await message.answer("Вы зарегистрированы! Добро пожаловать.")
        else:
            await message.answer("Добро пожаловать обратно!")
        return

    # Обработка параметров команды /start
    try:
        action, game_id, inviter_id = args.split(":")
        inviter_id = int(inviter_id)
    except ValueError:
        await message.answer("Неверный формат ссылки.")
        return

    if action == "invite":
        # Проверяем регистрацию пользователя
        if not await db.is_user_registered(user_id):
            # Регистрация нового пользователя
            await db.add_user(user_id, username)
            await message.answer(
                "Вы зарегистрированы! Теперь вы можете начать игру.",
                reply_markup=get_invite_keyboard(game_id, inviter_id)
            )
        else:
            await message.answer(
                "Вы можете присоединиться к игре.",
                reply_markup=get_invite_keyboard(game_id, inviter_id)
            )

# Обработчик принятия приглашения
@game_router.callback_query(InviteCallbackFactory.filter(F.action == "accept"))
async def handle_accept_invitation(callback: CallbackQuery, callback_data: InviteCallbackFactory):
    """
    Обработка принятия приглашения.
    """
    game_id = callback_data.game_id
    invitee_id = callback.from_user.id

    # Проверяем, активна ли игра
    if game_id not in cont.active_games:
        cont.active_games[game_id] = {
            "inviter": callback_data.inviter_id,
            "invitee": invitee_id,
            "state": "ready"
        }
        await callback.message.answer("Вы присоединились к игре! Игра начинается.")
    else:
        await callback.answer("Эта игра уже началась или завершена.")
