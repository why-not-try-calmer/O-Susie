from datetime import datetime
import asyncio
from aiogram import types
from aiogram.utils.markdown import code

from verify import *
from verify import Status
from init import config, bot, dp

# init


async def on_startup(app) -> None:
    """Simple hook for aiohttp application which manages webhook"""
    await bot.delete_webhook()
    await bot.set_webhook(config['webhook_url'])


async def start_worker() -> None:
    await bot.delete_webhook()
    await dp.start_polling()


# handlers


@dp.callback_query_handler()
async def pressed_verification_button(cb: types.CallbackQuery) -> None:
    user_id = cb.from_user.id
    chat_id = cb.message.chat.id
    key = cb.data

    if not Verify.can_verify(chat_id, user_id):
        return

    if key == config['key']:
        await Verify.authorize(chat=cb.message.chat, user_id=user_id)
        text = f"Welcome {code(cb.from_user.full_name)}, have a lot of fun!"
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown"
        )

    elif Verify.has_last_chance(chat_id, user_id):
        text = "Incorrect answer. Make sure to get it right next time or you will be banned *permanently*."
        response_msg = await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        Verify.chats[chat_id].users[user_id].pending_messages_ids.append(
            response_msg.message_id)
    else:
        await Verify.reject(bot, cb.message.chat, user_id)


@dp.message_handler(content_types=types.ContentTypes.NEW_CHAT_MEMBERS)
async def just_joined(message: types.Message) -> None:
    user_id = message.from_user.id
    chat = message.chat

    if not Verify.can_request_verification(chat.id, user_id):
        return

    values = [getattr(u, "_values") for u in message.new_chat_members]
    uids = [u["id"] for u in values if not u["is_bot"]]
    response_msg = await bot.send_message(
        chat_id=chat.id,
        text=f"Hi [{message.from_user.mention}](tg://user?id={user_id})! Please answer the question below within the next (*{config['delay']} seconds*). Which emoji below represents an animal often associated with openSUSE?",
        parse_mode="Markdown",
        reply_markup=create_verification_keyboard(),
    )

    for task in asyncio.as_completed([Verify.restrict(chat, _id) for _id in uids]):
        uid = await task
        if not chat.id in Verify.chats:
            Verify.chats[chat.id] = Chat(chat.id)
        Verify.chats[chat.id].users[uid] = User(
            pending_messages_ids=[response_msg.message_id],
            joined_at=datetime.now(),
            attempts=0,
            status=Status.challenged_to_verify
        )
        Verify.schedule_reject(bot, chat, uid)


@dp.message_handler(content_types=types.ContentTypes.ANY)
async def handle_otherwise(_any) -> None:
    print(f"Silently handled: {_any}")


if __name__ == '__main__':
    from sys import argv
    import uvloop
    uvloop.install()
    loop = asyncio.get_event_loop()
    if len(argv) >= 2 and "--webhook" in argv:
        print(
            f"Called with {argv}, running as aiohttp server after setting webhook.")
        from aiogram.utils import executor
        executor.start_webhook(
            dispatcher=dp,
            webhook_path=config['webhook_url_path'],
            loop=loop,
            skip_updates=True,
            on_startup=on_startup,
            host=config['host'],
            port=config['port']
        )
    else:
        print(f"Called with {argv}, running as long-polling worker.")
        asyncio.run(start_worker())
