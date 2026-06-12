from collections.abc import Callable
import json
from pathlib import Path
from typing import Any, TypeVar

import typer

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
        from pmc_toolkit.storage_api import list_versions
        from pmc_toolkit.validators import parse_pmcid

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
        from pmc_toolkit.storage_api import get_metadata

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
        from pmc_toolkit.storage_api import list_files

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
        from pmc_toolkit.storage_api import fetch_files

        return fetch_files(
            requested_pmcid,
            cache_dir=cache_dir,
            extensions=extensions,
            force=force,
        )

    result = _run_command(build_result)
    _emit_json(result.model_dump(mode="json"))


@app.command("convert-xml")
def convert_xml(
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
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Recreate the extracted JSON cache from the cached XML.",
    ),
) -> None:
    """
    Convert cached PMC full-text XML into cached extracted JSON.
    """

    def build_result():
        from pmc_toolkit.xml_parse_api import ensure_extracted_article

        return ensure_extracted_article(
            requested_pmcid,
            cache_dir=cache_dir,
            force=force,
        )

    result = _run_command(build_result)
    _emit_json(result.data)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
