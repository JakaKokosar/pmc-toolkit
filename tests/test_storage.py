import json
from pathlib import Path

import pytest
from botocore.exceptions import ClientError

from pmc_toolkit import cache as storage_cache
from pmc_toolkit.models import FetchAction
from pmc_toolkit.storage_api import fetch_files, get_metadata, list_files, list_versions


class FakePaginator:
    def __init__(self, pages: list[dict]) -> None:
        self._pages = pages
        self.calls: list[dict] = []

    def paginate(self, **kwargs) -> list[dict]:
        self.calls.append(kwargs)
        return self._pages


def _keys_to_pages(keys: list[str]) -> list[dict]:
    return [{"Contents": [{"Key": key} for key in keys]}]


def _metadata_payload(version: int) -> dict:
    versioned_pmcid = f"PMC11370360.{version}"
    return {
        "pmcid": "PMC11370360",
        "version": version,
        "pmid": 123456 if version == 2 else None,
        "doi": "10.1000/example" if version == 2 else None,
        "mid": None,
        "title": "Example title",
        "citation": "Example citation",
        "is_pmc_openaccess": True,
        "is_manuscript": False,
        "is_historical_ocr": False,
        "is_retracted": False,
        "license_code": "CC BY" if version == 2 else None,
        "xml_url": f"s3://pmc-oa-opendata/{versioned_pmcid}/{versioned_pmcid}.xml",
        "pdf_url": (
            f"s3://pmc-oa-opendata/{versioned_pmcid}/{versioned_pmcid}.pdf"
            if version == 2
            else None
        ),
        "media_urls": [],
        "text_url": f"s3://pmc-oa-opendata/{versioned_pmcid}/{versioned_pmcid}.txt",
    }


def _write_cached_metadata(cache_root: Path, versioned_pmcid: str, payload: dict) -> None:
    article_dir = cache_root / versioned_pmcid
    article_dir.mkdir(parents=True, exist_ok=True)
    (article_dir / f"{versioned_pmcid}.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def _write_cached_object_keys(
    cache_root: Path, versioned_pmcid: str, keys: list[str]
) -> None:
    article_dir = cache_root / versioned_pmcid
    article_dir.mkdir(parents=True, exist_ok=True)
    (article_dir / storage_cache.OBJECT_KEYS_CACHE_FILENAME).write_text(
        json.dumps(keys, indent=2),
        encoding="utf-8",
    )


def test_get_metadata_uses_latest_version_when_not_provided(
    monkeypatch, tmp_path
) -> None:
    payload = _metadata_payload(version=2)

    class FakeBody:
        def read(self) -> bytes:
            return json.dumps(payload).encode()

    class FakeS3Client:
        def get_object(self, *, Bucket: str, Key: str) -> dict:
            assert Bucket == "pmc-oa-opendata"
            assert Key == "metadata/PMC11370360.2.json"
            return {"Body": FakeBody()}

    monkeypatch.setattr("pmc_toolkit.cache.default_cache_root", lambda: tmp_path)
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils.list_versioned_pmcids",
        lambda pmcid: ["PMC11370360.1", "PMC11370360.2"],
    )
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    result = get_metadata("PMC11370360")

    assert result.pmcid == "PMC11370360"
    assert result.version == 2
    cached = json.loads(
        (tmp_path / "PMC11370360.2" / "PMC11370360.2.json").read_text(encoding="utf-8")
    )
    assert cached["version"] == 2


def test_get_metadata_uses_cached_explicit_version(monkeypatch, tmp_path) -> None:
    _write_cached_metadata(tmp_path, "PMC11370360.1", _metadata_payload(version=1))

    class FakeS3Client:
        def get_object(self, *, Bucket: str, Key: str) -> dict:
            raise AssertionError("expected cached metadata to avoid S3")

    monkeypatch.setattr("pmc_toolkit.cache.default_cache_root", lambda: tmp_path)
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    result = get_metadata("PMC11370360.1")

    assert result.pmcid == "PMC11370360"
    assert result.version == 1


def test_get_metadata_uses_cached_latest_version_after_s3_resolution(
    monkeypatch, tmp_path
) -> None:
    _write_cached_metadata(tmp_path, "PMC11370360.1", _metadata_payload(version=1))
    _write_cached_metadata(tmp_path, "PMC11370360.2", _metadata_payload(version=2))

    monkeypatch.setattr("pmc_toolkit.cache.default_cache_root", lambda: tmp_path)
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils.list_versioned_pmcids",
        lambda pmcid: ["PMC11370360.1", "PMC11370360.2"],
    )
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client",
        lambda: type(
            "C",
            (),
            {
                "get_object": lambda self, **kwargs: (_ for _ in ()).throw(
                    AssertionError("expected cached latest metadata to avoid S3 fetch")
                )
            },
        )(),
    )

    result = get_metadata("PMC11370360")

    assert result.pmcid == "PMC11370360"
    assert result.version == 2


def test_get_metadata_ignores_older_cached_versions_when_s3_has_newer_one(
    monkeypatch, tmp_path
) -> None:
    payload = _metadata_payload(version=3)
    _write_cached_metadata(tmp_path, "PMC11370360.1", _metadata_payload(version=1))
    _write_cached_metadata(tmp_path, "PMC11370360.2", _metadata_payload(version=2))

    class FakeBody:
        def read(self) -> bytes:
            return json.dumps(payload).encode()

    class FakeS3Client:
        def get_object(self, *, Bucket: str, Key: str) -> dict:
            assert Bucket == "pmc-oa-opendata"
            assert Key == "metadata/PMC11370360.3.json"
            return {"Body": FakeBody()}

    monkeypatch.setattr("pmc_toolkit.cache.default_cache_root", lambda: tmp_path)
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils.list_versioned_pmcids",
        lambda pmcid: ["PMC11370360.1", "PMC11370360.2", "PMC11370360.3"],
    )
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    result = get_metadata("PMC11370360")

    assert result.version == 3
    cached = json.loads(
        (tmp_path / "PMC11370360.3" / "PMC11370360.3.json").read_text(encoding="utf-8")
    )
    assert cached["version"] == 3


def test_get_metadata_raises_value_error_for_missing_object(
    monkeypatch, tmp_path
) -> None:
    class FakeS3Client:
        def get_object(self, *, Bucket: str, Key: str) -> dict:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

    monkeypatch.setattr("pmc_toolkit.cache.default_cache_root", lambda: tmp_path)
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    with pytest.raises(ValueError, match="No metadata found"):
        get_metadata("PMC11370360.1")


def test_list_versions_sorts_numeric_suffixes(monkeypatch) -> None:
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils.list_versioned_pmcids",
        lambda pmcid: ["PMC11370360.2", "PMC11370360.10", "PMC11370360.1"],
    )

    result = list_versions("PMC11370360")

    assert result.versions == ["PMC11370360.1", "PMC11370360.2", "PMC11370360.10"]


def test_list_files_fetches_and_caches_keys_on_cache_miss(
    monkeypatch, tmp_path
) -> None:
    keys = [
        "PMC11370360.1/PMC11370360.1.xml",
        "PMC11370360.1/PMC11370360.1.pdf",
        "PMC11370360.1/PMC11370360.1.txt",
        "PMC11370360.1/PMC11370360.1.json",
        "PMC11370360.1/gr1.jpg",
        "PMC11370360.1/mmc1.pdf",
    ]
    paginator = FakePaginator(_keys_to_pages(keys))

    class FakeS3Client:
        def get_paginator(self, name: str):
            assert name == "list_objects_v2"
            return paginator

    monkeypatch.setattr("pmc_toolkit.cache.default_cache_root", lambda: tmp_path)
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    result = list_files("PMC11370360.1")

    assert result.versioned_pmcid == "PMC11370360.1"
    assert result.keys == sorted(keys)
    assert paginator.calls == [
        {"Bucket": "pmc-oa-opendata", "Prefix": "PMC11370360.1/"}
    ]
    cached = json.loads(
        (
            tmp_path
            / "PMC11370360.1"
            / storage_cache.OBJECT_KEYS_CACHE_FILENAME
        ).read_text(encoding="utf-8")
    )
    assert cached == sorted(keys)


def test_list_files_uses_cached_manifest_for_explicit_version(
    monkeypatch, tmp_path
) -> None:
    keys = ["PMC11370360.1/PMC11370360.1.xml", "PMC11370360.1/PMC11370360.1.pdf"]
    _write_cached_object_keys(tmp_path, "PMC11370360.1", keys)

    class FakeS3Client:
        def get_paginator(self, name: str):
            raise AssertionError("expected cached manifest to avoid S3 list")

    monkeypatch.setattr("pmc_toolkit.cache.default_cache_root", lambda: tmp_path)
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    result = list_files("PMC11370360.1")

    assert result.versioned_pmcid == "PMC11370360.1"
    assert result.keys == sorted(keys)


def test_list_files_uses_cached_manifest_after_s3_version_resolution(
    monkeypatch, tmp_path
) -> None:
    keys = ["PMC11370360.2/PMC11370360.2.xml"]
    _write_cached_object_keys(tmp_path, "PMC11370360.2", keys)

    monkeypatch.setattr(
        "pmc_toolkit.storage_utils.list_versioned_pmcids",
        lambda pmcid: ["PMC11370360.1", "PMC11370360.2"],
    )
    monkeypatch.setattr("pmc_toolkit.cache.default_cache_root", lambda: tmp_path)
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client",
        lambda: type(
            "C",
            (),
            {
                "get_paginator": lambda self, name: (_ for _ in ()).throw(
                    AssertionError("expected cached manifest to avoid S3 list")
                )
            },
        )(),
    )

    result = list_files("PMC11370360")

    assert result.versioned_pmcid == "PMC11370360.2"
    assert result.keys == keys


def test_list_files_raises_when_prefix_is_empty(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("pmc_toolkit.cache.default_cache_root", lambda: tmp_path)
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client",
        lambda: type(
            "C",
            (),
            {"get_paginator": lambda self, name: FakePaginator([{"Contents": []}])},
        )(),
    )

    with pytest.raises(ValueError, match="No files found"):
        list_files("PMC11370360.1")


def test_fetch_files_downloads_and_skips_existing(monkeypatch, tmp_path) -> None:
    keys = [
        "PMC11370360.1/PMC11370360.1.xml",
        "PMC11370360.1/PMC11370360.1.pdf",
    ]
    downloads: list[tuple[str, str, str]] = []
    paginator = FakePaginator(_keys_to_pages(keys))

    class FakeS3Client:
        def get_paginator(self, name: str):
            assert name == "list_objects_v2"
            return paginator

        def download_file(self, Bucket, Key, Filename):  # noqa: N803
            downloads.append((Bucket, Key, Filename))
            Path(Filename).touch()

    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    result = fetch_files("PMC11370360.1", cache_dir=tmp_path)

    assert result.versioned_pmcid == "PMC11370360.1"
    assert result.cache_dir == str(tmp_path / "PMC11370360.1")
    assert [f.action for f in result.files] == [
        FetchAction.DOWNLOADED,
        FetchAction.DOWNLOADED,
    ]
    assert len(downloads) == 2
    assert paginator.calls == [
        {"Bucket": "pmc-oa-opendata", "Prefix": "PMC11370360.1/"}
    ]
    cached = json.loads(
        (
            tmp_path
            / "PMC11370360.1"
            / storage_cache.OBJECT_KEYS_CACHE_FILENAME
        ).read_text(encoding="utf-8")
    )
    assert cached == sorted(keys)

    result_again = fetch_files("PMC11370360.1", cache_dir=tmp_path)
    assert [f.action for f in result_again.files] == [
        FetchAction.SKIPPED,
        FetchAction.SKIPPED,
    ]
    assert len(downloads) == 2
    assert len(paginator.calls) == 1


def test_fetch_files_force_redownloads(monkeypatch, tmp_path) -> None:
    keys = ["PMC11370360.1/PMC11370360.1.xml"]
    downloads: list[str] = []
    _write_cached_object_keys(tmp_path, "PMC11370360.1", keys)

    class FakeS3Client:
        def get_paginator(self, name: str):
            raise AssertionError("expected cached manifest to avoid S3 list")

        def download_file(self, Bucket, Key, Filename):  # noqa: N803
            downloads.append(Key)
            Path(Filename).touch()

    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    fetch_files("PMC11370360.1", cache_dir=tmp_path)
    fetch_files("PMC11370360.1", cache_dir=tmp_path, force=True)

    assert len(downloads) == 2


def test_fetch_files_downloads_only_missing_files_from_cached_manifest(
    monkeypatch, tmp_path
) -> None:
    keys = [
        "PMC11370360.1/PMC11370360.1.xml",
        "PMC11370360.1/PMC11370360.1.pdf",
    ]
    downloads: list[str] = []
    _write_cached_object_keys(tmp_path, "PMC11370360.1", keys)
    (tmp_path / "PMC11370360.1" / "PMC11370360.1.xml").parent.mkdir(
        parents=True, exist_ok=True
    )
    (tmp_path / "PMC11370360.1" / "PMC11370360.1.xml").touch()

    class FakeS3Client:
        def get_paginator(self, name: str):
            raise AssertionError("expected cached manifest to avoid S3 list")

        def download_file(self, Bucket, Key, Filename):  # noqa: N803
            downloads.append(Key)
            Path(Filename).touch()

    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    result = fetch_files("PMC11370360.1", cache_dir=tmp_path)

    assert downloads == ["PMC11370360.1/PMC11370360.1.pdf"]
    assert {file.key: file.action for file in result.files} == {
        "PMC11370360.1/PMC11370360.1.pdf": FetchAction.DOWNLOADED,
        "PMC11370360.1/PMC11370360.1.xml": FetchAction.SKIPPED,
    }


def test_fetch_files_honors_extensions(monkeypatch, tmp_path) -> None:
    keys = [
        "PMC11370360.1/PMC11370360.1.xml",
        "PMC11370360.1/PMC11370360.1.pdf",
        "PMC11370360.1/gr1.jpg",
    ]
    downloads: list[str] = []

    class FakeS3Client:
        def get_paginator(self, name: str):
            return FakePaginator(_keys_to_pages(keys))

        def download_file(self, Bucket, Key, Filename):  # noqa: N803
            downloads.append(Key)
            Path(Filename).touch()

    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    result = fetch_files("PMC11370360.1", cache_dir=tmp_path, extensions=["pdf"])

    assert downloads == ["PMC11370360.1/PMC11370360.1.pdf"]
    assert [f.key for f in result.files] == ["PMC11370360.1/PMC11370360.1.pdf"]


def test_fetch_files_honors_comma_separated_extensions(monkeypatch, tmp_path) -> None:
    keys = [
        "PMC11370360.1/PMC11370360.1.xml",
        "PMC11370360.1/PMC11370360.1.pdf",
        "PMC11370360.1/gr1.jpg",
        "PMC11370360.1/PMC11370360.1.txt",
    ]
    downloads: list[str] = []

    class FakeS3Client:
        def get_paginator(self, name: str):
            return FakePaginator(_keys_to_pages(keys))

        def download_file(self, Bucket, Key, Filename):  # noqa: N803
            downloads.append(Key)
            Path(Filename).touch()

    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    result = fetch_files(
        "PMC11370360.1",
        cache_dir=tmp_path,
        extensions=["xml,pdf,jpg"],
    )

    assert downloads == [
        "PMC11370360.1/PMC11370360.1.pdf",
        "PMC11370360.1/PMC11370360.1.xml",
        "PMC11370360.1/gr1.jpg",
    ]
    assert [f.key for f in result.files] == [
        "PMC11370360.1/PMC11370360.1.pdf",
        "PMC11370360.1/PMC11370360.1.xml",
        "PMC11370360.1/gr1.jpg",
    ]


def test_fetch_files_rejects_path_traversal_keys(monkeypatch, tmp_path) -> None:
    keys = ["PMC11370360.1/../../outside.txt"]

    class FakeS3Client:
        def get_paginator(self, name: str):
            return FakePaginator(_keys_to_pages(keys))

        def download_file(self, Bucket, Key, Filename):  # noqa: N803
            raise AssertionError("expected key sanitization to prevent downloads")

    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    with pytest.raises(ValueError, match="Unsafe object key path"):
        fetch_files("PMC11370360.1", cache_dir=tmp_path)


def test_fetch_files_uses_custom_cache_dir_after_s3_version_resolution(
    monkeypatch, tmp_path
) -> None:
    default_root = tmp_path / "default-cache"
    custom_root = tmp_path / "custom-cache"
    keys = ["PMC11370360.1/PMC11370360.1.xml"]
    downloads: list[str] = []
    _write_cached_metadata(default_root, "PMC11370360.2", _metadata_payload(version=2))
    _write_cached_object_keys(custom_root, "PMC11370360.1", keys)

    class FakeS3Client:
        def get_paginator(self, name: str):
            raise AssertionError("expected custom cache root to avoid S3 list")

        def download_file(self, Bucket, Key, Filename):  # noqa: N803
            downloads.append(Key)
            Path(Filename).touch()

    monkeypatch.setattr(
        "pmc_toolkit.cache.default_cache_root", lambda: default_root
    )
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils.list_versioned_pmcids",
        lambda pmcid: ["PMC11370360.1"],
    )
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    result = fetch_files("PMC11370360", cache_dir=custom_root)

    assert result.versioned_pmcid == "PMC11370360.1"
    assert result.cache_dir == str(custom_root / "PMC11370360.1")
    assert downloads == ["PMC11370360.1/PMC11370360.1.xml"]


def test_fetch_files_ignores_older_cached_versions_when_s3_has_newer_one(
    monkeypatch, tmp_path
) -> None:
    downloads: list[str] = []
    keys = ["PMC11370360.3/PMC11370360.3.pdf"]
    paginator = FakePaginator(_keys_to_pages(keys))
    _write_cached_object_keys(
        tmp_path,
        "PMC11370360.2",
        ["PMC11370360.2/PMC11370360.2.pdf"],
    )

    class FakeS3Client:
        def get_paginator(self, name: str):
            assert name == "list_objects_v2"
            return paginator

        def download_file(self, Bucket, Key, Filename):  # noqa: N803
            downloads.append(Key)
            Path(Filename).touch()

    monkeypatch.setattr(
        "pmc_toolkit.storage_utils.list_versioned_pmcids",
        lambda pmcid: ["PMC11370360.1", "PMC11370360.2", "PMC11370360.3"],
    )
    monkeypatch.setattr(
        "pmc_toolkit.storage_utils._get_s3_client", lambda: FakeS3Client()
    )

    result = fetch_files("PMC11370360", cache_dir=tmp_path, extensions=["pdf"])

    assert result.versioned_pmcid == "PMC11370360.3"
    assert downloads == ["PMC11370360.3/PMC11370360.3.pdf"]
    assert paginator.calls == [
        {"Bucket": "pmc-oa-opendata", "Prefix": "PMC11370360.3/"}
    ]
