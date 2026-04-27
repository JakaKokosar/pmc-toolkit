"""Public API for the PMC open-access **S3 dataset** and **local download cache**.

CLI commands use this API; low-level S3 helpers live in :mod:`pmc_toolkit.storage_utils`
and local cache helpers live in :mod:`pmc_toolkit.cache`."""

from pathlib import Path

from pmc_toolkit import cache as storage_cache
from pmc_toolkit import storage_utils
from pmc_toolkit.models import (
    FetchAction,
    PMCFetchFile,
    PMCFetchResult,
    PMCFiles,
    PMCMetadata,
    PMCVersions,
)


def list_versions(pmcid: str) -> PMCVersions:
    versions = storage_utils.list_versioned_pmcids(pmcid)
    return PMCVersions(
        pmcid=pmcid,
        versions=sorted(set(versions), key=storage_utils.version_number),
    )


def get_metadata(requested_pmcid: str) -> PMCMetadata:
    cache_root = storage_cache.resolve_cache_root()
    versioned_pmcid = storage_utils.resolve_versioned_pmcid(requested_pmcid)
    cached = storage_cache.read_cached_metadata(cache_root, versioned_pmcid)

    if cached is not None:
        return cached

    metadata = storage_utils.read_metadata(versioned_pmcid)
    storage_cache.write_cached_metadata(cache_root, versioned_pmcid, metadata)
    return metadata


def list_files(requested_pmcid: str) -> PMCFiles:
    cache_root = storage_cache.resolve_cache_root()
    versioned_pmcid = storage_utils.resolve_versioned_pmcid(requested_pmcid)
    keys = storage_utils.read_or_cache_object_keys(cache_root, versioned_pmcid)

    return PMCFiles(versioned_pmcid=versioned_pmcid, keys=keys)


def fetch_files(
    requested_pmcid: str,
    cache_dir: Path | None = None,
    extensions: list[str] | None = None,
    force: bool = False,
) -> PMCFetchResult:
    cache_root = storage_cache.resolve_cache_root(cache_dir)
    versioned_pmcid = storage_utils.resolve_versioned_pmcid(requested_pmcid)
    all_keys = storage_utils.read_or_cache_object_keys(cache_root, versioned_pmcid)

    normalized = storage_utils.normalize_extensions(extensions)
    keys = [
        key for key in all_keys if storage_utils.key_matches_extensions(key, normalized)
    ]

    article_dir = storage_cache.article_cache_dir(cache_root, versioned_pmcid)
    article_dir.mkdir(parents=True, exist_ok=True)

    results: list[PMCFetchFile] = []

    for key in keys:
        dest = storage_cache.local_object_path(cache_root, versioned_pmcid, key)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists() and not force:
            results.append(
                PMCFetchFile(key=key, local_path=str(dest), action=FetchAction.SKIPPED)
            )
            continue

        storage_utils.download_object(key, dest)
        results.append(
            PMCFetchFile(key=key, local_path=str(dest), action=FetchAction.DOWNLOADED)
        )

    return PMCFetchResult(
        versioned_pmcid=versioned_pmcid,
        cache_dir=str(article_dir),
        files=results,
    )
