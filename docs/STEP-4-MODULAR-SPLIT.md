# Step 4: Modular Split + Backboard SDK Migration

This document is a self-contained brief for a fresh agent. You are picking up a project that has already had three feature commits land on `master`. Do **not** consult this conversation's history — everything you need is here.

## Context (one paragraph)

Biome is a personal AI strength coach. Backend is a single-file FastAPI app at `backend/main.py` (~935 lines). The Python project uses **`uv`** for dependency management — never use `pip`. Frontend is React + Vite + TypeScript. The app integrates with **Backboard** (`https://docs.backboard.io/`) for AI chat with tool-calling and per-user assistants. There is no Backboard API key in this environment — you will write code against the SDK / docs and verify static checks. The user will exercise it later with a real key.

Authoritative sources:
- Backboard docs: https://docs.backboard.io/
- Cookbook: https://github.com/Backboard-io/backboard_io_cookbook (canonical patterns and recipe code)
- Project plan: `docs/PLAN.MD`
- Hackathon brief: `AGENTS.md` (mentions the Backboard Spring 2026 challenge)

## Goal

Two changes, two commits, one session:

1. **Commit A — modular split.** Refactor `backend/main.py` into 6 files. Pure refactor, **zero behavior change**, no new deps.
2. **Commit B — Backboard SDK migration.** Replace the hand-rolled `BackboardClient` (raw httpx) with the official **`backboard-sdk`** package. Convert affected handlers to `async`. Drop the direct `httpx` dependency.

Two commits so a future bisect can tell which change caused any regression.

## Pre-flight

Run these and confirm before touching code:

```bash
git -C /home/patrickpassos/GitHub/work/biome-nv status                 # must be clean
git -C /home/patrickpassos/GitHub/work/biome-nv log --oneline -6       # confirm Steps 1-3 are landed
ls /home/patrickpassos/GitHub/work/biome-nv/backend                    # must contain main.py, pyproject.toml, biome.db
```

If the working tree is dirty, **stop** and ask the user whether their unstaged changes should be preserved or stashed. Do not commit on top of someone else's work-in-progress.

---

## Commit A — Modular Split

### Target file layout

```
backend/
  main.py        # FastAPI app, lifespan, CORS, mounts router (~50 lines)
  db.py          # DB class + schema + migrations + seed + load_user_goals
  backboard.py   # BackboardClient + assistant lifecycle + CHAT_TOOLS + system prompts
  routes.py      # All routes via APIRouter; metric helpers; dispatch_tool
  schemas.py     # Pydantic models
  deps.py        # require_user_id
```

This is the **lighter** of the two layouts I considered. We are intentionally **not** creating a `routes/` directory or a separate `metrics.py`. YAGNI — when `routes.py` crosses ~600 lines, future-you can split it. Don't pre-build for a 50-route app.

### Symbol-to-file mapping (read carefully — order matters)

| Current symbol in `main.py` | Destination file | Notes |
|---|---|---|
| `import os, csv, io, json, uuid, uvicorn` | distributed | each module imports what it actually uses |
| `from fastapi import ...` | `main.py` (FastAPI), `routes.py` (APIRouter, Depends, Header, HTTPException, UploadFile, File), `deps.py` (Header, HTTPException) | |
| `load_dotenv()` | `main.py` | called once, before anything else imports env |
| `BACKBOARD_API_KEY`, `USE_SQLITE_FALLBACK`, `ORACLE_*` | `db.py` (Oracle vars), `backboard.py` (Backboard key) | each constant lives where it's read |
| `DEFAULT_GOALS_SEED` | `db.py` | used by `seed_default_profile` and `load_user_goals` |
| `EXERCISE_MUSCLE` | `routes.py` | only used by `_volume_metrics` |
| `class DB`, `db = DB()` singleton | `db.py` | move `_load_user_goals` from main onto DB as **`db.load_user_goals(user_id) -> dict`** so both `backboard.py` and `routes.py` can call it without circular imports |
| `class BackboardClient` | `backboard.py` | unchanged for Commit A |
| `bb_client` singleton | `backboard.py` | |
| `USER_ASSISTANTS`, `USER_CHAT_THREADS` | `backboard.py` | module-level state stays |
| `CHAT_TOOLS` | `backboard.py` | |
| `_chat_system_prompt(goals)`, `_rec_system_prompt()` | `backboard.py` | |
| `_get_user_assistant(user_id)` → `get_user_assistant(user_id)` | `backboard.py` | rename to drop the `_` since it's now imported from another module |
| `_get_recommender_assistant()` → `get_recommender_assistant()` | `backboard.py` | same rename |
| `_parse_tool_args(tc)` → `parse_tool_args(tc)` | `backboard.py` | |
| `lifespan` | `main.py` | calls `db.connect()`, `db.setup()`, `db.seed_default_profile()` |
| `app = FastAPI(...)`, CORS middleware | `main.py` | |
| `ChatMessage`, `ChatRequest`, `LogSet`, `LogExercise`, `LogWorkout`, `ProfileCreate`, `Profile` | `schemas.py` | |
| `_to_int`, `_to_float` | `routes.py` | only used by `/import` |
| `_exercise_metrics`, `_volume_metrics`, `_asymmetry_metrics` | `routes.py` | unchanged |
| `_is_in_workout_type`, `_fallback_recommendation` | `routes.py` | only used by `/recommend` |
| `_profile_row_to_dict` | `routes.py` | only used by profile routes |
| `require_user_id` | `deps.py` | imports `db` from `db.py` to validate the profile exists |
| `_dispatch_tool` | `routes.py` | calls metric helpers locally |
| All `@app.get` / `@app.post` / `@app.delete` decorators | `routes.py` | switch to `@router.<verb>` on a module-level `router = APIRouter()` |
| `if __name__ == "__main__": uvicorn.run(...)` | `main.py` | |

### Import dependency graph (must be acyclic)

```
schemas.py    ← (no internal imports)
db.py         ← (no internal imports)
backboard.py  ← imports db
deps.py       ← imports db
routes.py     ← imports db, backboard, schemas, deps
main.py       ← imports db, routes
```

If you find yourself wanting to import `routes` from `backboard.py` or `db.py`, you've put something in the wrong file. Stop and re-check.

### Step-by-step procedure

1. Create the four new files (`db.py`, `backboard.py`, `schemas.py`, `deps.py`, `routes.py`) with their copied content. Use **plain copy-paste** of existing code — no rewrites, no "while I'm here" cleanups.
2. Slim `main.py` down to: imports, `load_dotenv`, lifespan, `app = FastAPI(lifespan=lifespan)`, CORS middleware, `app.include_router(routes.router)`, `if __name__ == "__main__"` block.
3. Add `router = APIRouter()` at the top of `routes.py` and replace every `@app.<verb>` with `@router.<verb>`. Don't change paths or signatures.
4. Update `lifespan` in `main.py` to use `from db import db` (the singleton).
5. Run the verification block below.
6. Commit with the message: **`refactor: split backend/main.py into modular files`**.

### Pitfalls

- **Module-level state is fine but must live in exactly one file.** `USER_ASSISTANTS` / `USER_CHAT_THREADS` belong in `backboard.py`. The `/profiles DELETE` handler in `routes.py` mutates them — it does so via `from backboard import USER_ASSISTANTS, USER_CHAT_THREADS`. Be careful: importing a dict by name and mutating it is fine; importing and rebinding is not.
- **`_load_user_goals` must move onto the DB class** as `db.load_user_goals(user_id) -> dict` to avoid a `backboard ↔ routes` cycle. Update both callsites.
- **Do not change behavior.** No new logging, no renamed routes, no signature drift. The only renames allowed are dropping leading `_` on the three `backboard.py` helpers that are now public to `routes.py`.
- **Don't simplify the Oracle / SQLite branches in `DB.setup()`.** Leave both paths intact. The user wants Oracle preserved.

---

## Commit B — Backboard SDK Migration

### What changes

Replace the hand-rolled `BackboardClient` in `backboard.py` with the official SDK from PyPI.

```bash
cd /home/patrickpassos/GitHub/work/biome-nv/backend
uv add backboard-sdk
uv remove httpx        # the SDK has its own HTTP client; we no longer need httpx directly
```

**The SDK is async-only.** The cookbook (`https://github.com/Backboard-io/backboard_io_cookbook/blob/main/recipes/hello_backboard.py`) shows `await client.add_message(...)`. Before writing code, read these two recipe files to confirm the SDK shape:

- `recipes/hello_backboard.py`
- `recipes/tool_calling.py`
- `recipes/_common.py`

### Async conversion

Because the SDK is async, every function that calls it must become `async`:

- `get_user_assistant(user_id)` → `async def`
- `get_recommender_assistant()` → `async def`
- `chat_endpoint(...)` → `async def`
- `get_recommendation(...)` → `async def`

Sync DB calls inside async handlers are fine — FastAPI runs them in a threadpool.

### Field-shape changes (dict → object)

The current code does `res.get("status")`. SDK responses are objects with attribute access:

| Old (dict) | New (SDK object) |
|---|---|
| `res.get("status")` | `res.status` |
| `res.get("tool_calls")` | `res.tool_calls` |
| `res.get("run_id")` | `res.run_id` |
| `res.get("content")` | `res.content` |
| `tc.get("function", {}).get("name")` | `tc.function.name` |
| `tc.get("id")` | `tc.id` |
| custom `parse_tool_args(tc)` | **delete it** — use `tc.function.parsed_arguments` (already a dict) |
| `assistant_data["assistant_id"]` (from `list_assistants()`) | `a.assistant_id` (and `a.name`) |

### Error handling

The current code catches `httpx.HTTPError`. The SDK raises its own exception types — read the SDK source / docs to find them. Until you confirm, catch `Exception` only inside the narrowly-scoped Backboard call-and-loop block, with a `print(f"Backboard error: {e}")` for debugging. **Do not** catch `Exception` around the entire handler — keep the `require_user_id` 400/404 paths un-swallowed.

### `bb_client` initialization

```python
# backboard.py — Commit B
import os
from backboard import BackboardClient   # the SDK class

BACKBOARD_API_KEY = os.getenv("BACKBOARD_API_KEY", "")
bb_client: BackboardClient | None = (
    BackboardClient(api_key=BACKBOARD_API_KEY) if BACKBOARD_API_KEY else None
)
```

If the SDK exposes both a sync and async client (e.g. `Client` vs `AsyncClient`), use the **async** one. The cookbook uses the async API exclusively.

### `get_or_create_assistant` pattern

The cookbook's idempotent get-or-create pattern is mandatory. Keep our existing logic (lookup by name → create if missing → cache the id in `USER_ASSISTANTS`). With the SDK it becomes:

```python
async def get_user_assistant(user_id: str) -> str:
    if user_id in USER_ASSISTANTS:
        return USER_ASSISTANTS[user_id]
    name = f"biome-user-{user_id}"
    assistants = await bb_client.list_assistants()
    for a in assistants:
        if a.name == name:
            USER_ASSISTANTS[user_id] = a.assistant_id
            return a.assistant_id
    goals = db.load_user_goals(user_id)
    created = await bb_client.create_assistant(
        name=name,
        system_prompt=_chat_system_prompt(goals),
        tools=CHAT_TOOLS,
    )
    USER_ASSISTANTS[user_id] = created.assistant_id
    return created.assistant_id
```

Same shape for `get_recommender_assistant()`.

### `memory="Auto"` parameter — keep it

The SDK supports `memory="Auto" | "Readonly" | "Off"` on `add_message`. Preserve current behavior:

- `/chat` uses `memory="Auto"` (cross-thread memory persists)
- `/recommend` uses `memory="Off"` (recommendation context stays out of chat memory)

### Step-by-step procedure for Commit B

1. `uv add backboard-sdk` — verify it lands in `pyproject.toml` and `uv.lock` updates.
2. **Read** `recipes/hello_backboard.py` and `recipes/tool_calling.py` from the cookbook to confirm the exact SDK shape before coding.
3. Rewrite `backboard.py`: replace the `BackboardClient` class with the SDK-backed `bb_client` singleton. Convert helpers to `async`.
4. Convert `chat_endpoint` and `get_recommendation` in `routes.py` to `async def` and `await` the helpers. Delete `parse_tool_args` (use `tc.function.parsed_arguments` directly).
5. `uv remove httpx`. Confirm no other module imports `httpx` (`grep -rn 'import httpx\|from httpx' backend/`). If anything still does, **don't remove** — flag and ask.
6. Run the verification block below.
7. Commit with the message: **`feat: migrate Backboard integration to official backboard-sdk`**.

### Pitfalls for Commit B

- **`uv add`, never `pip install`.** The user does not use pip.
- **Do not change route shapes, paths, request bodies, or response bodies.** The frontend has no idea this swap happened.
- **Per-user assistant pattern is mandatory.** Cookbook critical rule #1: shared assistant + `memory="Auto"` leaks data between users. Keep `biome-user-{user_id}`.
- **`BackboardClient` class name collision.** Our existing `backboard.py` defines a class named `BackboardClient`. The SDK exports a class with the same name. **Delete our class entirely** before importing the SDK's — don't try to subclass or shadow.

---

## Verification (run after each commit, before committing)

### Static checks

```bash
cd /home/patrickpassos/GitHub/work/biome-nv/backend
uv run --no-project python -m py_compile main.py db.py backboard.py routes.py schemas.py deps.py
echo "exit=$?"   # must be 0

cd /home/patrickpassos/GitHub/work/biome-nv/frontend
npx tsc --noEmit
echo "exit=$?"   # must be 0
```

### Runtime boot

```bash
cd /home/patrickpassos/GitHub/work/biome-nv/backend
BACKBOARD_API_KEY='' USE_SQLITE_FALLBACK=true uv run --no-project python -c "
import asyncio
from main import app
async def go():
    async with app.router.lifespan_context(app):
        from db import db
        profiles = db.query('SELECT id, name FROM profiles')
        print('profiles:', profiles)
        print('routes:', sorted(getattr(r, 'path', '') for r in app.routes if hasattr(r, 'methods')))
asyncio.run(go())
"
```

Expected: at least one profile (`Patrick`), and the route list includes `/chat`, `/import`, `/metrics/asymmetry`, `/metrics/exercises`, `/metrics/volume`, `/profiles`, `/profiles/{profile_id}`, `/recommend`, `/workouts`.

### End-to-end smoke

```bash
cd /home/patrickpassos/GitHub/work/biome-nv/backend
BACKBOARD_API_KEY='' USE_SQLITE_FALLBACK=true uv run --no-project uvicorn main:app --port 8765 --log-level warning &
SERVER_PID=$!
until curl -sf http://127.0.0.1:8765/profiles >/dev/null 2>&1; do sleep 0.3; done
echo "--- list profiles"
curl -s http://127.0.0.1:8765/profiles | python3 -m json.tool
PATRICK=$(curl -s http://127.0.0.1:8765/profiles | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")
echo "--- expect 400 (no header)"
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/metrics/exercises
echo "--- expect 404 (bogus user)"
curl -s -o /dev/null -w "%{http_code}\n" -H "X-User-ID: not-real" http://127.0.0.1:8765/metrics/exercises
echo "--- expect 200 (Patrick)"
curl -s -o /dev/null -w "%{http_code}\n" -H "X-User-ID: $PATRICK" http://127.0.0.1:8765/metrics/exercises
echo "--- create + delete profile"
NEW=$(curl -s -X POST -H "Content-Type: application/json" -d '{"name":"Smoke","fitness_goal":"Test"}' http://127.0.0.1:8765/profiles | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
curl -s -X DELETE "http://127.0.0.1:8765/profiles/$NEW" | python3 -m json.tool
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null
```

All status codes and outputs must match exactly. If anything differs, **don't commit** — investigate.

### What you cannot verify without an API key

- A real chat round-trip through Backboard
- The SDK's exact response object shape (you're reading docs/source instead)
- Tool-call argument parsing in production

This is fine. The user will exercise these with a real key separately. Your job is to ship code that compiles, type-checks, boots, and behaves correctly on every path that doesn't actually hit Backboard. The `bb_client is None` branch must return `{"reply": "Backboard API is not configured..."}` for `/chat` and the `_fallback_recommendation()` for `/recommend`. Verify both manually if needed.

---

## Things explicitly out of scope

- **Don't add RAG / document upload.** The user explicitly deferred this; they will review and add it later.
- **Don't add a goals-editing UI.** Known gap; out of scope for this session.
- **Don't restore the wiped `biome.db` workout history.** The user knows it's gone; they'll re-import the CSV themselves.
- **Don't migrate to Supabase.** Off the table for now.
- **Don't touch the frontend** beyond what's strictly required (which should be **nothing** — the API surface is unchanged).
- **Don't reorganize the `frontend/` directory.** Frontend is fine as-is.
- **Don't update `AGENTS.md` or `CLAUDE.md`.** Those reference high-level architecture which remains accurate.
- **Don't `git push`.** Local commits only. The user pushes themselves.

---

## Stop conditions — ask the user before proceeding

Stop and ping the user if:

- The working tree is dirty when you start.
- `uv add backboard-sdk` fails (network, package not found, etc.).
- The SDK turns out to be sync-only (contradicts the cookbook).
- You discover a `pip install backboard` that's a different package.
- A verification step fails and you can't immediately see why.
- Removing `httpx` would break something else in the codebase.
- The SDK API shape contradicts the cookbook (e.g., the hello-backboard recipe's `await client.add_message(...)` doesn't actually exist on the package).

---

## Acceptance checklist

- [ ] `backend/main.py` is < 80 lines.
- [ ] `db.py`, `backboard.py`, `routes.py`, `schemas.py`, `deps.py` exist and contain their assigned symbols.
- [ ] No `import httpx` anywhere in `backend/`.
- [ ] `pyproject.toml` lists `backboard-sdk` and **does not** list `httpx`.
- [ ] `uv.lock` is updated and committed alongside `pyproject.toml`.
- [ ] All static + runtime + smoke checks pass.
- [ ] Two commits on `master`, in order: `refactor:` then `feat:`.
- [ ] Working tree clean after final commit.

When everything passes, hand back to the user with: a one-paragraph summary of what landed, the two commit hashes, and a note that they need to set `BACKBOARD_API_KEY` and run the smoke test once with a live key to validate the SDK responses end-to-end.
