from datetime import datetime
from pydantic import BaseModel, Field


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    due_at: datetime | None = None


class ReminderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_at: datetime | None = None
    completed: bool | None = None


class ReminderOut(BaseModel):
    id: str
    title: str
    description: str
    due_at: datetime | None
    completed: bool
    created_at: datetime
    updated_at: datetime
