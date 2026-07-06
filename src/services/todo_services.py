from config.mongo import collections
from bson.objectid import ObjectId
from datetime import datetime, timedelta

todo_col = collections("todos")


def _oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        return None


async def create_todo(user_id: str, data: dict):
    data.update({
        "user_id": user_id,
        "is_favorite": False,
        "is_archived": False,
        "is_deleted": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    return await todo_col.insert_one(data)


async def get_todo_by_id(todo_id: str, user_id: str):
    oid = _oid(todo_id)
    if not oid:
        return None
    return await todo_col.find_one({"_id": oid, "user_id": user_id})


async def get_todos(
    user_id: str,
    status: str = None,
    priority: str = None,
    category_id: str = None,
    is_favorite: bool = None,
    is_archived: bool = False,
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
        date_query = {}
        if date_from:
            date_query["$gte"] = date_from
        if date_to:
            date_query["$lte"] = date_to
        query["due_date"] = date_query

    allowed_sort_fields = {"created_at", "updated_at", "due_date", "title", "priority"}
    if sort_by not in allowed_sort_fields:
        sort_by = "created_at"

    cursor = todo_col.find(query).sort(sort_by, sort_order)
    return await cursor.to_list(length=500)


async def update_todo(todo_id: str, user_id: str, data: dict):
    oid = _oid(todo_id)
    if not oid:
        return None
    data["updated_at"] = datetime.utcnow()
    return await todo_col.update_one(
        {"_id": oid, "user_id": user_id},
        {"$set": data}
    )


async def delete_todo(todo_id: str):
    oid = _oid(todo_id)
    if not oid:
        return None
    return await todo_col.delete_one({"_id": oid})


async def set_status(todo_id: str, user_id: str, status: str):
    return await update_todo(todo_id, user_id, {"status": status})


async def set_favorite(todo_id: str, user_id: str, is_favorite: bool):
    return await update_todo(todo_id, user_id, {"is_favorite": is_favorite})


async def set_archived(todo_id: str, user_id: str, is_archived: bool):
    return await update_todo(todo_id, user_id, {"is_archived": is_archived})


async def soft_delete_todo(todo_id: str, user_id: str):
    """Moves a task to trash."""
    return await update_todo(todo_id, user_id, {"is_deleted": True, "deleted_at": datetime.utcnow()})


async def restore_todo(todo_id: str, user_id: str):
    """Restores a task out of trash."""
    return await update_todo(todo_id, user_id, {"is_deleted": False, "deleted_at": None})


async def get_trash(user_id: str):
    cursor = todo_col.find({"user_id": user_id, "is_deleted": True}).sort("deleted_at", -1)
    return await cursor.to_list(length=500)


async def permanently_delete_todo(todo_id: str, user_id: str):
    oid = _oid(todo_id)
    if not oid:
        return None
    return await todo_col.delete_one({"_id": oid, "user_id": user_id, "is_deleted": True})


async def empty_trash(user_id: str):
    return await todo_col.delete_many({"user_id": user_id, "is_deleted": True})


async def get_dashboard_summary(user_id: str):
    base_query = {"user_id": user_id, "is_deleted": False, "is_archived": False}

    total = await todo_col.count_documents(base_query)
    completed = await todo_col.count_documents({**base_query, "status": "completed"})
    pending = await todo_col.count_documents({**base_query, "status": "pending"})

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    today_count = await todo_col.count_documents({
        **base_query, "due_date": {"$gte": today_start, "$lt": today_end}
    })
    upcoming_count = await todo_col.count_documents({
        **base_query, "due_date": {"$gt": today_end}, "status": "pending"
    })

    completion_pct = round((completed / total) * 100, 1) if total > 0 else 0.0

    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": pending,
        "today_tasks": today_count,
        "upcoming_tasks": upcoming_count,
        "completion_percentage": completion_pct
    }