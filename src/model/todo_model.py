from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class PriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class StatusEnum(str, Enum):
    pending = "pending"
    completed = "completed"


class TodoItem(BaseModel):
    title: str = Field(..., min_length=1, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: StatusEnum = Field(default=StatusEnum.pending, description="Task status: pending or completed")
    priority: PriorityEnum = Field(default=PriorityEnum.medium, description="Task priority")
    category_id: Optional[str] = Field(None, description="Category this task belongs to")
    due_date: Optional[datetime] = Field(None, description="Due date for the task")


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: Optional[StatusEnum] = Field(None, description="Task status: pending or completed")
    priority: Optional[PriorityEnum] = Field(None, description="Task priority")
    category_id: Optional[str] = Field(None, description="Category this task belongs to")
    due_date: Optional[datetime] = Field(None, description="Due date for the task")


class CategoryItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Category name", examples=["School Project"])
    color: Optional[str] = Field(None, description="Hex color for the category badge", examples=["#2f6f5e"])


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None)