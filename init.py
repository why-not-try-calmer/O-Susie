from datetime import timedelta
from urllib.parse import urljoin
from aiogram import Bot, Dispatcher
from os import environ as env

DELAY = 120


config = {
    "webhook_host": env["WEBHOOK_HOST"],
    "webhook_url_path": env["WEBHOOK_ENDPOINT"] + env["TELEGRAM_BOT_TOKEN"],
    "webhook_url": urljoin(env["WEBHOOK_HOST"], env["WEBHOOK_ENDPOINT"] + env["TELEGRAM_BOT_TOKEN"]),
    "key": env["KEY"],
    "port": int(env.get("PORT", 3001)),
    "host":"0.0.0.0",
    "emojis": {
        "robot": "\U0001F916",
        "snake": "\U0001F40D",
        "alien": "\U0001F47D",
        "gecko": "\U0001F98E",
        "clown": "\U0001F921",
        "shark": "\U0001F988"
    },
    "delay": DELAY,
    "delta": timedelta(seconds=DELAY)
}

bot = Bot(token=env["TELEGRAM_BOT_TOKEN"])
dp = Dispatcher(bot)

__all__ = ["dp", "bot", "config"]