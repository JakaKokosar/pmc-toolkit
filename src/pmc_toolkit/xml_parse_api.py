"""Public API for extracting cached PMC full-text XML files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from pmc_toolkit import cache as storage_cache
from pmc_toolkit import storage_utils

if TYPE_CHECKING:
    from pmc_toolkit.models import PMCExtractResult


def ensure_extracted_article(
    requested_pmcid: str,
    cache_dir: Path | None = None,
    force: bool = False,
) -> PMCExtractResult:
    extracted_path = ensure_extracted_article_cache(
        requested_pmcid,
        cache_dir=cache_dir,
        force=force,
    )
    cache_root = storage_cache.resolve_cache_root(cache_dir)
    versioned_pmcid = storage_utils.resolve_versioned_pmcid(requested_pmcid)
    key = f"{versioned_pmcid}/{versioned_pmcid}.xml"
    xml_path = storage_cache.local_object_path(cache_root, versioned_pmcid, key)
    cached = storage_cache.read_cached_extracted_article(cache_root, versioned_pmcid)
    if cached is None:
        raise ValueError(f"Invalid extracted article cache: {extracted_path}")

    from pmc_toolkit.models import PMCExtractResult

    return PMCExtractResult(
        versioned_pmcid=versioned_pmcid,
        xml_path=str(xml_path),
        data=cached,
    )


def ensure_extracted_article_cache(
    requested_pmcid: str,
    cache_dir: Path | None = None,
    force: bool = False,
) -> Path:
    cache_root = storage_cache.resolve_cache_root(cache_dir)
    versioned_pmcid = storage_utils.resolve_versioned_pmcid(requested_pmcid)
    extracted_path = storage_cache.extracted_article_cache_path(
        cache_root, versioned_pmcid
    )
    if extracted_path.exists() and not force:
        return extracted_path

    key = f"{versioned_pmcid}/{versioned_pmcid}.xml"
    xml_path = storage_cache.local_object_path(cache_root, versioned_pmcid, key)

    if not xml_path.exists():
        raise ValueError(
            "Cached XML not found. Run "
            f"`pmc fetch {versioned_pmcid} --ext xml"
            f"{' --cache-dir ' + str(cache_root) if cache_dir is not None else ''}` "
            f"first. Expected file: {xml_path}"
        )

    from pmc_toolkit.xml_parse_utils import extract_article_data, load_xml

    root = load_xml(xml_path)
    parsed = _group_extracted_article(
        extract_article_data(root),
        versioned_pmcid=versioned_pmcid,
        xml_path=xml_path,
    )
    storage_cache.write_cached_extracted_article(cache_root, versioned_pmcid, parsed)
    return extracted_path


def _group_extracted_article(
    raw_data: dict[str, Any],
    *,
    versioned_pmcid: str,
    xml_path: Path,
) -> dict[str, Any]:
    return {
        "_meta": {
            "versioned_pmcid": versioned_pmcid,
            "xml_path": str(xml_path),
        },
        "article-info": _article_info(raw_data),
        "content": raw_data["content"],
        "references": raw_data["references"],
        "figures": raw_data["figures"],
        "tables": raw_data["tables"],
        "supporting-info": {
            "acknowledgements": raw_data["acknowledgements"],
            "competing_interests": raw_data["competing_interests"],
            "data_availability": raw_data["data_availability"],
            "supplementary_media": raw_data["supplementary_media"],
            "author_notes": raw_data["author_notes"],
            "related_articles": raw_data["related_articles"],
            "custom_metadata": raw_data["custom_metadata"],
        },
    }


def _article_info(raw_data: dict[str, Any]) -> dict[str, Any]:
    journal = raw_data["journal"]
    article = raw_data["article"]
    abstract = raw_data["abstract"]

    return _compact_dict(
        {
            "journal": _journal_info(journal),
            "article_ids": _article_ids(article),
            "title": article.get("title"),
            "publication_date": _publication_date(article),
            "article_type": article.get("type"),
            "license": article.get("permissions", {}).get("license"),
            "keywords": article.get("keywords", []),
            "authors": _authors_with_affiliations(
                article.get("authors", []),
                raw_data.get("affiliations", []),
            ),
            "abstract": abstract.get("text"),
            "funding_grants": article.get("funding", []),
        },
        keep_empty={"keywords", "authors", "funding_grants"},
    )


def _journal_info(journal: dict[str, Any]) -> dict[str, Any]:
    return _compact_dict(
        {
            "name": journal.get("title"),
            "publisher": journal.get("publisher", {}).get("name"),
            "issn": _first_mapping_value(journal.get("issn", {})),
        }
    )


def _article_ids(article: dict[str, Any]) -> dict[str, Any]:
    identifiers = article.get("identifiers", {})
    return _compact_dict(
        {
            "doi": identifiers.get("doi"),
            "pmid": identifiers.get("pmid"),
            "pmcid": identifiers.get("pmcid"),
        }
    )


def _publication_date(article: dict[str, Any]) -> str | None:
    dates = article.get("publication_dates", [])
    for date in dates:
        if isinstance(date, dict) and date.get("date"):
            return date["date"]
    return None


def _authors_with_affiliations(
    authors: list[dict[str, Any]],
    affiliations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    affiliation_text_by_id = {
        affiliation["source_id"]: affiliation["text"]
        for affiliation in affiliations
        if affiliation.get("source_id") and affiliation.get("text")
    }
    return [
        _compact_dict(
            {
                "given_names": author.get("given_names"),
                "surname": author.get("surname"),
                "full_name": author.get("name"),
                "orcid": author.get("orcid"),
                "affiliations": [
                    affiliation_text_by_id[affiliation_id]
                    for affiliation_id in author.get("affiliation_ids", [])
                    if affiliation_id in affiliation_text_by_id
                ],
            },
            keep_empty={"affiliations"},
        )
        for author in authors
    ]


def _first_mapping_value(data: dict[str, Any]) -> Any | None:
    return next(iter(data.values()), None)


def _compact_dict(
    data: dict[str, Any],
    *,
    keep_empty: set[str] | None = None,
) -> dict[str, Any]:
    keep_empty = keep_empty or set()
    return {
        key: value
        for key, value in data.items()
        if key in keep_empty or value not in (None, "", [], {})
    }
