from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from keyboard_builder import get_invite_keyboard
from database2 import db
from uuid import uuid4
from keyboard_builder import *
from logger import logger
from aiogram import F
from container import cont
from tictactoe import *

game_router = Router()

@game_router.message(Command('game'))
async def start_game(message: types.Message):
    chat_type = message.chat.type
    if chat_type not in ["group", "supergroup"]:
        await message.reply_text("Игра возможна только в группе!")
        return
    chat_id = message.chat.id
    if chat_id in cont.active_games:
        await message.reply_text("Игра уже идет в этом чате")
        return
    await message.answer(text=f'Пользователь начал игру', reply_markup=get_invite_keyboard(str(chat_id), message.from_user.id))
    

@game_router.callback_query(InviteCallbackFactory.filter(F.action == "accept"))
async def handle_accept_invitation(callback: CallbackQuery, callback_data: InviteCallbackFactory):
    chat_id = int(callback_data.game_id)
    inviter_id = callback_data.inviter_id
    invitee_id = callback.from_user.id
    if inviter_id == invitee_id:
        return
    game = TicTacToe(inviter_id, invitee_id)
    cont.active_games[chat_id] = game
    await callback.message.edit_text(text=str(game), reply_markup=game_keyboard(game.field))

@game_router.callback_query(MoveCallbackFactory.filter(F.action == "move"))
async def game(callback: CallbackQuery, callback_data: MoveCallbackFactory):
    chat_id = callback.message.chat.id
    game = cont.active_games[chat_id]
    if game.current_player != callback.from_user.id:
        return
    cord = list(map(int, callback_data.value.split()))
    game.move(callback.from_user.id, cord)
    if game.state == 'ongoing':
        await callback.message.edit_text(text=str(game), reply_markup=game_keyboard(game.field))
    elif game.state == 'win':
        del cont.active_games[chat_id]
        winner = game.winner
        str_winner = f'Победил игрок {'1' if winner == game.players_by_id["id_1"] else '2'}'
        str_winner += game.return_str_field()
        await callback.message.edit_text(text=str_winner)
    else:
        del cont.active_games[chat_id]
        await callback.message.edit_text(text=f'Ничья{game.return_str_field()}')
    
    
