# Copilot Instructions (AOCC FastAPI Project)

- This is a FastAPI microservice deployed on Azure with layered architecture:
  - Clients → Routers → Pipelines → Handlers → core
  - Clients are async singletons stored in `app.state`

- Always initialize/close clients in `main.py` lifespan context.
  Access via `request.app.state.{client}`.

- Use `@timed(task_name="...")` on all handlers for OpenTelemetry tracing.

- Error handling:
  - `AbortException`: Stop request and return error response.
  - `WarningException`: Log warning and return fallback result.

- Use `set_extract_log({})` to enrich logs; all requests are logged via middleware.

- Configuration:
  - Local: `.env.{APP_ENV}` from network share
  - Azure: Environment variables via SCM deployment

- Adding new endpoints:
  1. Create handler with `@timed`
  2. Add router calling it
  3. Register route in `main.py`
  4. Update `PATH_TO_CONTAINER` for Cosmos logging

- Adding new clients:
  - Define `initialize()` / `close()`
  - Register in lifespan
  - Access via `app.state`

- Common pitfalls:
  - Missing `@timed`
  - Recreating clients instead of using `app.state`
  - Using bare `except:`
  - Not updating `PATH_TO_CONTAINER`
