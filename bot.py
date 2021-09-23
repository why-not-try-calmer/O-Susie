from verify import *
from aiogram import Bot, Dispatcher, types
from datetime import datetime
from os import environ as env
from dotenv import load_dotenv
from urllib.parse import urljoin

load_dotenv()
TOKEN = env["TELEGRAM_BOT_TOKEN"]
WEBHOOK_HOST = env["WEBHOOK_HOST"]
WEBHOOK_URL_PATH = env["WEBHOOK_ENDPOINT"] + TOKEN
WEBHOOK_URL = urljoin(WEBHOOK_HOST, WEBHOOK_URL_PATH)
KEY = env["KEY"]

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

""" 
|- LOGGING -|
import logging
logging.basicConfig(level=logging.INFO)
from aiogram.contrib.middlewares.logging import LoggingMiddleware
dp.middleware.setup(LoggingMiddleware())
"""


@dp.callback_query_handler()
async def pressed_verification_button(cb: types.CallbackQuery) -> None:
    user_id = cb.from_user.id
    if not user_id in PURGATORY:
        return

    chat_id = cb.message.chat.id
    key = cb.data

    if key == KEY:
        replying = bot.send_message(
            chat_id=chat_id,
            text=f"Welcome, _{cb.from_user.mention}_! Have a lot of fun!",
            parse_mode="Markdown"
        )
        await asyncio.gather(replying, to_heavens(chat=cb.message.chat, user_id=user_id))

    elif visit_purgatory(user_id):
        text = "Wrong answer. Make sure you get it right now or you will get banned *forever*."
        response_msg = await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        delete_after_delay(message_id=response_msg.message_id,
                           chat=response_msg.chat, delay=DELAY+10)

    else:
        await to_hell(cb, user_id)


@dp.message_handler(content_types=types.ContentTypes.NEW_CHAT_MEMBERS)
async def just_joined(message: types.Message) -> None:
    chat = message.chat
    _values = [getattr(u, "_values") for u in message.new_chat_members]
    users_ids = [u["id"] for u in _values if not u["is_bot"]]

    response_msg = await bot.send_message(
        chat_id=message.chat.id,
        text=f"Hey, a new gecko! If you are not a bot, please answer this question within the next *{DELAY} seconds*. What emoji below resembles the openSUSE mascot the most?",
        parse_mode="Markdown",
        reply_markup=create_verification_keyboard()
    )
    delete_after_delay(message_id=response_msg.message_id,
                       chat=response_msg.chat, delay=DELAY+10)

    for task in asyncio.as_completed([restrict(chat, _id) for _id in users_ids]):
        user_id = await task
        PURGATORY[user_id] = {"joined_at": datetime.now(), "counter": 0}
        kick_after_delay(bot, chat, user_id)


@dp.message_handler()
async def handle_messages(message: types.Message) -> None:
    """ Because the bot might come online after the user has had time to send a couple of messages. """
    if message.from_user.id in PURGATORY:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


@dp.message_handler(content_types=types.ContentTypes.ANY)
async def handle_otherwise(_any) -> None:
    print(f"Silently handled: {_any}")


async def on_startup(_app) -> None:
    """Simple hook for aiohttp application which manages webhook"""
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)


async def start_worker() -> None:
    await bot.delete_webhook()
    await dp.start_polling()


if __name__ == '__main__':
    from sys import argv
    import uvloop
    uvloop.install()
    loop = asyncio.get_event_loop()
    if len(argv) >= 2 and argv[1] == "--webhook":
        print(
            f"Called with {argv}, running as aiohttp server after setting webhook.")
        from aiogram.utils import executor
        executor.start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_URL_PATH,
            loop=loop,
            skip_updates=True,
            on_startup=on_startup,
            host="0.0.0.0",
            port=int(env.get('PORT', 8080))
        )
    else:
        print(f"Called with {argv}, running as long-polling worker.")
        asyncio.run(start_worker())
