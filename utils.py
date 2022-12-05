async def try_sending_message(bot, *args, **kwargs):
    try:
        await bot.send_message(*args, **kwargs)
    except Exception as error:
        print(f"try_sending_message: choked on this exception: {error}")
