from datetime import timedelta
from os import environ as env

from aiogram import Bot, Dispatcher

DELAY = 120


config = {
    "host": env["HOST"],
    "webhook_path": f"{env['ENDPOINT']}/bot{env['TOKEN']}",
    "webhook_url": f"{env['HOST']}{env['ENDPOINT']}/bot{env['TOKEN']}",
    "token": env['TOKEN'],
    "key": env["KEY"],
    "app_port": int(env.get("PORT", 3001)),
    "app_host":"0.0.0.0",
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