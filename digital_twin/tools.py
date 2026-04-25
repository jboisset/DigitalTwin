"""Tool definitions and local executor for the Digital Twin agent.

Tools are declared as JSON schemas (consumed by the Anthropic API) and executed
locally — `execute_tool` dispatches the call to `digital_twin.db`.
"""

from datetime import date
from typing import Any

from . import db
from .models import CATEGORIES, HORIZONS, PRIORITIES, STATUSES


def _format_objective(obj: Any) -> str:
    return (
        f"#{obj.id} [{obj.priority}|{obj.category}|{obj.status}] {obj.title}"
        f" (horizon={obj.horizon}, deadline={obj.deadline}, kpi={obj.kpi})"
        + (f"\n    {obj.description}" if obj.description else "")
    )


TOOLS: list[dict[str, Any]] = [
    {
        "name": "list_objectives",
        "description": (
            "Lister les objectifs de l'utilisateur. Filtres optionnels : category, "
            "status, priority. Appelle systématiquement cet outil en début de "
            "session pour avoir le contexte avant de conseiller."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": CATEGORIES},
                "status": {"type": "string", "enum": STATUSES},
                "priority": {"type": "string", "enum": PRIORITIES},
            },
        },
    },
    {
        "name": "upsert_objective",
        "description": (
            "Créer ou mettre à jour un objectif. Passer `id` pour mettre à jour, "
            "l'omettre pour créer. TOUJOURS résumer la modification proposée et "
            "demander confirmation explicite à l'utilisateur AVANT d'appeler."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "ID de l'objectif à mettre à jour"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "category": {"type": "string", "enum": CATEGORIES},
                "priority": {"type": "string", "enum": PRIORITIES},
                "horizon": {"type": "string", "enum": HORIZONS},
                "status": {"type": "string", "enum": STATUSES},
                "deadline": {
                    "type": "string",
                    "description": "Date au format ISO YYYY-MM-DD",
                },
                "kpi": {"type": "string", "description": "Mesure de succès"},
            },
            "required": ["title", "category"],
        },
    },
    {
        "name": "delete_objective",
        "description": (
            "Supprimer un objectif par son ID. TOUJOURS demander confirmation "
            "explicite avant d'appeler cet outil."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"id": {"type": "integer"}},
            "required": ["id"],
        },
    },
]


def execute_tool(name: str, args: dict[str, Any]) -> tuple[str, bool]:
    """Run a tool by name and return `(result_text, is_error)`."""
    try:
        if name == "list_objectives":
            objectives = db.list_objectives(
                category=args.get("category"),
                status=args.get("status"),
                priority=args.get("priority"),
            )
            if not objectives:
                return "Aucun objectif enregistré.", False
            return "\n".join(_format_objective(o) for o in objectives), False

        if name == "upsert_objective":
            deadline_str = args.get("deadline")
            deadline = date.fromisoformat(deadline_str) if deadline_str else None
            obj = db.upsert_objective(
                id=args.get("id"),
                title=args["title"],
                description=args.get("description"),
                category=args.get("category", "pro"),
                priority=args.get("priority", "P1"),
                horizon=args.get("horizon", "moyen"),
                status=args.get("status", "active"),
                deadline=deadline,
                kpi=args.get("kpi"),
            )
            return f"OK -> {_format_objective(obj)}", False

        if name == "delete_objective":
            ok = db.delete_objective(int(args["id"]))
            if ok:
                return f"Supprimé #{args['id']}", False
            return f"Objectif #{args['id']} introuvable", True

        return f"Tool inconnu: {name}", True
    except (KeyError, ValueError) as e:
        return f"Erreur: {e}", True


TOOL_NAMES = [t["name"] for t in TOOLS]
