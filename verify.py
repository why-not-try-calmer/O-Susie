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

# emojis bytecodes

emojis = {
    "robot": "\U0001F916",
    "snake": "\U0001F40D",
    "alien": "\U0001F47D",
    "gecko": "\U0001F98E",
    "clown": "\U0001F921",
    "shark": "\U0001F988"
}

# delay before kick

DELAY = 120
DELTA = timedelta(seconds=DELAY)


# inline keyboard

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


# state data

@dataclass
class UserData:
    counter: int
    pending_messages_ids: List[int]
    joined_at: datetime
    timer: Optional[Task] = None


@dataclass
class ChatData:
    chat_id: int
    users: Dict[int, UserData] = {}


# verification workflow

class Verify:
    chats_state: Dict[int, ChatData] = {}

    @staticmethod
    def visit_purgatory(chat_id: int, user_id: int) -> bool:
        if Verify.chats_state[chat_id].users[user_id].counter == 0 and datetime.now() - Verify.chats_state[chat_id].users[user_id].joined_at < DELTA:
            Verify.chats_state[chat_id].users[user_id].counter += 1
            return True
        return False

    @staticmethod
    async def cleanup(chat: types.Chat, user_id: int) -> None:
        await asyncio.gather(*[chat.delete_message(m_id) for m_id in Verify.chats_state[chat.id].users[user_id].pending_messages_ids])
        if timer := Verify.chats_state[chat.id].users[user_id].timer:
            timer.cancel()
        Verify.chats_state[chat.id].users.__delitem__(user_id)
        if not Verify.chats_state[chat.id].users:
            Verify.chats_state.__delitem__(chat.id)

    @staticmethod
    async def to_heavens(chat: types.Chat, user_id: int) -> None:
        await asyncio.gather(Verify.unrestrict(chat=chat, user_id=user_id), Verify.cleanup(chat, user_id))

    @staticmethod
    async def to_hell(cb: types.CallbackQuery, user_id: int) -> None:
        await asyncio.gather(cb.message.chat.kick(user_id), Verify.cleanup(cb.message.chat, user_id))

    @staticmethod
    def kick_after_delay(bot: Bot, chat: types.Chat, user_id: int) -> None:
        async def kicking() -> None:
            await asyncio.sleep(DELAY)
            reply = bot.send_message(
                chat_id=chat.id, text=f"Time elapsed, kicked {user_id}")
            kick = chat.kick(user_id)
            await asyncio.gather(reply, kick, Verify.cleanup(chat, user_id))
        Verify.chats_state[chat.id].users[user_id].timer = asyncio.create_task(
            kicking())

    @staticmethod
    async def restrict(chat: types.Chat, user_id: int) -> int:
        await chat.restrict(user_id, permissions=types.ChatPermissions(False, False, False, False, False, False, False, False))
        return user_id

    @staticmethod
    async def unrestrict(chat: types.Chat, user_id: int) -> int:
        await chat.restrict(user_id, permissions=types.ChatPermissions(True, True, True, True, False, False, False, False))
        return user_id
