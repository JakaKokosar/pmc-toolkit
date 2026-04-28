import pytest

from pmc_toolkit.xml_parse_api import parse_cached_xml


def test_parse_cached_xml_reads_expected_file_from_cache(tmp_path) -> None:
    article_dir = tmp_path / "PMC11370360.1"
    article_dir.mkdir()
    (article_dir / "PMC11370360.1.xml").write_text(
        """
        <article>
          <front>
            <article-meta>
              <article-id pub-id-type="pmcid">PMC11370360</article-id>
              <title-group><article-title>Cached XML</article-title></title-group>
            </article-meta>
          </front>
          <body><sec><title>Intro</title></sec></body>
        </article>
        """,
        encoding="utf-8",
    )

    result = parse_cached_xml("PMC11370360.1", cache_dir=tmp_path)

    assert result.versioned_pmcid == "PMC11370360.1"
    assert result.xml_path == str(article_dir / "PMC11370360.1.xml")
    assert result.data["source"]["versioned_pmcid"] == "PMC11370360.1"
    assert result.data["title"] == "Cached XML"
    assert result.data["article"]["title"] == "Cached XML"
    assert result.data["content"]["headings"] == ["Intro"]


def test_parse_cached_xml_tells_user_to_fetch_first(tmp_path) -> None:
    with pytest.raises(ValueError, match=r"pmc fetch PMC11370360\.1 --ext xml"):
        parse_cached_xml("PMC11370360.1", cache_dir=tmp_path)
