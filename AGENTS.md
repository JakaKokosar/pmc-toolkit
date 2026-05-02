# Agent / dev notes

- ALWAYS use **uv** for Python environment, dependency, and tool commands; do not use **pip**, **python -m pip**, **virtualenv**, **poetry**, or similar unless explicitly asked.

- ALWAYS run repo tools via **`uv run`** from the project root.

- AFTER Python edits, run **`uv run ty check`**, **`uv run ruff check`**, and **`uv run ruff format`**; run **`uv sync`** when dependencies change.

- AFTER behavior changes, run **`uv run pytest`** to check for regressions and report the result.

- PREFER **`uv run pytest`** with a path, node id, or **`-k`** while iterating, not the whole suite each time.

- NEVER start development servers, watchers, builds, or long-running local processes unless explicitly asked.

- NEVER add or modify tests unless explicitly asked.

- NEVER assume **`ruff`**, **`ty check`**, or **`pytest`** failures on main are pre-existing.

- AVOID shortened names; prefer descriptive names like `version` over `ver`.
