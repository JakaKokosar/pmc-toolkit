"""Local filesystem cache helpers for PMC metadata, manifests, and downloads."""

import json
from pathlib import Path
from typing import Any

from platformdirs import user_cache_dir

from pmc_toolkit.models import PMCMetadata

OBJECT_KEYS_CACHE_FILENAME = ".pmc-object-keys.json"


def default_cache_root() -> Path:
    return Path(user_cache_dir("pmc-toolkit", appauthor=False))


def resolve_cache_root(cache_dir: Path | None = None) -> Path:
    return Path(cache_dir) if cache_dir is not None else default_cache_root()


def article_cache_dir(cache_root: Path, versioned_pmcid: str) -> Path:
    return cache_root / versioned_pmcid


def metadata_cache_path(cache_root: Path, versioned_pmcid: str) -> Path:
    return article_cache_dir(cache_root, versioned_pmcid) / f"{versioned_pmcid}.json"


def object_keys_cache_path(cache_root: Path, versioned_pmcid: str) -> Path:
    return article_cache_dir(cache_root, versioned_pmcid) / OBJECT_KEYS_CACHE_FILENAME


def _read_json_file(path: Path) -> Any | None:
    if not path.exists():
        return None

    return json.loads(path.read_text(encoding="utf-8"))


def read_cached_metadata(cache_root: Path, versioned_pmcid: str) -> PMCMetadata | None:
    payload = _read_json_file(metadata_cache_path(cache_root, versioned_pmcid))
    if payload is None:
        return None

    return PMCMetadata.model_validate(payload)


def write_cached_metadata(
    cache_root: Path, versioned_pmcid: str, metadata: PMCMetadata
) -> None:
    path = metadata_cache_path(cache_root, versioned_pmcid)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")


def read_cached_object_keys(
    cache_root: Path, versioned_pmcid: str
) -> list[str] | None:
    payload = _read_json_file(object_keys_cache_path(cache_root, versioned_pmcid))
    if payload is None:
        return None
    if not isinstance(payload, list) or not all(isinstance(item, str) for item in payload):
        raise ValueError(f"Invalid cached file listing for article: {versioned_pmcid}.")

    return sorted(payload)


def write_cached_object_keys(
    cache_root: Path, versioned_pmcid: str, keys: list[str]
) -> None:
    path = object_keys_cache_path(cache_root, versioned_pmcid)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(keys), indent=2), encoding="utf-8")


def local_object_path(cache_root: Path, versioned_pmcid: str, key: str) -> Path:
    """Return the local cache path for an S3 object key.

    S3 object keys are remote-controlled opaque strings, not trusted filesystem paths.
    A key may still start with the expected article prefix while using ``..`` or an
    absolute path segment to escape the article cache directory, so this helper
    enforces that the resolved destination remains inside that directory.
    """
    prefix = f"{versioned_pmcid}/"
    if not key.startswith(prefix):
        raise ValueError(f"Object key {key!r} does not belong to article: {versioned_pmcid}.")

    relpath = key.removeprefix(prefix)
    article_dir = article_cache_dir(cache_root, versioned_pmcid)

    # Keep downloads contained to the article cache directory without allowing
    # S3's opaque key strings to alias each other as normalized filesystem paths.
    key_parts = relpath.split("/")
    if (
        Path(relpath).is_absolute()
        or any(part in {"", ".", ".."} or "\\" in part for part in key_parts)
    ):
        raise ValueError(f"Unsafe object key path for article: {versioned_pmcid}.")

    dest_path = article_dir.joinpath(*key_parts).resolve()
    article_dir_resolved = article_dir.resolve()
    if not dest_path.is_relative_to(article_dir_resolved):
        raise ValueError(f"Unsafe object key path for article: {versioned_pmcid}.")

    return dest_path
