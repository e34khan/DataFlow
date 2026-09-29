# DataFlow

Distributed data processing & reconciliation platform. See project docs (to be added) for full architecture.

## Status

Phase 1 complete: FastAPI + PostgreSQL + Alembic + JWT auth (register/login/me).

## Local development

```bash
cp .env.example .env
docker compose up -d postgres
python -m venv .venv
.venv/Scripts/activate       # source .venv/bin/activate on macOS/Linux
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Tests

```bash
pytest
```

Tests spin up a `dataflow_test` database on the same Postgres instance (created automatically) and reset its schema per test run.

## Full stack via Docker

```bash
docker compose up -d
```
