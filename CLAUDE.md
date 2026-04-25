# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Digital Twin: a personal coach agent built on the **Claude Agent SDK** (Python). Tracks pro/perso objectives, challenges the user when they drift toward non-priorities, and maintains the objective DB through MCP tools. UI is Streamlit, persistence is SQLite via SQLModel.

## Commands

```bash
# Install (editable)
pip install -e ".[dev]"

# Run the app
streamlit run app.py

# Lint / format
ruff check .
ruff format .

# Reset the local DB
rm data/twin.db
```

`ANTHROPIC_API_KEY` must be set in `.env` (loaded by `app.py` via `python-dotenv`) for the chat tab to work. The `Objectifs` tab works without it.

## Architecture

Three layers, with the MCP tools as the bridge that lets the agent read/write user state:

```
   Streamlit UI  (app.py)
        |              \
        |               +--> chat()  --> digital_twin.agent  --> claude_agent_sdk.query
        |                                       |                      |
        |                                       |          (model emits tool calls)
        |                                       v                      v
        +-----------------------> digital_twin.db  <-----  digital_twin.tools (MCP server)
                                       |
                                       v
                                  data/twin.db (SQLite)
```

Key invariants:

- **`digital_twin/db.py` is the *only* place that talks to SQLite.** Both the UI (`app.py`) and the agent's MCP tools (`digital_twin/tools.py`) call its public functions — `list_objectives`, `upsert_objective`, `delete_objective`, `get_objective`. Don't open new sessions outside `db.py`.

- **The agent's behavior is defined by `SYSTEM_PROMPT` in `digital_twin/agent.py`.** Tone, recadrage logic, SMART method, and "always confirm before writing" rule live there. Tweak the prompt before reaching for code.

- **Tool surface is closed.** The agent can only call the names listed in `tools.ALLOWED_TOOLS` (= `mcp__digital_twin__*`). To grant a new capability, define a `@tool` in `tools.py`, add it to the `create_sdk_mcp_server(...)` call, and append its `mcp__digital_twin__<name>` to `ALLOWED_TOOLS`. Both steps are required.

- **Each chat turn is one-shot.** `agent.chat_turn` calls `query()` with the full history serialized into a single prompt; conversational continuity comes from re-passing `st.session_state.messages`. Long-term memory is the SQLite DB, not the chat history. A turn may include multiple internal tool calls (handled inside `async for msg in query(...)`).

- **Streamlit is sync, the SDK is async.** `agent.chat()` wraps `chat_turn` in `asyncio.run()`. Don't call the async version directly from `app.py`.

## Conventions

- **End-user strings are French**; identifiers, comments, and docstrings are English.
- **Categorical fields are plain strings**, validated against the constants in `digital_twin/models.py` (`CATEGORIES`, `PRIORITIES`, `HORIZONS`, `STATUSES`). Update those lists in one place when extending the taxonomy — the Streamlit dropdowns and the `validate_objective_fields` check both read from them.
- **Never commit `data/*.db`** (gitignored). The `data/` directory itself is kept via `.gitkeep`.

## Adding features

- **New objective field** → add column in `models.Objective`, extend `db.upsert_objective` signature, extend the form in `app.py`, extend the `upsert_objective` MCP tool schema in `tools.py`. The DB has no migrations yet — for non-trivial schema changes, delete `data/twin.db` (early-stage) or introduce Alembic.
- **New agent capability that touches data** → add a `@tool` in `tools.py`, register it in the server + `ALLOWED_TOOLS`, and document it in `SYSTEM_PROMPT` so the model knows when to use it.
- **Specialized subagents (v2)** → planned but not implemented. Will be invoked from the main Twin via the SDK's subagent mechanism; design choice deferred until objective-management UX is stable.

## Branching

Active development branch: `claude/add-claude-documentation-pTjA6`. Push there.
