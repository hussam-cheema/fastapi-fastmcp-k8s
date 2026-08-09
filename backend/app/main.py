import socket

from fastapi import FastAPI, HTTPException

from .db import mongo_client
from .models import (
    ReminderCreate,
    ReminderUpdate,
    ReminderOut,
)
from . import repository
from .mcp_server import mcp_app


app = FastAPI(
    title="Reminders API",
    version="1.0.0",
    lifespan=mcp_app.lifespan,
)


# -------------------------
# Health
# -------------------------

@app.get("/health/live")
async def liveness():
    return {
        "status": "alive",
        "pod": socket.gethostname(),
    }


@app.get("/health/ready")
async def readiness():
    await mongo_client.admin.command("ping")

    return {
        "status": "ready",
        "pod": socket.gethostname(),
    }


# -------------------------
# CRUD API
# -------------------------

@app.get(
    "/api/reminders",
    response_model=list[ReminderOut],
)
async def get_reminders():
    return await repository.list_reminders()


@app.get(
    "/api/reminders/{reminder_id}",
    response_model=ReminderOut,
)
async def get_reminder(reminder_id: str):

    reminder = await repository.get_reminder(reminder_id)

    if not reminder:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found",
        )

    return reminder


@app.post(
    "/api/reminders",
    response_model=ReminderOut,
    status_code=201,
)
async def create_reminder(reminder: ReminderCreate):

    return await repository.create_reminder(
        title=reminder.title,
        description=reminder.description,
        due_at=reminder.due_at,
    )


@app.put(
    "/api/reminders/{reminder_id}",
    response_model=ReminderOut,
)
async def update_reminder(
    reminder_id: str,
    reminder: ReminderUpdate,
):

    updates = reminder.model_dump(
        exclude_unset=True
    )

    result = await repository.update_reminder(
        reminder_id,
        updates,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found",
        )

    return result


@app.delete("/api/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str):

    deleted = await repository.delete_reminder(
        reminder_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found",
        )

    return {
        "deleted": True,
        "id": reminder_id,
    }


# -------------------------
# MCP
# -------------------------

app.mount(
    "/mcp",
    mcp_app,
)
