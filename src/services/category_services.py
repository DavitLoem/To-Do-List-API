from config.mongo import collections
from bson.objectid import ObjectId
from datetime import datetime

category_col = collections("categories")


async def create_category(user_id: str, data: dict):
    data.update({
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })
    return await category_col.insert_one(data)


async def get_categories(user_id: str):
    cursor = category_col.find({"user_id": user_id}).sort("created_at", -1)
    return await cursor.to_list(length=1000)


async def get_category_by_id(category_id: str, user_id: str):
    return await category_col.find_one({
        "_id": ObjectId(category_id),
        "user_id": user_id,
    })


async def update_category(category_id: str, user_id: str, data: dict):
    data["updated_at"] = datetime.utcnow()
    return await category_col.update_one(
        {"_id": ObjectId(category_id), "user_id": user_id},
        {"$set": data}
    )


async def delete_category(category_id: str, user_id: str):
    return await category_col.delete_one({
        "_id": ObjectId(category_id),
        "user_id": user_id,
    })
