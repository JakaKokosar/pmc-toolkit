from collections.abc import Callable
import json
from pathlib import Path
from typing import Any, TypeVar

import typer

from pmc_toolkit.storage_api import (
    fetch_files,
    get_metadata,
    list_files,
    list_versions,
)
from pmc_toolkit.xml_parse_api import (
    ensure_extracted_article,
    select_extracted_data,
)
from pmc_toolkit.validators import parse_pmcid

CommandResult = TypeVar("CommandResult")

app = typer.Typer(
    help="CLI for interacting with the PMC Open Data S3 bucket.",
    no_args_is_help=True,
)
extract_app = typer.Typer(
    help="Extract JSON groups from cached PMC full-text XML.",
    no_args_is_help=True,
)
app.add_typer(extract_app, name="extract")


def _run_command(action: Callable[[], CommandResult]) -> CommandResult:
    try:
        return action()
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


def _emit_json(payload: Any) -> None:
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))


@app.command("versions")
def versions(
    pmcid: str = typer.Argument(..., help="PMC accession ID, e.g. PMC11370360"),
) -> None:
    """
    List all versions belonging to a PMCID.
    """

    def build_result():
        normalized_pmcid, version = parse_pmcid(pmcid)
        if version is not None:
            raise ValueError(
                "The versions command expects a base PMCID like 'PMC11370360', not a versioned ID."
            )
        return list_versions(normalized_pmcid)

    result = _run_command(build_result)
    _emit_json(result.model_dump(mode="json"))


@app.command("metadata")
def metadata(
    requested_pmcid: str = typer.Argument(
        ...,
        help="PMC accession ID or version ID, e.g. PMC11370360 or PMC11370360.1",
    ),
) -> None:
    """
    Fetch metadata for a PMC article identifier.
    """

    def build_result():
        return get_metadata(requested_pmcid)

    result = _run_command(build_result)
    _emit_json(result.model_dump(mode="json"))


@app.command("files")
def files(
    requested_pmcid: str = typer.Argument(
        ...,
        help="PMC accession ID or version ID, e.g. PMC11370360 or PMC11370360.1",
    ),
) -> None:
    """
    List every object stored under a PMC article version's S3 prefix.
    """

    def build_result():
        return list_files(requested_pmcid)

    result = _run_command(build_result)
    _emit_json(result.model_dump(mode="json"))


@app.command("fetch")
def fetch(
    requested_pmcid: str = typer.Argument(
        ...,
        help="PMC accession ID or version ID, e.g. PMC11370360 or PMC11370360.1",
    ),
    extensions: list[str] = typer.Option(
        None,
        "--ext",
        "-e",
        help=(
            "Restrict download to these file extensions. Repeat the option or pass a "
            "comma-separated list, e.g. -e pdf -e xml or -e pdf,xml."
        ),
    ),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        envvar="PMC_TOOLKIT_CACHE",
        help=(
            "Cache root (default: OS user cache dir for pmc-toolkit, e.g. XDG on Linux, "
            "Library/Caches on macOS, Local AppData on Windows). Files under <cache>/<PMCid.N>/."
        ),
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Re-download files even when they already exist in the cache.",
    ),
) -> None:
    """
    Download all (or filtered) files for a PMC article version into a local cache.
    """

    def build_result():
        return fetch_files(
            requested_pmcid,
            cache_dir=cache_dir,
            extensions=extensions,
            force=force,
        )

    result = _run_command(build_result)
    _emit_json(result.model_dump(mode="json"))


def _extract_json(
    requested_pmcid: str,
    cache_dir: Path | None,
    output_key: str,
) -> None:
    result = _run_command(
        lambda: ensure_extracted_article(requested_pmcid, cache_dir=cache_dir)
    )
    output = select_extracted_data(result.data, output_key)
    _emit_json(output)


@extract_app.command("article-info")
def extract_article_info(
    requested_pmcid: str = typer.Argument(
        ...,
        help="PMC accession ID or version ID, e.g. PMC11370360 or PMC11370360.1",
    ),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        envvar="PMC_TOOLKIT_CACHE",
        help="Cache root containing <PMCid.N>/<PMCid.N>.xml.",
    ),
) -> None:
    """Output JSON field article-info with article-info.journal, article_ids, title, publication_date, article_type, license, keywords, authors[], abstract, and funding_grants[]."""
    _extract_json(requested_pmcid, cache_dir, "article-info")


@extract_app.command("content")
def extract_content(
    requested_pmcid: str = typer.Argument(
        ...,
        help="PMC accession ID or version ID, e.g. PMC11370360 or PMC11370360.1",
    ),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        envvar="PMC_TOOLKIT_CACHE",
        help="Cache root containing <PMCid.N>/<PMCid.N>.xml.",
    ),
) -> None:
    """Output JSON field content with content.paragraphs[] and content.sections[]; objects include source_id, section_id, title, text, reference_ids, figure_ids, and table_ids."""
    _extract_json(requested_pmcid, cache_dir, "content")


@extract_app.command("references")
def extract_references(
    requested_pmcid: str = typer.Argument(
        ...,
        help="PMC accession ID or version ID, e.g. PMC11370360 or PMC11370360.1",
    ),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        envvar="PMC_TOOLKIT_CACHE",
        help="Cache root containing <PMCid.N>/<PMCid.N>.xml.",
    ),
) -> None:
    """Output JSON field references; each references[] item includes source_id, label, text, publication_type, identifiers, article_title, source, year, volume, issue, and pages."""
    _extract_json(requested_pmcid, cache_dir, "references")


@extract_app.command("figures")
def extract_figures(
    requested_pmcid: str = typer.Argument(
        ...,
        help="PMC accession ID or version ID, e.g. PMC11370360 or PMC11370360.1",
    ),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        envvar="PMC_TOOLKIT_CACHE",
        help="Cache root containing <PMCid.N>/<PMCid.N>.xml.",
    ),
) -> None:
    """Output JSON field figures; each figures[] item includes source_id, label, caption, and graphics."""
    _extract_json(requested_pmcid, cache_dir, "figures")


@extract_app.command("tables")
def extract_tables(
    requested_pmcid: str = typer.Argument(
        ...,
        help="PMC accession ID or version ID, e.g. PMC11370360 or PMC11370360.1",
    ),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        envvar="PMC_TOOLKIT_CACHE",
        help="Cache root containing <PMCid.N>/<PMCid.N>.xml.",
    ),
) -> None:
    """Output JSON field tables; each tables[] item includes source_id, label, caption, rows, and footnotes."""
    _extract_json(requested_pmcid, cache_dir, "tables")


@extract_app.command("supporting-info")
def extract_supporting_info(
    requested_pmcid: str = typer.Argument(
        ...,
        help="PMC accession ID or version ID, e.g. PMC11370360 or PMC11370360.1",
    ),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        envvar="PMC_TOOLKIT_CACHE",
        help="Cache root containing <PMCid.N>/<PMCid.N>.xml.",
    ),
) -> None:
    """Output JSON field supporting-info with acknowledgements, competing_interests, data_availability, supplementary_media, author_notes, related_articles, and custom_metadata."""
    _extract_json(requested_pmcid, cache_dir, "supporting-info")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
