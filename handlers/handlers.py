import os
import random
import asyncio

from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram import Bot

from states import ProcessStates, AdminStates
from db.db import (
    get_or_create_user,
    is_user_admin,
    is_user_allowed,
    set_admin,
    allow_user,
    remove_user,
    get_all_users
)
from keyboard.keyboards import (
    main_menu,
    admin_menu,
    build_user_carousel
)

# Импортируем наши функции из service/unique_photo.py и service/unique_video.py
from service.unique_photo import make_unique_photo
from service.unique_video import make_unique_video

async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    doc = await get_or_create_user(user_id, username)

    if doc["is_admin"] or doc["is_allowed"]:
        await message.answer(
            "Привет! Я бот-уникализатор. Выбери действие:",
            reply_markup=main_menu
        )
    else:
        await message.answer("Вы пока не подтверждены администратором. Ожидайте...")

async def handle_login(message: Message):
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        await message.answer("Формат команды: /login <Пароль>")
        return

    entered_password = parts[1].strip()
    if entered_password == admin_password:
        await set_admin(message.from_user.id, True)
        await message.answer(
            "Пароль верный! Вы теперь администратор.",
            reply_markup=admin_menu
        )
    else:
        await message.answer("Неверный пароль. Доступ запрещён.")
        await message.answer("Вы снова в главном меню.", reply_markup=main_menu)


async def handle_start_processing(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not (await is_user_admin(user_id) or await is_user_allowed(user_id)):
        await message.answer("У вас нет доступа. Ожидайте подтверждения админом.")
        return

    await state.set_state(ProcessStates.waiting_number)
    await message.answer("Введите нужное количество уникальных копий (1–20). Например: 7")

async def handle_number(message: Message, state: FSMContext):
    try:
        copies_count = int(message.text)
        if not (1 <= copies_count <= 20):
            raise ValueError
    except ValueError:
        await message.answer("Ошибка: введите целое число от 1 до 20!")
        return

    await state.update_data(copies_count=copies_count)
    await state.set_state(ProcessStates.waiting_file)
    await message.answer(f"Вы указали {copies_count}. Теперь отправьте фото или видео.")

# ---- САМАЯ ВАЖНАЯ ЧАСТЬ: ПРИНИМАЕМ ФАЙЛ, СКАЧИВАЕМ, ОБРАБАТЫВАЕМ ----
async def handle_file(message: Message, state: FSMContext, bot: Bot):
    """
    Скачивает фото/видео, обрабатывает N раз, отправляет результат.
    """
    current_state = await state.get_state()
    if current_state != ProcessStates.waiting_file:
        return

    data = await state.get_data()
    copies_count = data.get("copies_count", 1)

    # Проверяем, что пользователь отправил
    if message.photo:
        # Берём самую большую (последнюю) миниатюру, она обычно в полном размере
        photo = message.photo[-1]
        file_id = photo.file_id
        file_info = await bot.get_file(file_id)
        # Придумаем локальное имя для скачивания
        input_path = f"temp_input_{message.from_user.id}.jpg"
        await bot.download_file(file_info.file_path, input_path)

        # Теперь обрабатываем N раз
        for i in range(copies_count):
            output_path = f"temp_output_{message.from_user.id}_{i}.jpg"
            # Вызываем нашу функцию из unique_photo.py
            make_unique_photo(input_path, output_path)
            # Затем отправляем обратно пользователю
            # (FSInputFile берёт файл с диска для отправки)
            await message.answer_photo(photo=FSInputFile(output_path))
            # При желании можно подписать: f"Вариант #{i+1}"

        # Удаляем входной файл, если нужно. Аналогично можно удалить выходные
        # import os
        # os.remove(input_path)
        # for i in range(copies_count):
        #     os.remove(f"temp_output_{message.from_user.id}_{i}.jpg")

        await message.answer("Все копии (фото) готовы!", reply_markup=main_menu)
        await state.clear()

    elif message.video:
        video = message.video
        file_id = video.file_id
        file_info = await bot.get_file(file_id)
        input_path = f"temp_input_{message.from_user.id}.mp4"
        await bot.download_file(file_info.file_path, input_path)

        for i in range(copies_count):
            output_path = f"temp_output_{message.from_user.id}_{i}.mp4"
            make_unique_video(input_path, output_path)

            # Отправляем готовое видео
            await message.answer_video(video=FSInputFile(output_path))

        await message.answer("Все копии (видео) готовы!", reply_markup=main_menu)
        await state.clear()

    else:
        # Если прислали не фото и не видео
        await message.answer("Пожалуйста, пришлите фото или видео.")
        return

# ---- Админские команды ----

async def handle_admin_menu(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_user_admin(user_id):
        await message.answer("У вас нет прав администратора!", reply_markup=main_menu)
        return

    match message.text:
        case "Добавить пользователя":
            await message.answer("Отправьте ID пользователя, которому дать доступ (is_allowed=True).")
            await state.set_state(AdminStates.waiting_user_id_to_add)

        case "Список пользователей":
            users = await get_all_users()
            if not users:
                await message.answer("Нет ни одного пользователя.")
            else:
                text, kb = build_user_carousel(users, 0)
                await message.answer(text, reply_markup=kb)

        case "Выйти из админ-режима":
            await message.answer("Вы вышли из меню админа.", reply_markup=main_menu)

        case _:
            await message.answer("Неизвестная команда в админ-меню.")

async def handle_add_user_id(message: Message, state: FSMContext):
    if not await is_user_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора!", reply_markup=main_menu)
        await state.clear()
        return

    try:
        target_id = int(message.text)
    except ValueError:
        await message.answer("Некорректный ID. Попробуйте снова.")
        return

    await allow_user(target_id)
    await message.answer(f"Пользователь {target_id} теперь is_allowed=True.", reply_markup=admin_menu)
    await state.clear()

async def handle_user_carousel_callback(call: CallbackQuery):
    if not await is_user_admin(call.from_user.id):
        await call.answer("У вас нет прав администратора.", show_alert=True)
        return

    data = call.data
    parts = data.split(":")
    users = await get_all_users()

    if not users:
        await call.message.edit_text("Нет ни одного пользователя.")
        await call.message.edit_reply_markup(reply_markup=None)
        return

    cmd = parts[0]
    if cmd in ("prev_user", "next_user"):
        old_index = int(parts[1])
        new_index = old_index - 1 if cmd == "prev_user" else old_index + 1

        text, kb = build_user_carousel(users, new_index)
        await call.message.edit_text(text, reply_markup=kb)

    elif cmd == "delete_user":
        user_id_str = parts[1]
        old_index_str = parts[2]
        user_id_int = int(user_id_str)
        old_index = int(old_index_str)

        success = await remove_user(user_id_int)
        if success:
            await call.answer(f"Пользователь {user_id_int} удалён.")
        else:
            await call.answer(f"Пользователь {user_id_int} не найден.", show_alert=True)

        updated_users = await get_all_users()
        if not updated_users:
            await call.message.edit_text("Нет ни одного пользователя.")
            await call.message.edit_reply_markup(reply_markup=None)
        else:
            if old_index >= len(updated_users):
                old_index = len(updated_users) - 1
            text, kb = build_user_carousel(updated_users, old_index)
            await call.message.edit_text(text, reply_markup=kb)
    else:
        await call.answer("Неизвестная команда.", show_alert=True)
