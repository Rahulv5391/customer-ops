# Customer Ops — Backend

A customer-service operations console with an AI "Agent Assist" chatbot layered on top: support agents look up customers, manage tickets/queues, get source-cited answers to policy questions from a real knowledge base, and execute actions (issue a credit, update an address, reassign a ticket) directly through chat — every write goes through a propose → confirm step, never landing on the LLM's turn alone.

## Tech stack

FastAPI + SQLAlchemy 2.0 + SQLite, Google ADK/Gemini for LLM orchestration, ChromaDB for RAG, `sqlglot` to gate LLM-generated SQL, `pyjwt`/`bcrypt` for auth. Packaged with [`uv`](https://docs.astral.sh/uv/). Python ≥3.12.

## Setup

```bash
uv sync
cp .env.example .env
```

Edit `.env`:
- `GEMINI_API_KEY` — get one at https://aistudio.google.com/app/apikey. Without one, set `DEMO_MODE=true` instead — the app runs, but every AI Assist chat reply degrades to a clean "temporarily unavailable" message rather than failing startup.
- `JWT_SECRET_KEY` — generate one: `python -c "import secrets; print(secrets.token_urlsafe(48))"`

Seed the database (drops and recreates everything — customers, orders, tickets, agents, escalations, KB documents, mock data sources):

```bash
uv run python -m data.seed_data
```

Run the app:

```bash
uv run uvicorn app.main:app --reload
```

API docs (Swagger UI): http://localhost:8000/docs

## Demo login

Every seeded agent's password is `password123`. Two useful accounts:

| Role | Email |
|---|---|
| Team lead (can approve escalations, manage agents/data-sources) | `jordan.lee@customerops.demo` |
| Support agent | `sam.rivera@customerops.demo` |

`POST /api/v1/auth/login` with `{"email": ..., "password": "password123"}` returns a bearer token; send it as `Authorization: Bearer <token>` on every other request.

## Trying the chat assistant

`POST /api/v1/chat` with `{"message": "...", "session_id": "<a stable id you generate, e.g. crypto.randomUUID()>"}`. Reusing the same `session_id` across calls gives the assistant real multi-turn memory - the backend persists every turn (`app/models/chat_session.py`) and feeds the last 10 back to the LLM as conversation history on each new request. A few things to try:

- `"find customer Daniel Brooks"` — CRM lookup, safely SQL-gated
- `"change her email to new@example.com"` (same `session_id`, right after the lookup above) — proposes a change; confirm it via `POST /api/v1/chat/action/confirm` with the `pending_action.token` from the response
- `"what's our refund policy for orders over 30 days old?"` — RAG answer with a real "Source: ..." citation
- `"how many agents are online right now"` — live queue availability
- `"how many escalations are pending review"` — analytics, deterministic aggregation

## Uploading knowledge base documents

`POST /api/v1/kb/upload` (multipart form: `title`, `category`, `source_updated_at`, `file` — a PDF) is the only way to add KB content; content is chunked, embedded, and immediately searchable through chat. `PATCH /api/v1/kb/{id}/upload` pushes a new revision into an existing document.

## Tests

```bash
uv run pytest
```

Runs fully offline — no Gemini API key or network access needed. The suite deliberately covers only the deterministic logic (SQL-security allow-list, entity resolution, circuit breaker, CRUD, the signed-token propose→confirm flow, analytics aggregation), never LLM classification itself, so it's fast, free, and never rate-limited. Each test run gets its own throwaway SQLite DB and Chroma directory under the OS temp dir — your real `customer_ops.db` and `data/chroma/` are never touched.

## Project structure

```
app/
├── main.py            # FastAPI app, lifespan, CORS, router mounting
├── core/              # config, database, exceptions, sql_security, circuit_breaker
├── models/            # SQLAlchemy ORM models
├── schemas/           # Pydantic request/response contracts
├── crud/              # thin repository layer, one file per entity
├── routers/           # API endpoints
├── services/          # crm_mutations, rag_service, audit_service, auth_service, analytics_service, ...
├── agents/            # LLM orchestration - router_agent + one sub-agent per capability
└── prompts/           # versioned YAML instruction templates
data/
└── seed_data.py       # drop + recreate + seed
tests/                 # pytest suite (see above)
```
