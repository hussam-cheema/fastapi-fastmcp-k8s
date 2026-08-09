from datetime import datetime, timezone
from uuid import uuid4

from .db import reminders_collection


def now():
    return datetime.now(timezone.utc).isoformat()


def serialize(doc):
    if not doc:
        return None

    doc = dict(doc)
    doc["id"] = doc.pop("_id")

    return doc


async def create_reminder(
    title: str,
    description: str = "",
    due_at=None,
):
    timestamp = now()

    reminder = {
        "_id": str(uuid4()),
        "title": title,
        "description": description,
        "due_at": due_at.isoformat() if hasattr(due_at, "isoformat") else due_at,
        "completed": False,
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    await reminders_collection.insert_one(reminder)

    return serialize(reminder)


async def list_reminders():
    cursor = reminders_collection.find({}).sort(
        [
            ("completed", 1),
            ("created_at", -1),
        ]
    )

    documents = await cursor.to_list(length=200)

    return [serialize(doc) for doc in documents]


async def get_reminder(reminder_id: str):
    document = await reminders_collection.find_one(
        {"_id": reminder_id}
    )

    return serialize(document)


async def update_reminder(reminder_id: str, updates: dict):
    if not updates:
        return await get_reminder(reminder_id)

    if "due_at" in updates:
        due = updates["due_at"]

        if hasattr(due, "isoformat"):
            updates["due_at"] = due.isoformat()

    updates["updated_at"] = now()

    result = await reminders_collection.update_one(
        {"_id": reminder_id},
        {"$set": updates},
    )

    if result.matched_count == 0:
        return None

    return await get_reminder(reminder_id)


async def delete_reminder(reminder_id: str):
    result = await reminders_collection.delete_one(
        {"_id": reminder_id}
    )

    return result.deleted_count == 1
