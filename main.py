import os
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
import handlers


async def set_main_menu(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command='/help', description='Справка по работе бота'),
        BotCommand(command='/submit', description='Загрузить показания на сервер'),
        BotCommand(command='/get', description='Получить показания с сервера'),
    ])

dp = Dispatcher()
dp.include_router(handlers.router)
dp.startup.register(set_main_menu)
dp.run_polling(Bot(os.getenv("BOT_TOKEN")))
