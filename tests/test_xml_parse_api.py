import json

import pytest

from pmc_toolkit.xml_parse_api import ensure_extracted_article


def test_ensure_extracted_article_reads_xml_and_writes_extracted_cache(
    tmp_path,
) -> None:
    article_dir = tmp_path / "PMC11370360.1"
    article_dir.mkdir()
    (article_dir / "PMC11370360.1.xml").write_text(
        """
        <article article-type="research-article">
          <front>
            <journal-meta>
              <journal-title-group>
                <journal-title>bioRxiv</journal-title>
              </journal-title-group>
              <issn pub-type="epub">2692-8205</issn>
              <publisher>
                <publisher-name>Cold Spring Harbor Laboratory Preprints</publisher-name>
              </publisher>
            </journal-meta>
            <article-meta>
              <article-id pub-id-type="pmcid">PMC11370360</article-id>
              <article-id pub-id-type="pmid">39229047</article-id>
              <article-id pub-id-type="doi">10.1101/example</article-id>
              <title-group><article-title>Cached XML</article-title></title-group>
              <contrib-group>
                <contrib contrib-type="author">
                  <name>
                    <surname>Doe</surname>
                    <given-names>Jane</given-names>
                  </name>
                  <contrib-id contrib-id-type="orcid">http://orcid.org/0000</contrib-id>
                  <xref ref-type="aff" rid="aff1" />
                </contrib>
              </contrib-group>
              <aff id="aff1"><label>1</label>Department of Examples</aff>
              <abstract><p>Example abstract.</p></abstract>
              <pub-date pub-type="epub">
                <year>2024</year>
                <month>9</month>
                <day>20</day>
              </pub-date>
              <kwd-group><kwd>neuroprosthesis</kwd></kwd-group>
              <permissions>
                <license license-type="cc-by">
                  <license-p>Creative Commons</license-p>
                </license>
              </permissions>
              <funding-group>
                <award-group>
                  <institution>NIH</institution>
                  <award-id>1DP2DC021055</award-id>
                </award-group>
              </funding-group>
            </article-meta>
          </front>
          <body><sec><title>Intro</title></sec></body>
          <back>
            <ack id="ack1"><p>Thanks.</p></ack>
            <ref-list><ref id="R1"><label>1</label></ref></ref-list>
          </back>
        </article>
        """,
        encoding="utf-8",
    )

    result = ensure_extracted_article("PMC11370360.1", cache_dir=tmp_path)

    assert result.versioned_pmcid == "PMC11370360.1"
    assert result.xml_path == str(article_dir / "PMC11370360.1.xml")
    assert "_meta" not in result.data
    assert result.data["article_info"]["journal"]["name"] == "bioRxiv"
    assert result.data["article_info"]["journal"]["issn"] == "2692-8205"
    assert result.data["article_info"]["article_ids"] == {
        "doi": "10.1101/example",
        "pmid": "39229047",
        "pmcid": "PMC11370360",
    }
    assert result.data["article_info"]["title"] == "Cached XML"
    assert result.data["article_info"]["publication_date"] == "2024-09-20"
    assert result.data["article_info"]["article_type"] == "research-article"
    assert result.data["article_info"]["keywords"] == ["neuroprosthesis"]
    assert result.data["article_info"]["authors"][0]["affiliations"] == [
        "Department of Examples"
    ]
    assert result.data["article_info"]["abstract"] == "Example abstract."
    assert result.data["article_info"]["funding_grants"] == [
        {"institution": "NIH", "award_id": "1DP2DC021055"}
    ]
    assert result.data["content"]["sections"][0]["title"] == "Intro"
    assert "sections" not in result.data

    cache_path = article_dir / ".pmc-extracted-article.json"
    assert json.loads(cache_path.read_text(encoding="utf-8")) == result.data


def test_ensure_extracted_article_reads_existing_extracted_cache(tmp_path) -> None:
    article_dir = tmp_path / "PMC11370360.1"
    article_dir.mkdir()
    (article_dir / "PMC11370360.1.xml").write_text("<article />", encoding="utf-8")
    cached_data = {
        "_meta": {"versioned_pmcid": "PMC11370360.1"},
        "article_info": {"title": "Cached JSON"},
        "content": {},
        "references": [],
        "figures": [],
        "tables": [],
        "supporting_info": {},
    }
    (article_dir / ".pmc-extracted-article.json").write_text(
        json.dumps(cached_data),
        encoding="utf-8",
    )

    result = ensure_extracted_article("PMC11370360.1", cache_dir=tmp_path)

    assert result.data == cached_data


def test_ensure_extracted_article_tells_user_to_fetch_first(tmp_path) -> None:
    with pytest.raises(ValueError, match=r"pmc-toolkit fetch PMC11370360\.1 --ext xml"):
        ensure_extracted_article("PMC11370360.1", cache_dir=tmp_path)
