from datetime import timedelta
from urllib.parse import urljoin
from aiogram import Bot, Dispatcher
from os import environ as env

DELAY = 120

config = {
    "webhook_host": env["WEBHOOK_HOST"],
    "webhook_url_path": env["WEBHOOK_ENDPOINT"] + env["TELEGRAM_BOT_TOKEN"],
    "webhook_url": urljoin(env["WEBHOOK_HOST"], env["WEBHOOK_URL_PATH"]),
    "key": env["KEY"],
    "port": int(env.get('PORT', 8080)),
    "host":"0.0.0.0",
    "emojis": {
        "church": "\U000026EA",
        "hospital": "\U0001F3E5",
        "wheel": "\U0001F3A1",
        "station": "\U0001F689",
        "bank": "\U0001F3E6",
        "post": "\U0001F3E4"
    },
    "delay": DELAY,
    "delta": timedelta(seconds=DELAY)
}

bot = Bot(token=env["TOKEN"])
dp = Dispatcher(bot)