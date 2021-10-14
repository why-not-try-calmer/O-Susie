from asyncio.tasks import Task
from dataclasses import dataclass
from datetime import timedelta, datetime
from functools import reduce
from typing import Dict, List, Optional, Tuple
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


@dataclass
class UserData:
    counter: int
    pending_messages_ids: Dict[int, List[int]]
    joined_at: datetime
    timer: Optional[Task] = None


@dataclass
class ChatData:
    chat_id: int
    users: Dict[int, UserData]


class Verify:
    chats_state: Dict[int, ChatData] = {}

    @classmethod
    def visit_purgatory(cls, chat_id: int, user_id: int) -> bool:
        if cls.chats_state[chat_id].users[user_id].counter == 0 and datetime.now() - cls.chats_state[chat_id].users[user_id].joined_at < DELTA:
            cls.chats_state[chat_id].users[user_id].counter += 1
            return True
        return False

    @classmethod
    async def cleanup(cls, chat: types.Chat, user_id: int) -> None:
        await asyncio.gather(*[chat.delete_message(m_id) for m_id in cls.chats_state[chat.id].users[user_id].pending_messages_ids[chat.id]])
        if timer := cls.chats_state[chat.id].users[user_id].timer:
            timer.cancel()
        cls.chats_state[chat.id].users.__delitem__(user_id)

    @classmethod
    async def to_heavens(cls, chat: types.Chat, user_id: int) -> None:
        await asyncio.gather(Verify.unrestrict(chat=chat, user_id=user_id), cls.cleanup(chat, user_id))

    @classmethod
    async def to_hell(cls, cb: types.CallbackQuery, user_id: int) -> None:
        await asyncio.gather(cb.message.chat.kick(user_id), cls.cleanup(cb.message.chat, user_id))

    @classmethod
    def kick_after_delay(cls, bot: Bot, chat: types.Chat, user_id: int) -> None:
        async def kicking() -> None:
            await asyncio.sleep(DELAY)
            reply = bot.send_message(
                chat_id=chat.id, text=f"Time elapsed, kicked {user_id}")
            kick = chat.kick(user_id)
            _cleanup = cls.cleanup(chat, user_id)
            await asyncio.gather(reply, kick, _cleanup)
        cls.chats_state[chat.id].users[user_id].timer = asyncio.create_task(
            kicking())

    @staticmethod
    async def restrict(chat: types.Chat, user_id: int) -> int:
        await chat.restrict(user_id, permissions=types.ChatPermissions(False, False, False, False, False, False, False, False))
        return user_id

    @staticmethod
    async def unrestrict(chat: types.Chat, user_id: int) -> int:
        await chat.restrict(user_id, permissions=types.ChatPermissions(True, True, True, True, False, False, False, False))
        return user_id
