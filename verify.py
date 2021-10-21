from asyncio.tasks import Task
from dataclasses import dataclass, field
from datetime import datetime
from functools import reduce
from typing import Dict, List, Optional, Tuple
from random import sample
from aiogram import types
from aiogram.bot.bot import Bot
from aiogram.types.inline_keyboard import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio

from init import config

# inline keyboard

def list_captcha_randomly() -> List[Tuple[str, str]]:
    return sample(list(config['emojis'].items()), len(config['emojis']))


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
class Status:
    just_joined = "just_joined"
    challenged_to_verify = "challenged_to_verify"
    verified = "verified"
    banned = "banned"


@dataclass
class User:
    status: str
    pending_messages_ids: List[int]
    joined_at: datetime
    attempts: int = 0
    scheduled_reject: Optional[Task] = None


@dataclass
class Chat:
    chat_id: int
    users: Dict[int, User] = field(default_factory=dict)


# verification workflow

class Verify:
    chats: Dict[int, Chat] = {}

    @staticmethod
    def can_verify(chat_id: int, user_id: int) -> bool:
        if not chat_id in Verify.chats or not user_id in Verify.chats[chat_id].users:
            return False
        if Verify.chats[chat_id].users[user_id].status != Status.challenged_to_verify:
            return False
        return True

    @staticmethod
    def can_request_verification(chat_id: int, user_id: int) -> bool:
        if not chat_id in Verify.chats or not user_id in Verify.chats[chat_id].users or Verify.chats[chat_id].users[user_id].status == Status.challenged_to_verify:
            return True
        return False

    @staticmethod
    def has_last_chance(chat_id: int, user_id: int) -> bool:
        if Verify.chats[chat_id].users[user_id].attempts == 0 and datetime.now() - Verify.chats[chat_id].users[user_id].joined_at < config['delta']:
            Verify.chats[chat_id].users[user_id].attempts += 1
            return True
        return False

    @staticmethod
    async def authorize(chat: types.Chat, user_id: int) -> None:
        setattr(Verify.chats[chat.id].users[user_id],
                "status", Status.verified)
        if task := Verify.chats[chat.id].users[user_id].scheduled_reject:
            task.cancel()
        await Verify.unrestrict(chat=chat, user_id=user_id)
        await asyncio.gather(*[chat.delete_message(t) for t in Verify.chats[chat.id].users[user_id].pending_messages_ids])

    @staticmethod
    async def reject(chat: types.Chat, user_id: int) -> None:
        setattr(Verify.chats[chat.id].users[user_id], "status", Status.banned)
        await asyncio.gather(chat.kick(user_id), *[chat.delete_message(t) for t in Verify.chats[chat.id].users[user_id].pending_messages_ids])
        if task := Verify.chats[chat.id].users[user_id].scheduled_reject:
            task.cancel()
        Verify.chats[chat.id].users.__delitem__(user_id)

    @staticmethod
    def schedule_reject(bot: Bot, chat: types.Chat, user_id: int) -> None:
        async def kicking() -> None:
            await asyncio.sleep(config['delay'])
            reply = bot.send_message(
                chat_id=chat.id, text=f"Temps écoulé, éjecté cet utilisateur: {user_id}")
            await asyncio.gather(reply, Verify.reject(chat, user_id))
        Verify.chats[chat.id].users[user_id].scheduled_reject = asyncio.create_task(
            kicking())

    @staticmethod
    async def restrict(chat: types.Chat, user_id: int) -> int:
        await chat.restrict(user_id, permissions=types.ChatPermissions(False, False, False, False, False, False, False, False))
        return user_id

    @staticmethod
    async def unrestrict(chat: types.Chat, user_id: int) -> int:
        await chat.restrict(user_id, permissions=types.ChatPermissions(True, True, True, True, False, False, False, False))
        return user_id


__all__ = ["Chat", "Verify", "create_verification_keyboard", "User"]
