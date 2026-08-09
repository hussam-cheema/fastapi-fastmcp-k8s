from fastmcp import FastMCP

from . import repository


mcp = FastMCP("Reminders MCP")


@mcp.tool
async def list_reminders():
    """List all reminders."""
    return await repository.list_reminders()


@mcp.tool
async def get_reminder(reminder_id: str):
    """Get one reminder by ID."""
    reminder = await repository.get_reminder(reminder_id)

    if not reminder:
        return {"error": "Reminder not found"}

    return reminder


@mcp.tool
async def create_reminder(
    title: str,
    description: str = "",
    due_at: str | None = None,
):
    """Create a new reminder."""

    return await repository.create_reminder(
        title=title,
        description=description,
        due_at=due_at,
    )


@mcp.tool
async def update_reminder(
    reminder_id: str,
    title: str | None = None,
    description: str | None = None,
    due_at: str | None = None,
    completed: bool | None = None,
    clear_due_at: bool = False,
):
    """Update an existing reminder."""

    updates = {}

    if title is not None:
        updates["title"] = title

    if description is not None:
        updates["description"] = description

    if due_at is not None:
        updates["due_at"] = due_at

    if clear_due_at:
        updates["due_at"] = None

    if completed is not None:
        updates["completed"] = completed

    reminder = await repository.update_reminder(
        reminder_id,
        updates,
    )

    if not reminder:
        return {"error": "Reminder not found"}

    return reminder


@mcp.tool
async def delete_reminder(reminder_id: str):
    """Delete a reminder."""

    deleted = await repository.delete_reminder(reminder_id)

    return {
        "deleted": deleted,
        "id": reminder_id,
    }


# FastMCP v3 style
mcp_app = mcp.http_app(
    path="/",
    stateless_http=True,
)
