import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

# Читаем MONGO_URI из .env (или используем дефолт)
MONGO_URI = os.getenv("MONGO_URI")

# Подключаемся к MongoDB
client = AsyncIOMotorClient(MONGO_URI)
db = client["shinobi_db"]         # ваша БД
users_collection = db["users"]     # коллекция для хранения пользователей


async def init_db():
    """
    Создаёт уникальный индекс по user_id, чтобы один и тот же user_id
    не дублировался.
    """
    await users_collection.create_index("user_id", unique=True)


async def get_or_create_user(user_id: int, username: str) -> dict:
    """
    Возвращает документ (dict) о пользователе по user_id.
    Если пользователя нет — создаём новую запись (is_admin=False, is_allowed=False).
    Также сохраняем username (если есть).
    """
    doc = await users_collection.find_one({"user_id": user_id})
    if doc:
        return doc

    new_doc = {
        "user_id": user_id,
        "username": username,
        "is_admin": False,
        "is_allowed": False
    }
    await users_collection.insert_one(new_doc)
    return new_doc


async def is_user_admin(user_id: int) -> bool:
    """Проверяем, есть ли user_id в БД и установлен ли ему is_admin=True."""
    doc = await users_collection.find_one({"user_id": user_id})
    return bool(doc and doc.get("is_admin"))


async def is_user_allowed(user_id: int) -> bool:
    """Проверяем, есть ли user_id в БД и установлен ли ему is_allowed=True."""
    doc = await users_collection.find_one({"user_id": user_id})
    return bool(doc and doc.get("is_allowed"))


async def set_admin(user_id: int, is_admin: bool):
    """
    Устанавливаем (или снимаем) флаг is_admin пользователю user_id.
    upsert=True -> если записи нет, создаём.
    """
    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"is_admin": is_admin}},
        upsert=True
    )


async def allow_user(user_id: int) -> bool:
    """
    Даёт пользователю (user_id) доступ (is_allowed=True).
    Если записи нет — создаём (is_admin=False, is_allowed=True).
    Возвращает True, если мы обновили / создали запись.
    """
    res = await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"is_allowed": True}},
        upsert=True
    )
    return (res.modified_count > 0 or res.upserted_id is not None)


async def remove_user(user_id: int) -> bool:
    """
    Полностью удаляем запись из БД.
    Возвращает True, если пользователь был удалён.
    """
    res = await users_collection.delete_one({"user_id": user_id})
    return (res.deleted_count > 0)


async def get_all_users() -> list:
    """Возвращает список (list) всех пользователей (dict) из коллекции."""
    cursor = users_collection.find({})
    return await cursor.to_list(None)
