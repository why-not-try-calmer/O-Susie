from datetime import timedelta
from aiogram import Bot, Dispatcher
from os import environ as env

DELAY = 120


config = {
    "webhook_host": env["WEBHOOK_HOST"],
    "webhook_url": f"{env['WEBHOOK_HOST']}/bot{env['TOKEN']}",
    "token": env['TOKEN'],
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

bot = Bot(token=env["TOKEN"])
dp = Dispatcher(bot)

__all__ = ["dp", "bot", "config"]