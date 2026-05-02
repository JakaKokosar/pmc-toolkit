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
- parsing cached full-text XML into a normalized article dictionary with
  title, journal, article, affiliations, author notes, abstract, content,
  acknowledgements, data availability, related articles, custom metadata,
  competing interests, supplementary media, references, figures, and tables

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

Extract JSON groups from a cached XML file. Run `fetch --ext xml` first if the
XML is not already in the cache. The first extract command parses XML once and
writes `<cache-root>/<PMCid.N>/.pmc-extracted-article.json`; later extract
commands for the same article version read that JSON cache.

```bash
uv run pmc fetch PMC11370360.1 --ext xml
uv run pmc extract article-info PMC11370360.1
```

Choose one output group per command. Output is JSON by default:

```bash
uv run pmc extract article-info PMC11370360.1
uv run pmc extract content PMC11370360.1
uv run pmc extract references PMC11370360.1
uv run pmc extract figures PMC11370360.1
uv run pmc extract tables PMC11370360.1
uv run pmc extract supporting-info PMC11370360.1
```

`article-info.publication_date` currently uses the first publication date found
in the XML. If downstream consumers need to distinguish date types such as
`epub`, `ppub`, or `collection`, the output can be extended later.

## Project Layout

Here **“storage”** means the AWS bucket plus the local cache directory where
`pmc fetch` writes files—not a database or ORM.

- `src/pmc_toolkit/cli.py` - Typer CLI commands
- `src/pmc_toolkit/storage_api.py` - import this for programmatic use: list versions, metadata, list all keys, fetch to cache
- `src/pmc_toolkit/storage_utils.py` - boto3/unsigned S3 client, list-objects, downloads; implementation details for `storage_api`
- `src/pmc_toolkit/xml_parse_api.py` - import this for programmatic parsing of cached XML files
- `src/pmc_toolkit/xml_parse_utils.py` - small `lxml`-based helpers for cached full-text XML extraction
- `src/pmc_toolkit/cache.py` - per-article directories under the cache root, JSON metadata, cached S3 key listings, and safe local paths for downloaded objects
- `src/pmc_toolkit/validators.py` - identifier validation
- `src/pmc_toolkit/models.py` - response models
- `tests/` - automated tests

### Local cache

Each resolved article version has a directory `<cache_root>/<PMCid.N>/` containing:

- **`<PMCid.N>.json`** — cached metadata (from S3 `metadata/<PMCid.N>.json`), written after a successful read.
- **`.pmc-object-keys.json`** — JSON array of S3 object keys under that article’s prefix, written after `list_objects_v2` (or read on cache hit). If this file is missing or not a list of strings, listing or fetch may refetch from S3 or raise `ValueError` for an invalid manifest.
- **`.pmc-extracted-article.json`** — full extracted JSON produced from the cached XML by `pmc extract`; reused by later extract commands for the same article version.

**Cache root selection:** `pmc metadata` and `pmc files` (and the matching `storage_api` functions) always use the default OS user cache from [`platformdirs`](https://github.com/tox-dev/platformdirs). Only `pmc fetch` and `fetch_files(..., cache_dir=...)` accept `--cache-dir` or the `PMC_TOOLKIT_CACHE` environment variable.

**Download paths:** For each S3 key, the toolkit maps `PMCid.N/relative/path` to `<cache_root>/PMCid.N/relative/path`. Keys that do not start with the `PMCid.N/` prefix, use an absolute path segment, or resolve outside that directory (for example `..` path segments) are rejected with `ValueError` so downloads never leave the article folder.
