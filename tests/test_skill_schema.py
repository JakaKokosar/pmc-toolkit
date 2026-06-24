"""Guard: keep the pmc-toolkit skill's documented parse schema in lockstep with the code.

The skill at ``skills/pmc-toolkit/SKILL.md`` ("The Parsed Schema Is Closed")
publishes a closed-world field dictionary the agent builds every jq projection
from. ``SCHEMA`` below mirrors it. The test parses a fixture that exercises every
documented field and asserts two directions:

* the parser never emits a key absent from the schema (undocumented drift), and
* every documented key is actually produced by the parser (phantom keys).

A failure here means the schema in SKILL.md and the parser have diverged and one
of them must be updated.
"""

from pmc_toolkit.xml_parse_api import ensure_extracted_article

# Allowed keys per object type, mirroring the SKILL.md closed-world schema.
# `custom_metadata` is a free-form name->value map and is checked structurally,
# not against a fixed key set.
SCHEMA: dict[str, set[str]] = {
    "root": {
        "article_info",
        "content",
        "references",
        "figures",
        "tables",
        "supporting_info",
    },
    "article_info": {
        "title",
        "abstract",
        "article_type",
        "publication_date",
        "article_ids",
        "journal",
        "license",
        "keywords",
        "authors",
        "funding_grants",
    },
    "article_ids": {"doi", "pmid", "pmcid"},
    "journal": {"name", "publisher", "issn"},
    "license": {"type", "url", "text"},
    "author": {"given_names", "surname", "full_name", "orcid", "affiliations"},
    "funding_grant": {"institution", "award_id"},
    "content": {"sections", "paragraphs"},
    "section": {"source_id", "section_id", "title", "paragraphs", "sections"},
    "section_like": {"source_id", "title", "paragraphs", "sections"},
    "para": {"source_id", "text", "reference_ids", "figure_ids", "table_ids"},
    "reference": {
        "source_id",
        "label",
        "text",
        "publication_type",
        "identifiers",
        "article_title",
        "source",
        "year",
        "volume",
        "issue",
        "pages",
    },
    "identifiers": {"doi", "pmid", "pmcid"},
    "figure": {"source_id", "label", "caption", "graphics"},
    "table": {"source_id", "label", "caption", "rows", "footnotes"},
    "supporting_info": {
        "acknowledgements",
        "competing_interests",
        "data_availability",
        "supplementary_media",
        "author_notes",
        "related_articles",
        "custom_metadata",
    },
    "competing_interest": {"source_id", "text"},
    "supplementary_media": {"source_id", "paragraphs", "links"},
    "media_paragraph": {"source_id", "text"},
    "link": {"href", "text", "type"},
    "author_notes": {"notes", "correspondence"},
    "note": {"source_id", "type", "label", "text"},
    "corresp": {"source_id", "text", "emails"},
    "related_article": {
        "type",
        "href",
        "title",
        "source",
        "volume",
        "issue",
        "pages",
        "date",
        "identifiers",
    },
}

# A single article exercising every documented branch of the parser so the guard
# sees each schema key at least once. Uses plain `href` (the parser matches both
# `href` and namespaced `*}href`).
ARTICLE_XML = """
<article article-type="research-article">
  <front>
    <journal-meta>
      <journal-title-group><journal-title>Example Journal</journal-title></journal-title-group>
      <issn pub-type="epub">2692-8205</issn>
      <publisher><publisher-name>Example Press</publisher-name></publisher>
    </journal-meta>
    <article-meta>
      <article-id pub-id-type="pmcid">PMC11370360</article-id>
      <article-id pub-id-type="pmid">39229047</article-id>
      <article-id pub-id-type="doi">10.1101/example</article-id>
      <title-group><article-title>Example Title</article-title></title-group>
      <contrib-group>
        <contrib contrib-type="author">
          <name><surname>Doe</surname><given-names>Jane</given-names></name>
          <contrib-id contrib-id-type="orcid">http://orcid.org/0000</contrib-id>
          <xref ref-type="aff" rid="aff1" />
        </contrib>
      </contrib-group>
      <aff id="aff1"><label>1</label>Department of Examples</aff>
      <author-notes>
        <fn id="fn1" fn-type="equal"><label>*</label><p>Equal contribution.</p></fn>
        <corresp id="cor1">Correspondence: <email>jane@example.org</email></corresp>
      </author-notes>
      <abstract><p>Example abstract.</p></abstract>
      <pub-date pub-type="epub"><year>2024</year><month>9</month><day>20</day></pub-date>
      <volume>42</volume>
      <issue>3</issue>
      <kwd-group><kwd>example</kwd></kwd-group>
      <permissions>
        <license license-type="cc-by">
          <license-p>Creative Commons.</license-p>
          <ext-link href="https://creativecommons.org/licenses/by/4.0/">CC BY</ext-link>
        </license>
      </permissions>
      <funding-group>
        <award-group><institution>NIH</institution><award-id>1DP2DC021055</award-id></award-group>
      </funding-group>
      <related-article related-article-type="companion" href="https://example.org/related">
        <article-title>Related Article</article-title>
        <source>Related Journal</source>
        <volume>3</volume>
        <issue>1</issue>
        <fpage>1</fpage>
        <lpage>9</lpage>
        <date><year>2019</year></date>
        <pub-id pub-id-type="doi">10.1101/related</pub-id>
      </related-article>
      <custom-meta-group>
        <custom-meta><meta-name>pmc-status</meta-name><meta-value>live</meta-value></custom-meta>
      </custom-meta-group>
    </article-meta>
  </front>
  <body>
    <p id="bp1">Body-level paragraph outside any section.</p>
    <sec id="s1">
      <title>Introduction</title>
      <p id="p1">Text citing <xref ref-type="bibr" rid="R1">1</xref>,
        <xref ref-type="fig" rid="F1">Fig 1</xref>, and
        <xref ref-type="table" rid="T1">Table 1</xref>.</p>
      <sec id="s1a"><title>Background</title><p>Subsection prose.</p></sec>
    </sec>
    <fig id="F1">
      <label>Figure 1</label>
      <caption><p>Figure caption.</p></caption>
      <graphic href="example-g001.jpg" />
    </fig>
    <table-wrap id="T1">
      <label>Table 1</label>
      <caption><p>Table caption.</p></caption>
      <table><tr><th>Header</th></tr><tr><td>Cell</td></tr></table>
      <table-wrap-foot><fn><p>Table footnote.</p></fn></table-wrap-foot>
    </table-wrap>
  </body>
  <back>
    <ack id="ack1">
      <title>Acknowledgements</title>
      <p>We thank the reviewers.</p>
      <sec id="acks1"><title>Author contributions</title><p>JD wrote the paper.</p></sec>
    </ack>
    <fn fn-type="COI-statement" id="coi1"><p>The authors declare no competing interests.</p></fn>
    <fn id="sm1">
      <p id="smp1">Supplementary material is available online.</p>
      <ext-link href="https://example.org/supp" ext-link-type="uri">Supplement</ext-link>
    </fn>
    <sec sec-type="data-availability" id="da1">
      <title>Data availability</title>
      <p>Data are available in the example repository.</p>
    </sec>
    <ref-list>
      <ref id="R1">
        <label>1</label>
        <mixed-citation publication-type="journal">
          <article-title>Referenced Article</article-title>
          <source>Reference Journal</source>
          <year>2020</year>
          <volume>5</volume>
          <issue>2</issue>
          <fpage>10</fpage>
          <lpage>20</lpage>
          <pub-id pub-id-type="doi">10.1234/ref</pub-id>
          <pub-id pub-id-type="pmid">23193287</pub-id>
          <pub-id pub-id-type="pmcid">PMC3531190</pub-id>
        </mixed-citation>
      </ref>
    </ref-list>
  </back>
</article>
"""


def _check(obj: object, type_name: str, seen: dict[str, set[str]]) -> None:
    assert isinstance(obj, dict), f"{type_name} should be an object, got {type(obj)}"
    extra = set(obj) - SCHEMA[type_name]
    assert not extra, (
        f"{type_name} has undocumented key(s) {sorted(extra)}; "
        f"update the closed-world schema in skills/pmc-toolkit/SKILL.md"
    )
    seen.setdefault(type_name, set()).update(obj)


def _walk_section(section: dict, type_name: str, seen: dict[str, set[str]]) -> None:
    _check(section, type_name, seen)
    for paragraph in section.get("paragraphs", []):
        _check(paragraph, "para", seen)
    child_type = "section" if type_name == "section" else "section_like"
    for child in section.get("sections", []):
        _walk_section(child, child_type, seen)


def test_parse_output_matches_documented_skill_schema(tmp_path) -> None:
    article_dir = tmp_path / "PMC11370360.1"
    article_dir.mkdir()
    (article_dir / "PMC11370360.1.xml").write_text(ARTICLE_XML, encoding="utf-8")

    data = ensure_extracted_article("PMC11370360.1", cache_dir=tmp_path).data
    seen: dict[str, set[str]] = {}

    assert set(data) == SCHEMA["root"]
    seen["root"] = set(data)

    info = data["article_info"]
    _check(info, "article_info", seen)
    _check(info["article_ids"], "article_ids", seen)
    _check(info["journal"], "journal", seen)
    _check(info["license"], "license", seen)
    for author in info["authors"]:
        _check(author, "author", seen)
    for grant in info["funding_grants"]:
        _check(grant, "funding_grant", seen)

    content = data["content"]
    _check(content, "content", seen)
    for section in content["sections"]:
        _walk_section(section, "section", seen)
    for paragraph in content.get("paragraphs", []):
        _check(paragraph, "para", seen)

    for reference in data["references"]:
        _check(reference, "reference", seen)
        if "identifiers" in reference:
            _check(reference["identifiers"], "identifiers", seen)
    for figure in data["figures"]:
        _check(figure, "figure", seen)
    for table in data["tables"]:
        _check(table, "table", seen)

    support = data["supporting_info"]
    _check(support, "supporting_info", seen)
    for ack in support["acknowledgements"]:
        _walk_section(ack, "section_like", seen)
    for statement in support["competing_interests"]:
        _check(statement, "competing_interest", seen)
    for section in support["data_availability"]:
        _walk_section(section, "section_like", seen)
    for media in support["supplementary_media"]:
        _check(media, "supplementary_media", seen)
        for paragraph in media.get("paragraphs", []):
            _check(paragraph, "media_paragraph", seen)
        for link in media.get("links", []):
            _check(link, "link", seen)
    notes = support["author_notes"]
    _check(notes, "author_notes", seen)
    for note in notes["notes"]:
        _check(note, "note", seen)
    for corresp in notes["correspondence"]:
        _check(corresp, "corresp", seen)
    for related in support["related_articles"]:
        _check(related, "related_article", seen)
        if "identifiers" in related:
            _check(related["identifiers"], "identifiers", seen)
    assert isinstance(support["custom_metadata"], dict)
    assert support["custom_metadata"], "fixture should populate custom_metadata"

    # Every documented key must be produced by the parser for the fixture above;
    # an unseen key means the schema lists a field the code no longer emits.
    for type_name, allowed in SCHEMA.items():
        missing = allowed - seen.get(type_name, set())
        assert not missing, (
            f"{type_name} documents key(s) {sorted(missing)} the parser did not "
            f"emit; the fixture or the SKILL.md schema is stale"
        )
