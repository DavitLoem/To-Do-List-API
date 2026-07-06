from config.mongo import collections
from bson.objectid import ObjectId
from datetime import datetime

category_col = collections("categories")


def _oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        return None


async def create_category(user_id: str, data: dict):
    data.update({"user_id": user_id, "created_at": datetime.utcnow()})
    return await category_col.insert_one(data)


async def get_categories(user_id: str):
    cursor = category_col.find({"user_id": user_id}).sort("name", 1)
    return await cursor.to_list(length=200)


async def get_category_by_id(category_id: str, user_id: str):
    oid = _oid(category_id)
    if not oid:
        return None
    return await category_col.find_one({"_id": oid, "user_id": user_id})


async def update_category(category_id: str, user_id: str, data: dict):
    oid = _oid(category_id)
    if not oid:
        return None
    return await category_col.update_one(
        {"_id": oid, "user_id": user_id},
        {"$set": data}
    )


async def delete_category(category_id: str, user_id: str):
    oid = _oid(category_id)
    if not oid:
        return None
    return await category_col.delete_one({"_id": oid, "user_id": user_id})