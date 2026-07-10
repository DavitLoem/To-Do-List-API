from config.mongo import collections
from bson.objectid import ObjectId
from datetime import datetime

todo_col = collections("todos")


async def create_todo(user_id: str, data: dict):
    data.update({
        "user_id": user_id,
        "is_favorite": data.get("is_favorite", False),
        "is_archived": data.get("is_archived", True),
        "is_deleted": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })
    return await todo_col.insert_one(data)


async def get_todos(
    user_id: str,
    status: str = None,
    priority: str = None,
    category_id: str = None,
    is_favorite: bool = None,
    is_archived: bool = True,
    search: str = None,
    date_from: datetime = None,
    date_to: datetime = None,
    sort_by: str = "created_at",
    sort_order: int = -1,
):
    query = {"user_id": user_id, "is_deleted": False, "is_archived": is_archived}

    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if category_id:
        query["category_id"] = category_id
    if is_favorite is not None:
        query["is_favorite"] = is_favorite
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]
    if date_from or date_to:
        query["due_date"] = {}
        if date_from:
            query["due_date"]["$gte"] = date_from
        if date_to:
            query["due_date"]["$lte"] = date_to

    cursor = todo_col.find(query).sort(sort_by, sort_order)
    return await cursor.to_list(length=1000)


async def get_todo_by_id(todo_id: str, user_id: str):
    return await todo_col.find_one({
        "_id": ObjectId(todo_id),
        "user_id": user_id,
        "is_deleted": False,
    })


async def update_todo(todo_id: str, user_id: str, data: dict):
    data["updated_at"] = datetime.utcnow()
    return await todo_col.update_one(
        {"_id": ObjectId(todo_id), "user_id": user_id},
        {"$set": data}
    )


async def set_status(todo_id: str, user_id: str, status: str):
    return await todo_col.update_one(
        {"_id": ObjectId(todo_id), "user_id": user_id, "is_deleted": False},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}}
    )


async def set_favorite(todo_id: str, user_id: str, value: bool):
    return await todo_col.update_one(
        {"_id": ObjectId(todo_id), "user_id": user_id, "is_deleted": False},
        {"$set": {"is_favorite": value, "updated_at": datetime.utcnow()}}
    )


async def set_archived(todo_id: str, user_id: str, value: bool):
    return await todo_col.update_one(
        {"_id": ObjectId(todo_id), "user_id": user_id, "is_deleted": False},
        {"$set": {"is_archived": value, "updated_at": datetime.utcnow()}}
    )


async def soft_delete_todo(todo_id: str, user_id: str):
    return await todo_col.update_one(
        {"_id": ObjectId(todo_id), "user_id": user_id, "is_deleted": False},
        {"$set": {
            "is_deleted": True,
            "is_archived": True,
            "updated_at": datetime.utcnow(),
        }}
    )


async def restore_todo(todo_id: str, user_id: str):
    return await todo_col.update_one(
        {"_id": ObjectId(todo_id), "user_id": user_id, "is_deleted": True},
        {"$set": {"is_deleted": False, "updated_at": datetime.utcnow()}}
    )


async def get_trash(user_id: str):
    cursor = todo_col.find({"user_id": user_id, "is_deleted": True})
    return await cursor.to_list(length=1000)


async def permanently_delete_todo(todo_id: str, user_id: str):
    return await todo_col.delete_one({
        "_id": ObjectId(todo_id),
        "user_id": user_id,
        "is_deleted": True,
    })


async def empty_trash(user_id: str):
    return await todo_col.delete_many({"user_id": user_id, "is_deleted": True})


async def get_dashboard_summary(user_id: str):
    pipeline = [
        {"$match": {"user_id": user_id, "is_deleted": False}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
        }}
    ]
    results = await todo_col.aggregate(pipeline).to_list(length=100)
    summary = {"total": 0, "pending": 0, "completed": 0, "favorites": 0}
    for row in results:
        summary["total"] += row["count"]
        if row["_id"] == "completed":
            summary["completed"] = row["count"]
        elif row["_id"] == "pending":
            summary["pending"] = row["count"]

    summary["favorites"] = await todo_col.count_documents({
        "user_id": user_id,
        "is_deleted": False,
        "is_favorite": True,
    })
    return summary
