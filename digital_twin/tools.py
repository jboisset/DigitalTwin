"""In-process MCP tools exposed to the Digital Twin agent.

The agent reads and writes the objectives database through these tools. The
naming convention `mcp__digital_twin__<tool>` is what the SDK exposes to the
model, and the same names must be passed in `allowed_tools` (see agent.py).
"""

from datetime import date
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from . import db
from .models import CATEGORIES, HORIZONS, PRIORITIES, STATUSES


def _format_objective(obj: Any) -> str:
    return (
        f"#{obj.id} [{obj.priority}|{obj.category}|{obj.status}] {obj.title}"
        f" (horizon={obj.horizon}, deadline={obj.deadline}, kpi={obj.kpi})"
        + (f"\n    {obj.description}" if obj.description else "")
    )


@tool(
    "list_objectives",
    "List the user's objectives. Optional filters: category (pro|perso), "
    "status (active|paused|done|dropped), priority (P0|P1|P2).",
    {"category": str, "status": str, "priority": str},
)
async def list_objectives_tool(args: dict[str, Any]) -> dict[str, Any]:
    objectives = db.list_objectives(
        category=args.get("category") or None,
        status=args.get("status") or None,
        priority=args.get("priority") or None,
    )
    if not objectives:
        text = "Aucun objectif enregistré."
    else:
        text = "\n".join(_format_objective(o) for o in objectives)
    return {"content": [{"type": "text", "text": text}]}


@tool(
    "upsert_objective",
    "Create or update an objective. Pass `id` to update an existing one, "
    f"omit it to create. category={CATEGORIES}, priority={PRIORITIES}, "
    f"horizon={HORIZONS}, status={STATUSES}. deadline is ISO date YYYY-MM-DD. "
    "Always confirm with the user before calling this tool.",
    {
        "id": int,
        "title": str,
        "description": str,
        "category": str,
        "priority": str,
        "horizon": str,
        "status": str,
        "deadline": str,
        "kpi": str,
    },
)
async def upsert_objective_tool(args: dict[str, Any]) -> dict[str, Any]:
    deadline_str = args.get("deadline")
    deadline = date.fromisoformat(deadline_str) if deadline_str else None
    try:
        obj = db.upsert_objective(
            id=args.get("id"),
            title=args["title"],
            description=args.get("description") or None,
            category=args.get("category", "pro"),
            priority=args.get("priority", "P1"),
            horizon=args.get("horizon", "moyen"),
            status=args.get("status", "active"),
            deadline=deadline,
            kpi=args.get("kpi") or None,
        )
    except (KeyError, ValueError) as e:
        return {"content": [{"type": "text", "text": f"Erreur: {e}"}], "is_error": True}
    return {"content": [{"type": "text", "text": f"OK -> {_format_objective(obj)}"}]}


@tool(
    "delete_objective",
    "Delete an objective by id. Always confirm with the user before calling.",
    {"id": int},
)
async def delete_objective_tool(args: dict[str, Any]) -> dict[str, Any]:
    ok = db.delete_objective(int(args["id"]))
    msg = f"Supprimé #{args['id']}" if ok else f"Objectif #{args['id']} introuvable"
    return {"content": [{"type": "text", "text": msg}], "is_error": not ok}


server = create_sdk_mcp_server(
    name="digital_twin",
    version="0.1.0",
    tools=[list_objectives_tool, upsert_objective_tool, delete_objective_tool],
)

ALLOWED_TOOLS = [
    "mcp__digital_twin__list_objectives",
    "mcp__digital_twin__upsert_objective",
    "mcp__digital_twin__delete_objective",
]
