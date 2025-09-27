import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import ADMINS, BOT_TOKEN
from handlers import add_task, feedback, start, tasks
from middlewares.anti_spam import CooldownMiddleware
from models.db import init_db

BOT_MODE = os.getenv("BOT_MODE", "polling")  # 'polling' по умолчанию
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # нужен для webhook режима


async def main():
    await init_db()  # Создание таблиц
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # FSM-хранилище
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    antispam = CooldownMiddleware(
        cooldown=1.0,
        whitelist={int(x) for x in (ADMINS or []) if str(x).strip().isdigit()},
    )

    dp.message.middleware(antispam)
    dp.callback_query.middleware(antispam)

    # Подключаем все роутеры (по модулям)
    dp.include_routers(
        start.router,  # Приветствие, старт, сбор контактов
        tasks.router,
        add_task.router,
        feedback.router,  # Обратная связь от пользователей
    )

    if BOT_MODE == "polling":
        print("Task Bot started in POLLING mode!")
        await dp.start_polling(bot)
    else:
        # --- Webhook mode ---
        print("Task Bot started in WEBHOOK mode!")
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler
        from aiohttp import web

        app = web.Application()

        # Регистрируем обработчик webhook
        SimpleRequestHandler(dp, bot).register(app, path="/")

        async def on_startup(app):
            if not WEBHOOK_URL:
                raise RuntimeError("WEBHOOK_URL not set for webhook mode!")
            await bot.set_webhook(WEBHOOK_URL)
            print(f"Webhook set to {WEBHOOK_URL}")

        app.on_startup.append(on_startup)

        port = int(os.environ.get("PORT", 8080))
        web.run_app(app, port=port)


if __name__ == "__main__":
    asyncio.run(main())
