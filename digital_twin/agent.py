"""Digital Twin agent: Anthropic SDK client + manual tool-use loop.

Each call to `chat()` runs one full turn:
  1. Send the chat history + tools to Claude.
  2. While the model responds with `stop_reason == "tool_use"`, execute the
     requested tools locally (via `digital_twin.tools.execute_tool`), append
     the results, and re-call.
  3. Return the final assistant text once the loop terminates.

System prompt + tools are sent with `cache_control` so the prefix is cached
across turns (becomes effective once the prefix exceeds the model's minimum
cacheable size).
"""

from typing import Any

import anthropic

from .tools import TOOLS, execute_tool

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8192
MAX_TOOL_ITERATIONS = 8

SYSTEM_PROMPT = """Tu es le **Digital Twin** de l'utilisateur — un coach personnel qui l'aide à suivre ses objectifs pro et perso.

Ton rôle :
- L'aider à **clarifier** ses objectifs (méthode SMART : Spécifique, Mesurable, Atteignable, Réaliste, Temporel).
- **Détecter** les conflits de priorités, les objectifs flous, les dispersions vers du non-prioritaire.
- Le **challenger** quand il s'éparpille : ramène toujours la conversation aux objectifs P0/P1 actifs.
- **Maintenir** la base d'objectifs via les outils disponibles (`list_objectives`, `upsert_objective`, `delete_objective`).

Règles strictes :
- Réponds en **français**, sois **direct et concis**. Pose des questions ciblées plutôt que de monologuer.
- Avant toute écriture en base (`upsert_objective`, `delete_objective`), **résume la modification proposée et demande confirmation explicite** dans ta réponse texte. N'appelle l'outil qu'au tour suivant, après le "ok" de l'utilisateur.
- En début de session ou si tu manques de contexte, appelle `list_objectives` pour voir l'état actuel.
- Si l'utilisateur amène un nouveau sujet, vérifie d'abord son alignement avec ses objectifs P0/P1 actifs avant de t'y engager.

Taxonomie :
- Catégories : `pro`, `perso`.
- Priorités : `P0` (critique), `P1` (important), `P2` (secondaire).
- Horizons : `court`, `moyen`, `long`.
- Statuts : `active`, `paused`, `done`, `dropped`.
"""

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _extract_text(content: list[Any]) -> str:
    return "\n".join(b.text for b in content if b.type == "text").strip()


def chat(history: list[dict[str, str]]) -> str:
    """Run one chat turn given the full UI-side history; return assistant text."""
    client = _get_client()
    messages: list[dict[str, Any]] = [
        {"role": m["role"], "content": m["content"]} for m in history
    ]

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            return _extract_text(response.content) or "(aucune réponse)"

        messages.append({"role": "assistant", "content": response.content})
        tool_results: list[dict[str, Any]] = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            text, is_error = execute_tool(block.name, block.input)
            result_block: dict[str, Any] = {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": text,
            }
            if is_error:
                result_block["is_error"] = True
            tool_results.append(result_block)
        messages.append({"role": "user", "content": tool_results})

    return "(le Twin a dépassé le nombre maximum d'itérations d'outils)"


__all__ = ["chat", "SYSTEM_PROMPT", "MODEL"]
