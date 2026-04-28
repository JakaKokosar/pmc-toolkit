from pathlib import Path

from typer.testing import CliRunner

from pmc_toolkit.cli import app
from pmc_toolkit.models import (
    FetchAction,
    PMCFetchFile,
    PMCFetchResult,
    PMCFiles,
    PMCMetadata,
    PMCParseResult,
    PMCVersions,
)

runner = CliRunner()


def test_help_shows_versions_subcommand() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "versions" in result.stdout
    assert "metadata" in result.stdout
    assert "files" in result.stdout
    assert "fetch" in result.stdout


def test_versions_subcommand_outputs_versions(monkeypatch) -> None:
    def fake_list_versions(pmcid: str) -> PMCVersions:
        assert pmcid == "PMC11370360"
        return PMCVersions(
            pmcid="PMC11370360",
            versions=["PMC11370360.1", "PMC11370360.2"],
        )

    monkeypatch.setattr("pmc_toolkit.cli.list_versions", fake_list_versions)

    result = runner.invoke(app, ["versions", "PMC11370360"])

    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["PMC11370360.1", "PMC11370360.2"]


def test_versions_subcommand_rejects_versioned_identifier() -> None:
    result = runner.invoke(app, ["versions", "PMC11370360.1"])

    assert result.exit_code == 2
    assert "expects a base PMCID" in result.stderr


def test_root_command_requires_subcommand() -> None:
    result = runner.invoke(app, ["PMC11370360"])

    assert result.exit_code == 2


def test_metadata_subcommand_uses_latest_version_by_default(monkeypatch) -> None:
    def fake_get_metadata(requested_pmcid: str) -> PMCMetadata:
        assert requested_pmcid == "PMC11370360"
        return PMCMetadata(
            pmcid="PMC11370360",
            version=2,
            pmid=123456,
            doi="10.1000/example",
            mid=None,
            title="Example title",
            citation="Example citation",
            is_pmc_openaccess=True,
            is_manuscript=False,
            is_historical_ocr=False,
            is_retracted=False,
            license_code="CC BY",
            xml_url="s3://pmc-oa-opendata/PMC11370360.2/PMC11370360.2.xml",
            pdf_url="s3://pmc-oa-opendata/PMC11370360.2/PMC11370360.2.pdf",
            media_urls=[],
            text_url="s3://pmc-oa-opendata/PMC11370360.2/PMC11370360.2.txt",
        )

    monkeypatch.setattr("pmc_toolkit.cli.get_metadata", fake_get_metadata)

    result = runner.invoke(app, ["metadata", "PMC11370360", "--json"])

    assert result.exit_code == 0
    assert '"pmcid": "PMC11370360"' in result.stdout
    assert '"version": 2' in result.stdout


def test_metadata_subcommand_accepts_explicit_version(monkeypatch) -> None:
    def fake_get_metadata(requested_pmcid: str) -> PMCMetadata:
        assert requested_pmcid == "PMC11370360.1"
        return PMCMetadata(
            pmcid="PMC11370360",
            version=1,
            pmid=None,
            doi=None,
            mid=None,
            title="Example title",
            citation="Example citation",
            is_pmc_openaccess=True,
            is_manuscript=False,
            is_historical_ocr=False,
            is_retracted=False,
            license_code=None,
            xml_url="s3://pmc-oa-opendata/PMC11370360.1/PMC11370360.1.xml",
            pdf_url=None,
            media_urls=[],
            text_url="s3://pmc-oa-opendata/PMC11370360.1/PMC11370360.1.txt",
        )

    monkeypatch.setattr("pmc_toolkit.cli.get_metadata", fake_get_metadata)

    result = runner.invoke(app, ["metadata", "PMC11370360.1"])

    assert result.exit_code == 0
    assert "pmcid: PMC11370360" in result.stdout
    assert "version: 1" in result.stdout


def test_files_subcommand_lists_keys(monkeypatch) -> None:
    captured = {}

    def fake_list_files(requested_pmcid: str):
        captured["requested_pmcid"] = requested_pmcid
        return PMCFiles(
            versioned_pmcid="PMC11370360.1",
            keys=[
                "PMC11370360.1/PMC11370360.1.xml",
                "PMC11370360.1/PMC11370360.1.pdf",
            ],
        )

    monkeypatch.setattr("pmc_toolkit.cli.list_files", fake_list_files)

    result = runner.invoke(app, ["files", "PMC11370360.1"])

    assert result.exit_code == 0
    assert captured == {"requested_pmcid": "PMC11370360.1"}
    assert "PMC11370360.1/PMC11370360.1.xml" in result.stdout
    assert "PMC11370360.1/PMC11370360.1.pdf" in result.stdout


def test_fetch_subcommand_invokes_storage_with_options(monkeypatch, tmp_path) -> None:
    captured = {}

    def fake_fetch(requested_pmcid, cache_dir=None, extensions=None, force=False):
        captured.update(
            requested_pmcid=requested_pmcid,
            cache_dir=cache_dir,
            extensions=extensions,
            force=force,
        )
        return PMCFetchResult(
            versioned_pmcid="PMC11370360.1",
            cache_dir=str(tmp_path / "PMC11370360.1"),
            files=[
                PMCFetchFile(
                    key="PMC11370360.1/PMC11370360.1.pdf",
                    local_path=str(tmp_path / "PMC11370360.1" / "PMC11370360.1.pdf"),
                    action=FetchAction.DOWNLOADED,
                )
            ],
        )

    monkeypatch.setattr("pmc_toolkit.cli.fetch_files", fake_fetch)

    result = runner.invoke(
        app,
        [
            "fetch",
            "PMC11370360.1",
            "--ext",
            "pdf",
            "--cache-dir",
            str(tmp_path),
            "--force",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert captured["requested_pmcid"] == "PMC11370360.1"
    assert captured["extensions"] == ["pdf"]
    assert captured["cache_dir"] == Path(str(tmp_path))
    assert captured["force"] is True
    assert "[downloaded]" in result.stdout


def test_fetch_subcommand_accepts_comma_separated_extensions(
    monkeypatch, tmp_path
) -> None:
    captured = {}

    def fake_fetch(requested_pmcid, cache_dir=None, extensions=None, force=False):
        captured.update(
            requested_pmcid=requested_pmcid,
            cache_dir=cache_dir,
            extensions=extensions,
            force=force,
        )
        return PMCFetchResult(
            versioned_pmcid="PMC11370360.2",
            cache_dir=str(tmp_path / "PMC11370360.2"),
            files=[],
        )

    monkeypatch.setattr("pmc_toolkit.cli.fetch_files", fake_fetch)

    result = runner.invoke(
        app,
        [
            "fetch",
            "PMC11370360.2",
            "--ext",
            "xml,pdf,jpg",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert captured["requested_pmcid"] == "PMC11370360.2"
    assert captured["extensions"] == ["xml,pdf,jpg"]


def test_parse_subcommand_outputs_selected_json(monkeypatch, tmp_path) -> None:
    def fake_parse(requested_pmcid, cache_dir=None):
        assert requested_pmcid == "PMC11370360.1"
        assert cache_dir == tmp_path
        return PMCParseResult(
            versioned_pmcid="PMC11370360.1",
            xml_path=str(tmp_path / "PMC11370360.1" / "PMC11370360.1.xml"),
            data={
                "source": {"versioned_pmcid": "PMC11370360.1"},
                "title": "Example title",
                "journal": {"title": "bioRxiv"},
                "article": {"title": "Example title", "authors": ["Jane Doe"]},
                "affiliations": [],
                "author_notes": {"notes": [], "correspondence": []},
                "related_articles": [],
                "custom_metadata": {},
                "abstract": {"text": "Example abstract"},
                "content": {
                    "headings": ["Introduction", "Methods"],
                    "sections": [
                        {
                            "source_id": "s1",
                            "paragraphs": [
                                {"source_id": "p1", "reference_ids": ["R1"]},
                            ],
                        },
                    ],
                },
                "acknowledgements": [],
                "data_availability": [],
                "competing_interests": [],
                "supplementary_media": [],
                "references": [],
                "figures": [],
                "tables": [],
            },
        )

    monkeypatch.setattr("pmc_toolkit.cli.parse_cached_xml", fake_parse)

    result = runner.invoke(
        app,
        [
            "parse",
            "PMC11370360.1",
            "--title",
            "--article",
            "--content",
            "--cache-dir",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert '"title": "Example title"' in result.stdout
    assert '"headings": [' in result.stdout
    assert '"source_id": "s1"' in result.stdout
    assert '"source_id": "p1"' in result.stdout
    assert '"reference_ids": [' in result.stdout
    assert '"id":' not in result.stdout
    assert "journal" not in result.stdout


def test_parse_subcommand_defaults_to_all_categories(monkeypatch) -> None:
    def fake_parse(requested_pmcid, cache_dir=None):
        return PMCParseResult(
            versioned_pmcid="PMC11370360.1",
            xml_path="/cache/PMC11370360.1/PMC11370360.1.xml",
            data={
                "source": {"versioned_pmcid": "PMC11370360.1"},
                "title": "Example title",
                "journal": {"title": "bioRxiv"},
                "article": {"title": "Example title"},
                "affiliations": [],
                "author_notes": {"notes": [], "correspondence": []},
                "related_articles": [],
                "custom_metadata": {},
                "abstract": {"text": "Example abstract"},
                "content": {"headings": ["Introduction"]},
                "acknowledgements": [],
                "data_availability": [],
                "competing_interests": [],
                "supplementary_media": [],
                "references": [],
                "figures": [],
                "tables": [],
            },
        )

    monkeypatch.setattr("pmc_toolkit.cli.parse_cached_xml", fake_parse)

    result = runner.invoke(app, ["parse", "PMC11370360.1"])

    assert result.exit_code == 0, result.stdout
    assert '"source": {' in result.stdout
    assert '"title": "Example title"' in result.stdout
    assert '"journal": {' in result.stdout
    assert '"article": {' in result.stdout
    assert '"affiliations": []' in result.stdout
    assert '"author_notes": {' in result.stdout
    assert '"related_articles": []' in result.stdout
    assert '"custom_metadata": {}' in result.stdout
    assert '"abstract": {' in result.stdout
    assert '"content": {' in result.stdout
    assert '"acknowledgements": []' in result.stdout
    assert '"data_availability": []' in result.stdout
    assert '"competing_interests": []' in result.stdout
    assert '"supplementary_media": []' in result.stdout
    assert '"references": []' in result.stdout
    assert '"figures": []' in result.stdout
    assert '"tables": []' in result.stdout


def test_files_subcommand_exits_with_code_1_on_unexpected_error(monkeypatch) -> None:
    def fake_list_files(requested_pmcid: str):
        raise RuntimeError("boom")

    monkeypatch.setattr("pmc_toolkit.cli.list_files", fake_list_files)

    result = runner.invoke(app, ["files", "PMC11370360.1"])

    assert result.exit_code == 1
    assert "Error: boom" in result.stderr
