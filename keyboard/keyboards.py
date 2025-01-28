from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from typing import List, Tuple

# Главное меню (пример)
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Начать обработку")]
    ],
    resize_keyboard=True
)

# Меню админа
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Добавить пользователя"),
            KeyboardButton(text="Список пользователей")
        ],
        [
            KeyboardButton(text="Выйти из админ-режима")
        ]
    ],
    resize_keyboard=True
)


def build_user_carousel(users: List[dict], index: int) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Отображаем ОДНОГО пользователя (users[index]) + inline-клавиатуру «◀ Удалить ▶».
    - Если index=0, кнопка «◀» не показывается.
    - Если index=len(users)-1, кнопка «▶» не показывается.
    Возвращаем (text, inline_kb).
    """

    n = len(users)
    if n == 0:
        # Вообще нет пользователей
        return ("Нет ни одного пользователя.", InlineKeyboardMarkup(inline_keyboard=[]))

    # Безопасно сдвигаем index в диапазон [0..n-1]
    if index < 0:
        index = 0
    elif index >= n:
        index = n - 1

    user = users[index]
    user_id = user["user_id"]
    username = user.get("username") or "NoName"
    is_admin = user.get("is_admin", False)
    is_allowed = user.get("is_allowed", False)

    # Формируем текст:
    # Пример:
    # Юзер 1/5
    # Ник: ...
    # ID: ...
    # [admin, allowed]
    lines = [
        f"Юзер {index+1}/{n}",
        f"Ник: {username}",
        f"ID: {user_id}"
    ]
    flags = []
    if is_admin:
        flags.append("admin")
    if is_allowed:
        flags.append("allowed")
    if flags:
        lines.append("Статусы: " + ", ".join(flags))

    text_result = "\n".join(lines)

    # Формируем inline-кнопки: «◀», «Удалить», «▶»
    # Левая кнопка (если есть куда листать)
    left_btn = None
    if index > 0:
        left_btn = InlineKeyboardButton(
            text="◀",
            callback_data=f"prev_user:{index}"
        )

    # Кнопка «Удалить»
    delete_btn = InlineKeyboardButton(
        text="Удалить",
        callback_data=f"delete_user:{user_id}:{index}"
    )

    # Правая кнопка (если есть куда листать)
    right_btn = None
    if index < n - 1:
        right_btn = InlineKeyboardButton(
            text="▶",
            callback_data=f"next_user:{index}"
        )

    # Собираем ряд
    row = []
    if left_btn:
        row.append(left_btn)
    row.append(delete_btn)
    if right_btn:
        row.append(right_btn)

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[row])
    return text_result, inline_kb
