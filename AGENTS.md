# Copilot Instructions for AOCC FastAPI Project

## Architecture Overview

This is a **FastAPI-based microservice** designed for Azure deployment with comprehensive error handling, OpenTelemetry tracing, and connection pooling. The codebase follows a layered architecture:

- **Clients** (`src/clients/`): Async HTTP/AI clients with connection pooling (GPT, aiohttp, Cosmos DB)
- **Routers** (`src/routers/`): Endpoint handlers that orchestrate business logic
- **Handlers** (`src/handlers/`): Reusable task-specific logic decorated with `@timed`
- **Pipelines** (`src/pipelines/`): Orchestrated multi-step workflows that combine multiple handlers, services, or clients into a single cohesive process.
- **Core** (`core/`): Cross-cutting concerns (config, logging, middleware, exception handling)

### Lifespan Management Pattern

All clients use **initialize/close lifecycle** managed in `main.py` lifespan context:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize clients with connection pooling
    gpt_client = GptClient()
    await gpt_client.initialize()
    app.state.gpt_client = gpt_client
    
    yield
    
    await app.state.gpt_client.close()
```

Access clients via `request.app.state.{client_name}` in endpoints.

## Critical Conventions

### Error Handling: Two-Tier System

1. **AbortException**: Stop request immediately, return error response
   - Use for: Invalid input, authentication failure, critical external API errors
   - Example: `raise AbortException(status=400, message="Invalid input", message_detail="...")`

2. **WarningException**: Log error, return fallback, **continue processing**
   - Use for: Non-critical API timeouts, optional enrichment failures
   - Example: `raise WarningException(message="...", default_result="fallback", task_name="...")`
   - Automatically caught by `@timed` decorator

### Logging & Monitoring

- **Request logging** is automatic via `RequestLoggingMiddleware`
- All tracked endpoints defined in `PATH_TO_CONTAINER` dict (maps routes → Cosmos DB containers)
- Use `set_extract_log(dict)` to add structured metadata to request logs
- Every handler function MUST use `@timed(task_name="...")` for OpenTelemetry spans

### Configuration Management

- **Environment-specific config** loaded via `core.config` (import FIRST in main.py)
- Local dev: Reads `.env.{APP_ENV}` from network share (`//TP-TABLEAU-V05/...`)
- Azure: Uses environment variables set by deployment
- Detect environment: `IS_CLOUD = bool(os.getenv("SCM_DO_BUILD_DURING_DEPLOYMENT"))`

### OpenTelemetry Tracing

- **Local**: Console output via `ConsoleSpanExporter` (commented by default)
- **Azure**: Application Insights via `configure_azure_monitor(connection_string=...)`
- Always instrument FastAPI: `FastAPIInstrumentor.instrument_app(app)` (regardless of environment)

## Development Workflows

### Running Locally
```bash
cd api_structure
python main.py  # Starts uvicorn on localhost:8000 with reload
```

### Adding New Endpoints

1. Create handler in `src/handlers/` with `@timed` decorator
2. Create router in `src/routers/` that accesses `request.app.state.{client}`
3. Register endpoint in `main.py`:
   ```python
   @app.post("/v1/your_endpoint")
   async def v1_your_endpoint(input: YourModel, request: Request, response: Response):
       result = await your_router_function(request)
       return result
   ```
4. Add route to `PATH_TO_CONTAINER` if logging to Cosmos DB needed

### Adding New Clients

1. Create client class in `src/clients/` with:
   - `async def initialize()` - setup connection pooling
   - `async def close()` - cleanup resources
   - Validate credentials in `__init__`
2. Register in `main.py` lifespan:
   ```python
   client = YourClient()
   await client.initialize()
   app.state.your_client = client
   ```
3. Add cleanup in lifespan yield block

### Class-Based Endpoint Pattern

Preferred for complex logic - see `TestGptEndpoint` in `src/routers/use_gpt.py`:
```python
class YourEndpoint:
    def __init__(self, client1, client2):
        self.client1 = client1
        self.client2 = client2
    
    @timed(task_name="step1")
    async def _step1(self):
        # Each step wrapped separately
        ...
    
    @timed(task_name="run")
    async def run(self):
        result1 = await self._step1()
        set_extract_log({"metadata": ...})
        return final_result
```

## Project-Specific Notes

### Key Files to Modify When Adapting Template

- `core/config.py`: Update `GITLAB_PROJ_NAME` to your project name
- `core/logger.py`: Change `VER` version string and `case_id` field name logic
- `core/middleware.py`: Update `PATH_TO_CONTAINER` mapping for your endpoints
- `main.py`: Customize Application Insights connection string env var name

### Git Workflow

- Use Conventional Commits format: `<type>(<scope>): <subject>`
  - **Types:** feat, fix, docs, style, refactor, perf, test, chore, revert  
  - **Example:** `feat(api): add GPT endpoint`

### Background Scheduler (Optional)

Uncommented APScheduler setup in `main.py` allows periodic tasks:
```python
scheduler.add_job(
    your_function,
    trigger=IntervalTrigger(hours=1, timezone=timezone('Asia/Taipei'))
)
```
### Code Validation Before Commit
After completing any new feature or modification, always run Pytest to ensure that all existing and new test cases pass successfully before committing your code.


## Common Pitfalls

1. **Forgetting `@timed` decorator**: All async handlers need it for tracing
2. **Not accessing client via app.state**: Clients are shared singletons, don't create new instances
3. **Using bare `except:`**: Always catch specific exceptions (AbortException, WarningException, or stdlib exceptions)
4. **Modifying request body**: Middleware already handles body parsing - don't read `request.body()` again
5. **Missing PATH_TO_CONTAINER entry**: New endpoints won't log to Cosmos unless added to mapping
6. **Skipping tests**: Always run pytest after code changes to ensure functionality and prevent regressions