# Agent / dev notes

## After changing code

From the project root, run the full check (typecheck, lint, tests):

```bash
uv run ty check && uv run ruff check . && uv run pytest -q
```

- **ty** — static type check (`ty` is a dev dependency; use `uv run`).
- **ruff** — lint/format rules across the repo (library code and tests).
- **pytest** — test suite in `tests/`.
