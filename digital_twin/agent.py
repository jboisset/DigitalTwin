"""Digital Twin agent: thin wrapper around `claude_agent_sdk.query`.

Each call to `chat_turn` is a one-shot agent run that receives the full
conversation history as a single formatted prompt. Long-term memory lives in
SQLite and is read/written by the agent via the MCP tools defined in tools.py.
"""

from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)

from .tools import ALLOWED_TOOLS, server

SYSTEM_PROMPT = """Tu es le **Digital Twin** de l'utilisateur — un coach personnel qui l'aide à suivre ses objectifs pro et perso.

Ton rôle :
- L'aider à **clarifier** ses objectifs (méthode SMART : Spécifique, Mesurable, Atteignable, Réaliste, Temporel).
- **Détecter** les conflits de priorités, les objectifs flous, les dispersions vers du non-prioritaire.
- Le **challenger** quand il s'éparpille : ramène toujours la conversation aux objectifs P0/P1 actifs.
- **Maintenir** la base d'objectifs via les outils MCP disponibles.

Règles :
- Réponds en **français**, sois **direct et concis**. Pose des questions ciblées plutôt que de monologuer.
- Avant toute écriture en base (`upsert_objective`, `delete_objective`), **résume la modification proposée et demande confirmation explicite**.
- En début de session ou si tu manques de contexte, appelle `list_objectives` pour voir l'état actuel.
- Si l'utilisateur amène un nouveau sujet, vérifie d'abord son alignement avec ses objectifs P0/P1 actifs avant de t'y engager.

Catégories : `pro`, `perso`. Priorités : `P0` (critique), `P1` (important), `P2` (secondaire). Horizons : `court`, `moyen`, `long`. Statuts : `active`, `paused`, `done`, `dropped`.
"""


def _format_history(history: list[dict[str, str]]) -> str:
    parts = []
    for m in history:
        role = "USER" if m["role"] == "user" else "ASSISTANT"
        parts.append(f"{role}: {m['content']}")
    return "\n\n".join(parts)


async def chat_turn(history: list[dict[str, str]]) -> str:
    """Run one agent turn given the full chat history; return the assistant text."""
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"digital_twin": server},
        allowed_tools=ALLOWED_TOOLS,
        permission_mode="acceptEdits",
    )

    prompt = _format_history(history)
    text_parts: list[str] = []
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    text_parts.append(block.text)
    return "\n".join(text_parts).strip() or "(aucune réponse)"


def list_tool_names() -> list[str]:
    return list(ALLOWED_TOOLS)


__all__ = ["chat_turn", "list_tool_names", "SYSTEM_PROMPT"]


def _sync_chat_turn(history: list[dict[str, str]]) -> str:
    """Synchronous helper for Streamlit (which is sync)."""
    import asyncio

    return asyncio.run(chat_turn(history))


def chat(history: list[dict[str, str]]) -> str:
    return _sync_chat_turn(history)


# typing helper for callers
HistoryItem = dict[str, Any]
