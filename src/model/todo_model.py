from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TodoItem(BaseModel):
    title: str = Field(..., min_length=1, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: str = Field(default="pending", description="Task status: pending or completed")
    priority: Optional[str] = Field(None, description="low, medium, high, urgent")
    category_id: Optional[str] = Field(None, description="Associated category id")
    due_date: Optional[datetime] = Field(None, description="Due date for the task")
    is_favorite: bool = Field(default=False, description="Mark as favorite")
    is_archived: bool = Field(default=True, description="Mark as archived")

class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: Optional[str] = Field(None, description="Task status: pending or completed")
    priority: Optional[str] = Field(None, description="low, medium, high, urgent")
    category_id: Optional[str] = Field(None, description="Associated category id")
    due_date: Optional[datetime] = Field(None, description="Due date for the task")
    is_favorite: Optional[bool] = Field(None, description="Mark as favorite")
    is_archived: Optional[bool] = Field(None, description="Mark as archived")

class CategoryItem(BaseModel):
    name: str = Field(..., min_length=1, description="Category name")

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, description="Category name")
