# PMC Toolkit

Python toolkit and CLI for exploring, downloading, and parsing PMC article data
from the PMC Open Access dataset on AWS S3 (`s3://pmc-oa-opendata`).

## Current Status

The project currently supports:

- listing available versions for a PMCID
- validating PMC identifiers before making requests
- retrieving metadata for a PMC identifier, defaulting to the latest version for a base PMCID
- listing every object for a resolved article version, using the local cache when available
- downloading files for an article version into a local cache (optional `--ext`
  filters apply only to `fetch`, not to `files`; `--ext` accepts either a
  comma-separated list or repeated flags)

## Requirements

- Python 3.11+
- `uv`

## Setup

```bash
uv sync
```

## Development

After code changes, run the checks in [AGENTS.md](AGENTS.md) (typecheck, Ruff, tests).

## CLI Usage

Show the available commands:

```bash
uv run pmc --help
```

List versions for a PMC article:

```bash
uv run pmc versions PMC11370360
```

Get JSON output:

```bash
uv run pmc versions PMC11370360 --json
```

Fetch metadata for the latest available version of a PMCID:

```bash
uv run pmc metadata PMC11370360 --json
```

Fetch metadata for a specific version:

```bash
uv run pmc metadata PMC11370360.1 --json
```

List every object key for an article version (including media and supplements).
For unversioned IDs, the CLI resolves the latest version from S3 first; once the
version is known, the cached object-key manifest is reused when present. There
is no extension filter on this command.

```bash
uv run pmc files PMC11370360.1
```

Download files to a local cache. The default root is the **per-OS user cache
directory** from
[`platformdirs`](https://github.com/tox-dev/platformdirs) (e.g. `~/.cache/pmc-toolkit` on
Linux, `~/Library/Caches/pmc-toolkit` on macOS, and under `%LOCALAPPDATA%` on
Windows), with files under `<root>/<PMCid.N>/`. Override with `--cache-dir` or
`PMC_TOOLKIT_CACHE`.

```bash
uv run pmc fetch PMC11370360.1
```

Download only selected file types, re-downloading even if cached:

```bash
uv run pmc fetch PMC11370360.1 --ext xml,pdf,jpg --force
```

The `--ext` option also accepts repeated flags if you prefer the more explicit
form:

```bash
uv run pmc fetch PMC11370360.1 --ext pdf --ext xml --ext jpg --force
```

Override the cache location via a flag or the `PMC_TOOLKIT_CACHE` env var:

```bash
uv run pmc fetch PMC11370360.1 --cache-dir ./data
PMC_TOOLKIT_CACHE=./data uv run pmc fetch PMC11370360.1
```

## Project Layout

Here **“storage”** means the AWS bucket plus the local cache directory where
`pmc fetch` writes files—not a database or ORM.

- `src/pmc_toolkit/cli.py` - Typer CLI commands
- `src/pmc_toolkit/storage_api.py` - import this for programmatic use: list versions, metadata, list all keys, fetch to cache
- `src/pmc_toolkit/storage_utils.py` - boto3/unsigned S3 client, list-objects, downloads, `platformdirs` cache root; implementation details for `storage_api`
- `src/pmc_toolkit/validators.py` - identifier validation
- `src/pmc_toolkit/models.py` - response models
- `tests/` - automated tests
