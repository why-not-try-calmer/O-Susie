from datetime import timedelta, datetime
from functools import reduce
from typing import List, Tuple
from random import sample
from aiogram import types
from aiogram.bot.bot import Bot
from aiogram.types.inline_keyboard import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio

emojis = {
    "robot": "\U0001F916",
    "snake": "\U0001F40D",
    "alien": "\U0001F47D",
    "gecko": "\U0001F98E",
    "clown": "\U0001F921",
    "shark": "\U0001F988"
}

DELAY = 120
DELTA = timedelta(seconds=DELAY)
PURGATORY = {}


def list_captcha_randomly() -> List[Tuple[str, str]]:
    return sample(list(emojis.items()), len(emojis))


def rows_of_3(buttons: List[InlineKeyboardButton]) -> List[List[InlineKeyboardButton]]:
    def reducer(acc, val):
        if acc and len(acc[-1]) < 3:
            acc[-1].append(val)
            return acc
        acc.append([val])
        return acc
    return reduce(reducer, buttons, [])


def create_verification_keyboard() -> types.InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(text=v, callback_data=k)
               for k, v in list_captcha_randomly()]
    keyboard: List[List[InlineKeyboardButton]
                   ] = rows_of_3(buttons)
    return InlineKeyboardMarkup(3, inline_keyboard=keyboard)


async def restrict(chat: types.Chat, user_id: int) -> int:
    await chat.restrict(user_id, permissions=types.ChatPermissions(False, False, False, False, False, False, False, False))
    return user_id


async def unrestrict(chat: types.Chat, user_id: int) -> int:
    await chat.restrict(user_id, permissions=types.ChatPermissions(True, True, True, True, False, False, False, False))
    return user_id


def delete_after_delay(message_id: int, chat: types.Chat, delay: int) -> None:
    async def deleting(message_id):
        await asyncio.sleep(delay)
        await chat.delete_message(message_id)
        print(f"Message {message_id} in chat {chat} deleted!")
    asyncio.create_task(deleting(message_id))


def kick_after_delay(bot: Bot, chat: types.Chat, user_id: int) -> None:
    async def kicking(user_id: int) -> None:
        await asyncio.sleep(DELAY)
        reply = bot.send_message(
            chat_id=chat.id, text=f"Time elapsed, kicked {user_id}")
        kick = chat.kick(user_id)
        await asyncio.gather(reply, kick)
    PURGATORY[user_id]["timer"] = asyncio.create_task(kicking(user_id))


def visit_purgatory(user_id: int) -> bool:
    if PURGATORY[user_id]["counter"] == 0 and datetime.now() - PURGATORY[user_id]["joined_at"] < DELTA:
        PURGATORY[user_id]["counter"] += 1
        return True
    return False


async def cleanup(chat: types.Chat, user_id: int) -> None:
    await asyncio.gather(*[chat.delete_message(m_id) for m_id in PURGATORY[user_id]["pending_messages"][chat.id]])
    PURGATORY[user_id]["timer"].cancel()
    PURGATORY.__delitem__(user_id)


async def to_heavens(chat: types.Chat, user_id: int) -> None:
    await asyncio.gather(unrestrict(chat=chat, user_id=user_id), cleanup(chat, user_id))


async def to_hell(cb: types.CallbackQuery, user_id: int) -> None:
    await asyncio.gather(cb.message.chat.kick(user_id), cleanup(cb.message.chat, user_id))
