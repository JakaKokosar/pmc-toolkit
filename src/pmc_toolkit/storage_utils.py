"""Internal S3 helpers for ``storage_api``; local cache helpers live in
:mod:`pmc_toolkit.cache`. Not the Python import surface—use
:mod:`pmc_toolkit.storage_api`."""

import json
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

import boto3
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import ClientError

from pmc_toolkit import cache as storage_cache
from pmc_toolkit.models import PMCMetadata
from pmc_toolkit.validators import parse_pmcid

if TYPE_CHECKING:
    from types_boto3_s3.client import S3Client

BUCKET = "pmc-oa-opendata"
REGION = "us-east-1"


# Shared S3 setup
@cache
def _get_s3_client() -> "S3Client":
    return boto3.client(
        "s3", region_name=REGION, config=Config(signature_version=UNSIGNED)
    )


# Version resolution helpers
def version_number(versioned_pmcid: str) -> int:
    return int(versioned_pmcid.rsplit(".", 1)[1])


def list_versioned_pmcids(pmcid: str) -> list[str]:
    prefix = f"{pmcid}."

    s3 = _get_s3_client()
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(
        Bucket=BUCKET,
        Prefix=prefix,
        Delimiter="/",
    )

    versions: list[str] = []

    for page in pages:
        for item in page.get("CommonPrefixes", []):
            raw_prefix = item["Prefix"]
            version = raw_prefix.rstrip("/")
            if version:
                versions.append(version)

    return versions


def _latest_versioned_pmcid(pmcid: str) -> str:
    """Return the highest available article version published for a base PMCID."""
    versions = list_versioned_pmcids(pmcid)

    if not versions:
        raise ValueError(f"No versions found for PMCID: {pmcid}.")

    return max(versions, key=version_number)


def resolve_versioned_pmcid(requested_pmcid: str) -> str:
    """Resolve a PMCID input to an explicit version, using the latest version when omitted."""
    pmcid, version = parse_pmcid(requested_pmcid)
    return f"{pmcid}.{version}" if version is not None else _latest_versioned_pmcid(pmcid)


# Metadata S3 helpers
def read_metadata(versioned_pmcid: str) -> PMCMetadata:
    """Fetch article metadata from the S3 metadata index for a specific version."""
    key = f"metadata/{versioned_pmcid}.json"

    s3 = _get_s3_client()

    try:
        response = s3.get_object(Bucket=BUCKET, Key=key)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"NoSuchKey", "404"}:
            raise ValueError(f"No metadata found for article: {versioned_pmcid}.") from exc
        raise

    payload = json.loads(response["Body"].read())
    return PMCMetadata.model_validate(payload)


# Object-key listing helpers
def list_object_keys(versioned_pmcid: str) -> list[str]:
    prefix = f"{versioned_pmcid}/"

    s3 = _get_s3_client()
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=BUCKET, Prefix=prefix)

    keys: list[str] = []
    for page in pages:
        for item in page.get("Contents", []):
            key = item.get("Key")
            if key and not key.endswith("/"):
                keys.append(key)

    return sorted(keys)


def read_or_cache_object_keys(cache_root: Path, versioned_pmcid: str) -> list[str]:
    """Return cached object keys when available, otherwise list S3 and persist the result."""
    keys = storage_cache.read_cached_object_keys(cache_root, versioned_pmcid)
    if keys is not None:
        return keys

    keys = list_object_keys(versioned_pmcid)
    if not keys:
        raise ValueError(f"No files found for article: {versioned_pmcid}.")

    storage_cache.write_cached_object_keys(cache_root, versioned_pmcid, keys)
    return keys


# Fetch filtering and downloads
def normalize_extensions(extensions: list[str] | None) -> set[str] | None:
    """Normalize repeated or comma-separated extension filters into a lowercase suffix set."""
    if not extensions:
        return None
    normalized = {
        part.strip().lower().lstrip(".")
        for ext in extensions
        for part in ext.split(",")
        if part.strip()
    }
    return normalized or None


def key_matches_extensions(key: str, extensions: set[str] | None) -> bool:
    if extensions is None:
        return True
    filename = key.rsplit("/", 1)[-1]
    _, _, ext = filename.rpartition(".")
    return bool(ext) and ext.lower() in extensions


def download_object(key: str, dest: Path) -> None:
    _get_s3_client().download_file(BUCKET, key, str(dest))
