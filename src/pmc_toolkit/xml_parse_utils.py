"""XML extraction helpers for cached PMC full-text articles."""

from pathlib import Path
from typing import Any

import lxml.etree as etree  # ty: ignore[unresolved-import]

XMLParser = etree.XMLParser(
    load_dtd=False,
    no_network=True,
    resolve_entities=False,
    remove_blank_text=True,
)


def load_xml(path: Path) -> Any:
    root = etree.parse(str(path), parser=XMLParser).getroot()
    _strip_namespaces(root)
    return root


def extract_article_data(root: Any) -> dict[str, Any]:
    article = extract_article(root)
    return {
        "title": article.get("title"),
        "journal": extract_journal(root),
        "article": article,
        "affiliations": extract_affiliations(root),
        "author_notes": extract_author_notes(root),
        "related_articles": extract_related_articles(root),
        "custom_metadata": extract_custom_metadata(root),
        "abstract": extract_abstract(root),
        "content": extract_content(root),
        "acknowledgements": extract_acknowledgements(root),
        "data_availability": extract_data_availability(root),
        "competing_interests": extract_competing_interests(root),
        "supplementary_media": extract_supplementary_media(root),
        "references": extract_references(root),
        "figures": extract_figures(root),
        "tables": extract_tables(root),
    }


def extract_journal(root: Any) -> dict[str, Any]:
    journal_meta = root.find(".//journal-meta")
    journal: dict[str, Any] = {
        "identifiers": {},
        "title": None,
        "issn": {},
        "publisher": {},
    }
    if journal_meta is None:
        return journal

    identifiers = _extract_typed_texts(journal_meta, ".//journal-id", "journal-id-type")
    journal["identifiers"] = identifiers
    journal["title"] = _first_text(journal_meta, ".//journal-title")
    journal["abbreviated_title"] = _first_text(journal_meta, ".//abbrev-journal-title")
    journal["issn"] = _extract_typed_texts(journal_meta, ".//issn", "pub-type")

    publisher = {
        "name": _first_text(journal_meta, ".//publisher/publisher-name"),
        "location": _first_text(journal_meta, ".//publisher/publisher-loc"),
    }
    journal["publisher"] = _compact_dict(publisher)
    return _compact_dict(journal, keep_empty={"identifiers", "issn", "publisher"})


def extract_article(root: Any) -> dict[str, Any]:
    article_meta = root.find(".//article-meta")
    article: dict[str, Any] = {
        "identifiers": {},
        "type": root.get("article-type"),
        "language": _xml_lang(root),
        "title": None,
        "authors": [],
        "publication_dates": [],
        "volume": None,
        "issue": None,
        "pages": None,
        "keywords": [],
        "categories": {},
        "permissions": {},
    }
    if article_meta is None:
        return _compact_dict(
            article,
            keep_empty={
                "identifiers",
                "authors",
                "publication_dates",
                "keywords",
                "categories",
                "permissions",
            },
        )

    article["identifiers"] = _extract_typed_texts(
        article_meta, ".//article-id", "pub-id-type"
    )
    article["title"] = _first_text(article_meta, ".//title-group/article-title")
    article["authors"] = _extract_authors(article_meta)
    article["publication_dates"] = _extract_pub_dates(article_meta)
    article["volume"] = _first_text(article_meta, ".//volume")
    article["issue"] = _first_text(article_meta, ".//issue")
    article["pages"] = _page_range(article_meta)
    article["keywords"] = _texts(article_meta, ".//kwd")
    article["categories"] = _extract_categories(root)

    permissions = _extract_permissions(article_meta)
    if permissions:
        article["permissions"] = permissions

    funding = _extract_funding(article_meta)
    if funding:
        article["funding"] = funding

    return _compact_dict(
        article,
        keep_empty={
            "identifiers",
            "authors",
            "publication_dates",
            "keywords",
            "categories",
            "permissions",
        },
    )


def extract_abstract(root: Any) -> dict[str, Any]:
    abstract = root.find(".//article-meta/abstract")
    if abstract is None:
        abstract = root.find(".//abstract")
    if abstract is None:
        return {"text": None, "sections": []}

    return {
        "text": _text(abstract),
        "sections": [
            _abstract_section_data(section) for section in abstract.xpath("./sec")
        ],
    }


def extract_affiliations(root: Any) -> list[dict[str, Any]]:
    affiliations = []
    for affiliation in root.xpath(".//article-meta/aff"):
        label = _direct_child_text(affiliation, "label")
        text = _without_label(_text(affiliation), label)
        affiliations.append(
            _compact_dict(
                {
                    "source_id": affiliation.get("id"),
                    "label": label,
                    "text": text,
                }
            )
        )
    return affiliations


def extract_author_notes(root: Any) -> dict[str, Any]:
    author_notes = root.find(".//article-meta/author-notes")
    if author_notes is None:
        return {"notes": [], "correspondence": []}

    notes = []
    for note in author_notes.xpath("./fn"):
        label = _direct_child_text(note, "label")
        notes.append(
            _compact_dict(
                {
                    "source_id": note.get("id"),
                    "type": note.get("fn-type"),
                    "label": label,
                    "text": _without_label(_text(note), label),
                }
            ),
        )

    correspondence = []
    for corresp in author_notes.xpath("./corresp"):
        correspondence.append(
            _compact_dict(
                {
                    "source_id": corresp.get("id"),
                    "text": _text(corresp),
                    "emails": _texts(corresp, ".//email"),
                },
                keep_empty={"emails"},
            )
        )

    return {"notes": notes, "correspondence": correspondence}


def extract_related_articles(root: Any) -> list[dict[str, Any]]:
    related_articles = []
    for related in root.xpath(".//article-meta/related-article"):
        related_articles.append(
            _compact_dict(
                {
                    "type": related.get("related-article-type"),
                    "href": _href(related),
                    "title": _first_text(related, ".//article-title"),
                    "source": _first_text(related, ".//source"),
                    "volume": _first_text(related, ".//volume"),
                    "issue": _first_text(related, ".//issue"),
                    "pages": _page_range(related),
                    "date": _date_value(_first_element(related, "date")),
                    "identifiers": _extract_typed_texts(related, ".//pub-id", "pub-id-type"),
                },
                keep_empty={"identifiers"},
            )
        )
    return related_articles


def extract_custom_metadata(root: Any) -> dict[str, str]:
    metadata = {}
    for custom_meta in root.xpath(".//article-meta/custom-meta-group/custom-meta"):
        name = _first_text(custom_meta, "./meta-name")
        value = _first_text(custom_meta, "./meta-value")
        if name and value:
            metadata[name] = value
    return metadata


def extract_content(root: Any) -> dict[str, Any]:
    body = root.find(".//body")
    if body is None:
        return {"headings": [], "paragraphs": [], "sections": []}

    sections = [_section_data(section) for section in body.xpath("./sec")]
    return {
        "headings": _section_headings(sections),
        "paragraphs": [_paragraph_data(paragraph) for paragraph in body.xpath("./p")],
        "sections": sections,
    }


def extract_acknowledgements(root: Any) -> list[dict[str, Any]]:
    acknowledgements = []
    for ack in root.xpath(".//back/ack"):
        acknowledgements.append(
            _compact_dict(
                {
                    "source_id": ack.get("id"),
                    "title": _direct_child_text(ack, "title"),
                    "paragraphs": [_paragraph_data(paragraph) for paragraph in ack.xpath("./p")],
                    "sections": [_section_data(section) for section in ack.xpath("./sec")],
                },
                keep_empty={"paragraphs", "sections"},
            )
        )
    return acknowledgements


def extract_data_availability(root: Any) -> list[dict[str, Any]]:
    sections = []
    for section in root.xpath(".//back/sec[@sec-type='data-availability']"):
        sections.append(_section_data(section))
    return sections


def extract_competing_interests(root: Any) -> list[dict[str, Any]]:
    statements = []
    for note in root.xpath(".//back//fn[@fn-type='COI-statement']"):
        statements.append(
            _compact_dict(
                {
                    "source_id": note.get("id"),
                    "text": _text(note),
                }
            )
        )
    return statements


def extract_supplementary_media(root: Any) -> list[dict[str, Any]]:
    media = []
    for note in root.xpath(".//back//fn[not(@fn-type='COI-statement')]"):
        links = [_link_data(link) for link in note.xpath(".//ext-link")]
        media.append(
            _compact_dict(
                {
                    "source_id": note.get("id"),
                    "paragraphs": [
                        _compact_dict(
                            {
                                "source_id": paragraph.get("id"),
                                "text": _text(paragraph),
                            }
                        )
                        for paragraph in note.xpath("./p")
                    ],
                    "links": [link for link in links if link],
                },
                keep_empty={"paragraphs", "links"},
            )
        )
    return media


def extract_references(root: Any) -> list[dict[str, Any]]:
    references = []
    for ref in root.xpath(".//ref-list//ref"):
        citation = _first_element(ref, "mixed-citation", "element-citation", "citation")
        data: dict[str, Any] = {
            "source_id": ref.get("id"),
            "label": _direct_child_text(ref, "label"),
            "text": _text(citation) if citation is not None else _text(ref),
        }
        if citation is not None:
            publication_type = citation.get("publication-type")
            if publication_type:
                data["publication_type"] = publication_type

            ids = _extract_typed_texts(citation, ".//pub-id", "pub-id-type")
            if ids:
                data["identifiers"] = ids

            fields = _compact_dict(
                {
                    "article_title": _first_text(citation, ".//article-title"),
                    "source": _first_text(citation, ".//source"),
                    "year": _first_text(citation, ".//year"),
                    "volume": _first_text(citation, ".//volume"),
                    "issue": _first_text(citation, ".//issue"),
                    "pages": _page_range(citation),
                }
            )
            data.update(fields)

        references.append(_compact_dict(data))
    return references


def extract_figures(root: Any) -> list[dict[str, Any]]:
    figures = []
    for figure in root.xpath(".//fig"):
        figures.append(
            _compact_dict(
                {
                    "source_id": figure.get("id"),
                    "label": _direct_child_text(figure, "label"),
                    "caption": _first_text(figure, "./caption"),
                    "graphics": [_href(graphic) for graphic in figure.xpath(".//graphic")],
                },
                keep_empty={"graphics"},
            )
        )
    return figures


def extract_tables(root: Any) -> list[dict[str, Any]]:
    tables = []
    for table_wrap in root.xpath(".//table-wrap"):
        table = _first_element(table_wrap, "table")
        data = {
            "source_id": table_wrap.get("id"),
            "label": _direct_child_text(table_wrap, "label"),
            "caption": _first_text(table_wrap, "./caption"),
            "rows": _table_rows(table) if table is not None else [],
            "footnotes": _texts(table_wrap, ".//table-wrap-foot//fn"),
        }
        tables.append(_compact_dict(data, keep_empty={"rows", "footnotes"}))
    return tables


def extract_metadata(root: Any) -> dict[str, Any]:
    """Compatibility wrapper for the normalized article metadata category."""

    return extract_article(root)


def extract_headings(root: Any) -> list[str]:
    return extract_content(root)["headings"]


def _strip_namespaces(root: Any) -> None:
    for element in root.iter():
        if not isinstance(element.tag, str):
            continue
        if element.tag.startswith("{"):
            element.tag = element.tag.rsplit("}", 1)[1]
    etree.cleanup_namespaces(root)


def _xml_lang(element: Any) -> str | None:
    for key, value in element.attrib.items():
        if key == "lang" or key.endswith("}lang"):
            return value
    return None


def _text(element: Any | None) -> str | None:
    if element is None:
        return None
    value = " ".join(part.strip() for part in element.itertext() if part.strip())
    return value or None


def _first_text(root: Any, *paths: str) -> str | None:
    for path in paths:
        matches = root.xpath(path)
        for match in matches:
            if isinstance(match, etree._Element):
                value = _text(match)
            else:
                value = str(match).strip()
            if value:
                return value
    return None


def _direct_child_text(root: Any, name: str) -> str | None:
    child = root.find(name)
    return _text(child)


def _texts(root: Any, path: str) -> list[str]:
    values = []
    for element in root.xpath(path):
        if isinstance(element, etree._Element):
            value = _text(element)
            if value:
                values.append(value)
    return values


def _first_element(root: Any, *names: str) -> Any | None:
    for name in names:
        element = root.find(name)
        if element is not None:
            return element
    return None


def _extract_typed_texts(root: Any, path: str, type_attribute: str) -> dict[str, str]:
    values = {}
    for element in root.xpath(path):
        value_type = element.get(type_attribute)
        value = _text(element)
        if value_type and value:
            values[value_type] = value
    return values


def _extract_authors(article_meta: Any) -> list[dict[str, Any]]:
    authors = []
    for contrib in article_meta.xpath(".//contrib-group/contrib[@contrib-type='author']"):
        collaboration = _first_text(contrib, ".//collab")
        surname = _first_text(contrib, ".//name/surname")
        given_names = _first_text(contrib, ".//name/given-names")
        name = collaboration or " ".join(part for part in [given_names, surname] if part)

        author = {
            "name": name or None,
            "given_names": given_names,
            "surname": surname,
            "collaboration": collaboration,
            "orcid": _first_text(contrib, ".//contrib-id[@contrib-id-type='orcid']"),
            "affiliation_ids": [
                rid
                for xref in contrib.xpath(".//xref[@ref-type='aff']")
                if (rid := xref.get("rid"))
            ],
        }
        authors.append(_compact_dict(author, keep_empty={"affiliation_ids"}))
    return authors


def _extract_pub_dates(article_meta: Any) -> list[dict[str, str]]:
    dates = []
    for date in article_meta.xpath(".//pub-date"):
        value = _date_value(date)
        if not value:
            continue

        data = {"date": value}
        date_type = date.get("pub-type") or date.get("date-type")
        if date_type:
            data["type"] = date_type
        dates.append(data)
    return dates


def _date_value(date: Any | None) -> str | None:
    if date is None:
        return None
    parts = _compact_dict(
        {
            "year": _first_text(date, "year"),
            "month": _zero_pad(_first_text(date, "month")),
            "day": _zero_pad(_first_text(date, "day")),
        }
    )
    value = "-".join(parts[key] for key in ["year", "month", "day"] if key in parts)
    return value or None


def _zero_pad(value: str | None) -> str | None:
    return value.zfill(2) if value and value.isdigit() else value


def _page_range(root: Any) -> str | None:
    first = _first_text(root, ".//fpage", ".//first-page")
    last = _first_text(root, ".//lpage", ".//last-page")
    if first and last:
        return f"{first}-{last}"
    return first


def _extract_categories(root: Any) -> dict[str, Any]:
    categories: dict[str, Any] = {}
    article_type = root.get("article-type")
    if article_type:
        categories["article_type"] = article_type

    subject_groups = []
    for group in root.xpath(".//article-meta//subj-group"):
        subjects = _texts(group, ".//subject")
        if not subjects:
            continue
        data: dict[str, Any] = {"subjects": subjects}
        group_type = group.get("subj-group-type")
        if group_type:
            data["type"] = group_type
        subject_groups.append(data)

    if subject_groups:
        categories["subject_groups"] = subject_groups
    return categories


def _extract_permissions(article_meta: Any) -> dict[str, Any]:
    permissions = {}
    license_element = article_meta.find(".//license")
    if license_element is not None:
        license_data = {
            "type": license_element.get("license-type"),
            "url": next(
                (
                    href
                    for link in license_element.xpath(".//ext-link")
                    if (href := _href(link))
                ),
                None,
            ),
            "text": _first_text(license_element, ".//license-p"),
        }
        permissions["license"] = _compact_dict(license_data)
    return _compact_dict(permissions)


def _extract_funding(article_meta: Any) -> list[dict[str, Any]]:
    awards = []
    for award_group in article_meta.xpath(".//funding-group//award-group"):
        awards.append(
            _compact_dict(
                {
                    "institution": _first_text(award_group, ".//institution"),
                    "award_id": _first_text(award_group, ".//award-id"),
                }
            )
        )
    return [award for award in awards if award]


def _section_data(section: Any) -> dict[str, Any]:
    data = {
        "source_id": section.get("id"),
        "title": _direct_child_text(section, "title"),
        "paragraphs": [_paragraph_data(paragraph) for paragraph in section.xpath("./p")],
        "sections": [_section_data(child) for child in section.xpath("./sec")],
    }
    return _compact_dict(data, keep_empty={"paragraphs", "sections"})


def _abstract_section_data(section: Any) -> dict[str, Any]:
    paragraphs = _texts(section, "./p")
    text = " ".join(paragraphs) if paragraphs else _text(section)
    return _compact_dict(
        {
            "title": _direct_child_text(section, "title"),
            "text": text,
        }
    )


def _paragraph_data(paragraph: Any) -> dict[str, Any]:
    data = {
        "source_id": paragraph.get("id"),
        "text": _text(paragraph),
        "reference_ids": _xref_targets(paragraph, "bibr"),
        "figure_ids": _xref_targets(paragraph, "fig"),
        "table_ids": _xref_targets(paragraph, "table"),
    }
    return _compact_dict(
        data,
        keep_empty={"reference_ids", "figure_ids", "table_ids"},
    )


def _xref_targets(element: Any, ref_type: str) -> list[str]:
    ids = []
    for xref in element.xpath(".//xref[@ref-type=$ref_type]", ref_type=ref_type):
        rid = xref.get("rid")
        if rid:
            ids.extend(part for part in rid.split() if part)
    return ids


def _section_headings(sections: list[dict[str, Any]]) -> list[str]:
    headings = []
    for section in sections:
        title = section.get("title")
        if isinstance(title, str) and title:
            headings.append(title)
        nested = section.get("sections", [])
        if isinstance(nested, list):
            headings.extend(_section_headings(nested))
    return headings


def _href(element: Any) -> str | None:
    for key, value in element.attrib.items():
        if key == "href" or key.endswith("}href"):
            return value
    return None


def _link_data(element: Any) -> dict[str, Any]:
    return _compact_dict(
        {
            "href": _href(element),
            "text": _text(element),
            "type": element.get("ext-link-type"),
        }
    )


def _without_label(value: str | None, label: str | None) -> str | None:
    if not value or not label:
        return value
    clean = value.removeprefix(label).strip()
    return clean or value


def _table_rows(table: Any) -> list[list[str]]:
    rows = []
    for row in table.xpath(".//tr"):
        cells = []
        for cell in row.xpath("./th|./td"):
            value = _text(cell)
            if value:
                cells.append(value)
        if cells:
            rows.append(cells)
    return rows


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
