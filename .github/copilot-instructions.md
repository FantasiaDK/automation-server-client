## automation-server-client — Copilot instructions

This file gives concise, actionable guidance for an AI coding agent working in this repository.

Quick start
- Project requires Python >= 3.13 (see `pyproject.toml`).
- Dependencies: `python-dotenv`, `requests`, `pydantic`, `httpx` (dev: `pytest`, `ruff`).
- Typical developer commands (project uses `uv` as documented):
  - Install/sync deps: `uv sync`
  - Run tests: `uv run pytest` or `uv run pytest tests/test_logging.py::test_format_log_record`

Where to look (high-value files)
- `src/automation_server_client/_config.py` — central config singleton (loads `.env` via `load_dotenv()` and requires `ATS_URL`).
- `src/automation_server_client/_server.py` — main entry `AutomationServer.from_environment()` and `workqueue()` accessor.
- `src/automation_server_client/_models.py` — Pydantic models (Session, Process, Workqueue, WorkItem, Credential, Asset).
- `src/automation_server_client/_logging.py` — custom `AutomationServerLoggingHandler` that POSTs logs to the server.
- `tests/` — unit tests show expected behavior and integration points (notably logging tests use `httpx` client and expect 204 responses).

Big picture & data flow
- Configuration is global: `AutomationServerConfig` exposes class attributes (url, token, session, workqueue_override). Always call `AutomationServerConfig.init_from_environment()` (done by `AutomationServer.from_environment()`).
- Authentication: API calls use a Bearer token header built from `AutomationServerConfig.token`.
- Workqueue flow: `AutomationServer.workqueue()` returns a `Workqueue` model. The `Workqueue` implements the iterator protocol: `for item in workqueue:` triggers HTTP GET `/workqueues/{id}/next_item`. The `WorkItem` is a Pydantic model and implements a context manager to manage lifecycle (`__enter__`/`__exit__`).
- Logging flow: the `AutomationServerLoggingHandler.emit()` posts to `/audit-logs` only if `AutomationServerConfig.session` and `url` are set. The handler tracks a `workitem_id` via `start_workitem()`/`end_workitem()` called from `Workqueue.__next__` and `WorkItem` context.

Project-specific conventions
- Pydantic models use `model_config = ConfigDict(extra='ignore')` — unknown API fields are intentionally ignored.
- HTTP calls use `requests` and always call `response.raise_for_status()`; tests and calling code expect exceptions to bubble up for non-2xx.
- Environment variables prefixed `ATS_`:
  - `ATS_URL` (required)
  - `ATS_TOKEN` (optional)
  - `ATS_SESSION`, `ATS_RESOURCE`, `ATS_PROCESS`, `ATS_WORKQUEUE_OVERRIDE` (optional)
- `ATS_WORKQUEUE_OVERRIDE` (if set) takes precedence over process-derived workqueue in `AutomationServer.__init__()`.

Common editing & debugging hints
- To run tests locally set `ATS_URL` env var (tests assert `AutomationServerConfig.init_from_environment()` raises when missing). Example in PowerShell:
  - `$env:ATS_URL='http://localhost:8000'; uv run pytest -q`
- When adding fields returned by the API, update Pydantic models, but keep `extra='ignore'` to remain forward compatible.
- Logging failures are non-fatal: the handler prints errors and returns — keep that behavior unless intentionally changing failure modes.
- Use `WorkItem.update_status()` when changing status; `__exit__` will call `complete()` when status is `"in progress"`.

Examples (copy / paste)
- Initialize from environment and iterate queue:
  - `ats = AutomationServer.from_environment()`
  - `for item in ats.workqueue():
       with item:
           # process item
           item.update({"processed": True})`
- Get credential by name: `cred = Credential.get_credential("my_cred_name")`

Tests & expected API behavior
- Tests located in `tests/` assume a running automation-server (or a test double). Logging tests POST to `/audit-logs` and expect HTTP 204.
- Keep tests deterministic: mock external network calls when adding unit tests, or add integration tests under an `integration/` marker.

Where to change for common tasks
- Add API methods / endpoints: `src/automation_server_client/_models.py`
- Change logging format or fields: `src/automation_server_client/_logging.py` (see `_format_log_record`).
- Change environment parsing or defaults: `src/automation_server_client/_config.py`.

If something is missing
- If a required file or endpoint behavior isn't discoverable in source/tests, ask for a short snippet of the server API contract (example responses) or point to the running test server used by CI.

Remember to add docstrings for any new classes or methods you create.
