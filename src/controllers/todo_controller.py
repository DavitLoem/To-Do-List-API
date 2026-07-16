from fastapi import APIRouter, Body, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime
from src.model.todo_model import TodoItem, TodoUpdate
from src.services.todo_services import (
    create_todo, get_todos, get_todo_by_id, update_todo,
    set_status, set_favorite, set_archived,
    soft_delete_todo, restore_todo, get_trash,
    permanently_delete_todo, empty_trash, get_dashboard_summary
)
from src.services.auth_services import get_current_user

todo_router = APIRouter(prefix="/api/tasks", tags=["Todo List"])


def _serialize(todo: dict) -> dict:
    todo = dict(todo)
    todo["id"] = str(todo.pop("_id"))
    return todo


@todo_router.get("/dashboard", summary="Dashboard summary")
async def dashboard(user_id: str = Depends(get_current_user)):
    return await get_dashboard_summary(user_id)


@todo_router.post("/", summary="Create a new task")
async def add_todo(body: TodoItem, user_id: str = Depends(get_current_user)):
    result = await create_todo(user_id, body.model_dump())
    return {"message": "Task created", "id": str(result.inserted_id)}


@todo_router.get("/", summary="List tasks with optional filter/search/sort")
async def list_todos(
    user_id: str = Depends(get_current_user),
    status: Optional[str] = Query(None, description="pending or completed"),
    priority: Optional[str] = Query(None, description="low, medium, high, urgent"),
    category_id: Optional[str] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    is_archived: bool = Query(True),
    search: Optional[str] = Query(None, description="Search in title/description"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    sort_by: str = Query("created_at", description="created_at, updated_at, due_date, title, priority"),
    sort_order: int = Query(-1, description="1 for ascending, -1 for descending"),
):
    todos = await get_todos(
        user_id, status=status, priority=priority, category_id=category_id,
        is_favorite=is_favorite, is_archived=is_archived, search=search,
        date_from=date_from, date_to=date_to, sort_by=sort_by, sort_order=sort_order
    )
    return [_serialize(t) for t in todos]


@todo_router.get("/trash", summary="Get tasks in trash")
async def list_trash(user_id: str = Depends(get_current_user)):
    todos = await get_trash(user_id)
    return [_serialize(t) for t in todos]


@todo_router.delete("/trash", summary="Empty trash (permanently delete all)")
async def clear_trash(user_id: str = Depends(get_current_user)):
    result = await empty_trash(user_id)
    return {"message": f"{result.deleted_count} task(s) permanently deleted"}


@todo_router.get("/{todo_id}", summary="Get a single task")
async def get_todo(todo_id: str, user_id: str = Depends(get_current_user)):
    todo = await get_todo_by_id(todo_id, user_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Task not found")
    return _serialize(todo)


@todo_router.put("/{todo_id}", summary="Update a task")
async def edit_todo(todo_id: str, body: TodoUpdate, user_id: str = Depends(get_current_user)):
    result = await update_todo(todo_id, user_id, body.model_dump(exclude_unset=True))
    if result is None or result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task updated"}


@todo_router.delete("/{todo_id}", summary="Move a task to trash")
async def remove_todo(todo_id: str, user_id: str = Depends(get_current_user)):
    result = await soft_delete_todo(todo_id, user_id)
    if result is None or result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task moved to trash"}


@todo_router.patch("/{todo_id}/complete", summary="Mark task as completed")
async def complete_todo(todo_id: str, user_id: str = Depends(get_current_user)):
    result = await set_status(todo_id, user_id, "completed")
    if result is None or result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task marked as completed"}


@todo_router.patch("/{todo_id}/pending", summary="Mark task as pending")
async def pending_todo(todo_id: str, user_id: str = Depends(get_current_user)):
    result = await set_status(todo_id, user_id, "pending")
    if result is None or result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task marked as pending"}


@todo_router.patch("/{todo_id}/favorite", summary="Mark task as favorite")
async def favorite_todo(todo_id: str, user_id: str = Depends(get_current_user)):
    result = await set_favorite(todo_id, user_id, True)
    if result is None or result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task added to favorites"}


@todo_router.patch("/{todo_id}/unfavorite", summary="Remove task from favorites")
async def unfavorite_todo(todo_id: str, user_id: str = Depends(get_current_user)):
    result = await set_favorite(todo_id, user_id, False)
    if result is None or result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task removed from favorites"}


@todo_router.patch("/{todo_id}/archive", summary="Archive a task")
async def archive_todo(todo_id: str, user_id: str = Depends(get_current_user)):
    result = await set_archived(todo_id, user_id, True)
    if result is None or result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task archived"}


@todo_router.patch("/{todo_id}/unarchive", summary="Restore a task from archive")
async def unarchive_todo(todo_id: str, user_id: str = Depends(get_current_user)):
    result = await set_archived(todo_id, user_id, False)
    if result is None or result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task restored from archive"}


@todo_router.patch("/{todo_id}/restore", summary="Restore a task from trash")
async def restore_from_trash(todo_id: str, user_id: str = Depends(get_current_user)):
    result = await restore_todo(todo_id, user_id)
    if result is None or result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task restored from trash"}


@todo_router.delete("/{todo_id}/permanent", summary="Permanently delete a task from trash")
async def delete_forever(todo_id: str, user_id: str = Depends(get_current_user)):
    result = await permanently_delete_todo(todo_id, user_id)
    if result is None or result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found in trash")
    return {"message": "Task permanently deleted"}