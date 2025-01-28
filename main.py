import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Импортируем наши хэндлеры
from handlers.handlers import (
    cmd_start,
    handle_login,
    handle_start_processing,
    handle_number,
    handle_file,
    handle_admin_menu,
    handle_add_user_id,
    handle_user_carousel_callback,  # <-- новый коллбэк вместо remove_user_callback
    ProcessStates,
    AdminStates
)

# Импортируем init_db
from db.db import init_db

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация БД
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # /start
    dp.message.register(cmd_start, Command("start"))

    # /login <пароль>
    dp.message.register(handle_login, Command("login"))

    # «Начать обработку»
    dp.message.register(handle_start_processing, lambda m: m.text == "Начать обработку")
    dp.message.register(handle_number, ProcessStates.waiting_number)
    dp.message.register(handle_file, ProcessStates.waiting_file, lambda m: m.content_type in ("photo", "video"))

    # Админ-меню
    dp.message.register(
        handle_admin_menu,
        lambda m: m.text in {"Добавить пользователя", "Список пользователей", "Выйти из админ-режима"}
    )
    dp.message.register(handle_add_user_id, AdminStates.waiting_user_id_to_add)

    # Единый CallbackQuery-хэндлер для карусели пользователей:
    dp.callback_query.register(
        handle_user_carousel_callback,
        lambda c: c.data.startswith("prev_user:")
                  or c.data.startswith("next_user:")
                  or c.data.startswith("delete_user:")
    )

    # Запуск бота
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
