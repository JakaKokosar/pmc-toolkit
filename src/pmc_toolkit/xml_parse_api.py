"""Public API for parsing cached PMC full-text XML files."""

from pathlib import Path

from pmc_toolkit import cache as storage_cache
from pmc_toolkit import storage_utils
from pmc_toolkit.models import PMCParseResult
from pmc_toolkit.xml_parse_utils import extract_article_data, load_xml

PARSE_OUTPUT_KEYS = (
    "source",
    "title",
    "journal",
    "article",
    "affiliations",
    "author_notes",
    "related_articles",
    "custom_metadata",
    "abstract",
    "content",
    "acknowledgements",
    "data_availability",
    "competing_interests",
    "supplementary_media",
    "references",
    "figures",
    "tables",
)


def parse_cached_xml(
    requested_pmcid: str,
    cache_dir: Path | None = None,
) -> PMCParseResult:
    cache_root = storage_cache.resolve_cache_root(cache_dir)
    versioned_pmcid = storage_utils.resolve_versioned_pmcid(requested_pmcid)
    key = f"{versioned_pmcid}/{versioned_pmcid}.xml"
    xml_path = storage_cache.local_object_path(cache_root, versioned_pmcid, key)

    if not xml_path.exists():
        raise ValueError(
            "Cached XML not found. Run "
            f"`pmc fetch {versioned_pmcid} --ext xml"
            f"{' --cache-dir ' + str(cache_root) if cache_dir is not None else ''}` "
            f"first. Expected file: {xml_path}"
        )

    root = load_xml(xml_path)
    parsed = {
        "source": {
            "versioned_pmcid": versioned_pmcid,
            "xml_path": str(xml_path),
        },
        **extract_article_data(root),
    }
    return PMCParseResult(
        versioned_pmcid=versioned_pmcid,
        xml_path=str(xml_path),
        data=parsed,
    )


def select_parse_data(
    data: dict[str, object],
    selected_keys: list[str],
) -> dict[str, object]:
    if not selected_keys:
        return data

    return {key: data[key] for key in selected_keys if key in data}
