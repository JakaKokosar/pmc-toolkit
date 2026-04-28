from collections.abc import Callable
import json
from pathlib import Path
from typing import TypeVar

import typer

from pmc_toolkit.storage_api import (
    fetch_files,
    get_metadata,
    list_files,
    list_versions,
)
from pmc_toolkit.xml_parse_api import parse_cached_xml, select_parse_data
from pmc_toolkit.validators import parse_pmcid

CommandResult = TypeVar("CommandResult")

app = typer.Typer(
    help="CLI for interacting with the PMC Open Data S3 bucket.",
    no_args_is_help=True,
)


def _run_command(action: Callable[[], CommandResult]) -> CommandResult:
    try:
        return action()
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command("versions")
def versions(
    pmcid: str = typer.Argument(..., help="PMC accession ID, e.g. PMC11370360"),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print machine-readable JSON output.",
    ),
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

    if json_output:
        typer.echo(result.model_dump_json(indent=2))
        return

    for version in result.versions:
        typer.echo(version)


@app.command("metadata")
def metadata(
    requested_pmcid: str = typer.Argument(
        ...,
        help="PMC accession ID or version ID, e.g. PMC11370360 or PMC11370360.1",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print machine-readable JSON output.",
    ),
) -> None:
    """
    Fetch metadata for a PMC article identifier.
    """
    def build_result():
        return get_metadata(requested_pmcid)

    result = _run_command(build_result)

    if json_output:
        typer.echo(result.model_dump_json(indent=2))
        return

    for key, value in result.model_dump().items():
        typer.echo(f"{key}: {value}")


@app.command("files")
def files(
    requested_pmcid: str = typer.Argument(
        ...,
        help="PMC accession ID or version ID, e.g. PMC11370360 or PMC11370360.1",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print machine-readable JSON output.",
    ),
) -> None:
    """
    List every object stored under a PMC article version's S3 prefix.
    """
    def build_result():
        return list_files(requested_pmcid)

    result = _run_command(build_result)

    if json_output:
        typer.echo(result.model_dump_json(indent=2))
        return

    for key in result.keys:
        typer.echo(key)


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
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print machine-readable JSON output.",
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

    if json_output:
        typer.echo(result.model_dump_json(indent=2))
        return

    typer.echo(f"Cache directory: {result.cache_dir}")
    for file in result.files:
        typer.echo(f"[{file.action.value}] {file.local_path}")


@app.command("parse")
def parse_xml(
    requested_pmcid: str = typer.Argument(
        ...,
        help="PMC accession ID or version ID, e.g. PMC11370360 or PMC11370360.1",
    ),
    source: bool = typer.Option(
        False,
        "--source",
        help="Return the source identifier and XML path.",
    ),
    title: bool = typer.Option(
        False,
        "--title",
        help="Return the article title.",
    ),
    journal: bool = typer.Option(
        False,
        "--journal",
        "--journal-meta",
        help="Return journal metadata.",
    ),
    article: bool = typer.Option(
        False,
        "--article",
        "--article-meta",
        help="Return article metadata.",
    ),
    affiliations: bool = typer.Option(
        False,
        "--affiliations",
        help="Return author affiliations.",
    ),
    author_notes: bool = typer.Option(
        False,
        "--author-notes",
        help="Return author notes and correspondence.",
    ),
    related_articles: bool = typer.Option(
        False,
        "--related-articles",
        help="Return related article metadata.",
    ),
    custom_metadata: bool = typer.Option(
        False,
        "--custom-metadata",
        help="Return custom PMC metadata.",
    ),
    abstract: bool = typer.Option(
        False,
        "--abstract",
        help="Return abstract text and structure.",
    ),
    content: bool = typer.Option(
        False,
        "--content",
        help="Return article sections, headings, paragraphs, and citation links.",
    ),
    acknowledgements: bool = typer.Option(
        False,
        "--acknowledgements",
        help="Return acknowledgements.",
    ),
    data_availability: bool = typer.Option(
        False,
        "--data-availability",
        help="Return data availability statements.",
    ),
    competing_interests: bool = typer.Option(
        False,
        "--competing-interests",
        help="Return competing interest statements.",
    ),
    supplementary_media: bool = typer.Option(
        False,
        "--supplementary-media",
        help="Return supplementary media links.",
    ),
    references: bool = typer.Option(
        False,
        "--references",
        help="Return bibliography references.",
    ),
    figures: bool = typer.Option(
        False,
        "--figures",
        help="Return figure captions and graphics.",
    ),
    tables: bool = typer.Option(
        False,
        "--tables",
        help="Return table captions and rows.",
    ),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        envvar="PMC_TOOLKIT_CACHE",
        help="Cache root containing <PMCid.N>/<PMCid.N>.xml.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print machine-readable JSON output.",
    ),
) -> None:
    """
    Parse a cached PMC full-text XML file.
    """
    result = _run_command(lambda: parse_cached_xml(requested_pmcid, cache_dir=cache_dir))
    selected_keys = [
        key
        for key, enabled in [
            ("source", source),
            ("title", title),
            ("journal", journal),
            ("article", article),
            ("affiliations", affiliations),
            ("author_notes", author_notes),
            ("related_articles", related_articles),
            ("custom_metadata", custom_metadata),
            ("abstract", abstract),
            ("content", content),
            ("acknowledgements", acknowledgements),
            ("data_availability", data_availability),
            ("competing_interests", competing_interests),
            ("supplementary_media", supplementary_media),
            ("references", references),
            ("figures", figures),
            ("tables", tables),
        ]
        if enabled
    ]
    output = select_parse_data(result.data, selected_keys)

    typer.echo(json.dumps(output, indent=2, ensure_ascii=False))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
