# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Digital Twin: a personal coach agent built on the **Anthropic Python SDK**. Tracks pro/perso objectives, challenges the user when they drift toward non-priorities, and maintains the objective DB through tool use. UI is Streamlit, persistence is SQLite via SQLModel.

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

Three layers, with the tool-use loop as the bridge that lets the agent read/write user state:

```
   Streamlit UI  (app.py)
        |              \
        |               +--> chat()  --> digital_twin.agent  --> anthropic.Anthropic().messages.create
        |                                      ^   |                          |
        |                                      |   |   (model emits tool_use blocks)
        |                                      |   v                          v
        |                                  execute_tool  <-----  digital_twin.tools (schemas)
        |                                       |
        +-----------------------> digital_twin.db
                                       |
                                       v
                                  data/twin.db (SQLite)
```

Key invariants:

- **`digital_twin/db.py` is the *only* place that talks to SQLite.** Both the UI (`app.py`) and the agent's tool executor (`digital_twin/tools.py`) call its public functions — `list_objectives`, `upsert_objective`, `delete_objective`, `get_objective`. Don't open new sessions outside `db.py`.

- **The agent's behavior is defined by `SYSTEM_PROMPT` in `digital_twin/agent.py`.** Tone, recadrage logic, SMART method, and "always confirm before writing" rule live there. Tweak the prompt before reaching for code.

- **Tool surface is closed.** The model only sees the schemas listed in `tools.TOOLS`, and only those names are dispatched in `tools.execute_tool`. To grant a new capability, add an entry to `TOOLS` (JSON Schema) **and** a matching branch in `execute_tool`. Both steps are required.

- **One `chat()` call = one full agent turn = one tool-use loop.** `agent.chat()` re-calls `messages.create` until `stop_reason != "tool_use"`, capped at `MAX_TOOL_ITERATIONS`. Long-term memory is the SQLite DB; chat history (re-passed each turn) is just UI state.

- **Confirmation before write is enforced by the prompt, not the code.** The `upsert_objective` and `delete_objective` tools execute immediately when the model calls them — the "ask first" rule lives in `SYSTEM_PROMPT`. If the model starts writing without asking, fix the prompt, not `execute_tool`.

- **Prompt caching is on.** `system` is sent as a list with `cache_control: ephemeral`; once the system+tools prefix exceeds the model's minimum cacheable size (2048 tokens for Sonnet 4.6), repeated turns hit the cache. Below that threshold the marker is silently a no-op — expected and harmless.

## Conventions

- **Default model is `claude-sonnet-4-6`** (set in `agent.MODEL`). The system prompt and user-facing strings are tuned for it.
- **End-user strings are French**; identifiers, comments, and docstrings are English.
- **Categorical fields are plain strings**, validated against the constants in `digital_twin/models.py` (`CATEGORIES`, `PRIORITIES`, `HORIZONS`, `STATUSES`). Update those lists in one place when extending the taxonomy — Streamlit dropdowns, the `validate_objective_fields` check, *and* the JSON Schema `enum`s in `tools.TOOLS` all read from them.
- **Never commit `data/*.db`** (gitignored). The `data/` directory itself is kept via `.gitkeep`.

## Adding features

- **New objective field** → add column in `models.Objective`, extend `db.upsert_objective` signature, extend the form in `app.py`, extend the `upsert_objective` JSON Schema in `tools.TOOLS`, and pass it through in the `execute_tool` branch. The DB has no migrations — for non-trivial schema changes, delete `data/twin.db` (early-stage) or introduce Alembic.
- **New agent capability that touches data** → add a JSON Schema entry to `tools.TOOLS`, add a matching branch to `execute_tool`, and document it in `SYSTEM_PROMPT` so the model knows when (and when not) to use it.
- **Specialized subagents (v2)** → planned but not implemented. Will likely be sub-`messages.create` calls from the main Twin with their own scoped tool sets. Deferred until objective-management UX is stable.

## Deployment notes

- App is deployable to **Streamlit Community Cloud** (one-click from a GitHub repo, set `ANTHROPIC_API_KEY` in app secrets), Fly.io, Render, or Cloud Run.
- ⚠️ **Streamlit Community Cloud does not persist `data/twin.db` across redeploys/restarts.** For real usage, deploy to a platform with a persistent volume (Fly.io with a volume) or migrate `db.py` to Postgres (Supabase / Neon).

## Branching

Active development branch: `claude/add-claude-documentation-pTjA6`. Push there.
