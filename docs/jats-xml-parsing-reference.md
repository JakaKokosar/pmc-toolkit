# PMC / JATS full-text XML: parsing libraries reference

Short comparison of **[pyEuropePMC](https://github.com/JonasHeinickeBio/pyEuropePMC)** and **[pubmed_parser](https://github.com/titipata/pubmed_parser)** for full-text XML, plus the usual document shape.

---

## What these XML files are

PubMed Central full-text articles are typically **JATS** (Journal Article Tag Suite), often the **archiving** variant with optional **MathML**.

Declared DOCTYPE example:

```xml
<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Archiving and Interchange DTD with MathML3 ...">
```

Root element **`article`** often carries `article-type`, `xml:lang`, `dtd-version`.

### Typical structure

| Region   | Role |
|---------|------|
| **`front`** | `journal-meta`, `article-meta` (IDs, title, authors, abstract, dates, categories). |
| **`body`**  | Narrative: nested **`sec`**, **`p`**, **`fig`**, **`table-wrap`**, **`xref`**. |
| **`back`**  | **`ref-list`**, appendices, etc. |

**Identifiers** are usually **`article-id`** elements with **`pub-id-type`** such as `pmcid`, `pmcid-ver`, `doi`, `pmid`.

OA bulk files may use **namespaced** tags; some parsers strip namespaces so XPath stays simple.

---

## pyEuropePMC

- **Repo**: https://github.com/JonasHeinickeBio/pyEuropePMC  
- **Purpose**: Europe PMC API toolkit plus **full-text XML parsing**, plaintext/markdown export, tables, metadata, optional RDF pipeline.

### Parsing stack

- **`FullTextXMLParser`** parses strings with **`defusedxml.ElementTree`** (safer than raw `ElementTree` on untrusted XML).
- **`ElementPatterns` / `DocumentSchema`**: configurable JATS-like patterns for odd articles.
- **Lazy sub-parsers**: authors, affiliations, metadata, references, tables, figures, sections; plaintext and markdown converters.

### Outputs

| Feature | Approach |
|---------|-----------|
| **Plain text** | `PlaintextConverter.to_plaintext()` — title, authors, abstract, body sections, acknowledgments / appendices / glossary where configured. |
| **Markdown** | `MarkdownConverter.to_markdown()` — `#` title, bold authors, metadata block, `## Abstract`, then body **`sec`** with `_process_section_markdown`. |
| **Tables** | `TableParser` on `.//table-wrap`: label, caption, footer, **`colgroup`**, first **`table`**, headers + rows. |
| **Sections** | `SectionParser`: **`body`** → **`sec`**, **direct child `p` only** per section (avoids duplicating nested subsections). |
| **References** | `ReferenceParser`; optional in-text citations via **`xref`** (`ref-type="bibr"`). |

Namespaces **`xlink`** / **`mml`** (MathML) are accounted for in the parser API.

---

## pubmed_parser

- **Repo**: https://github.com/titipata/pubmed_parser  
- **Purpose**: Lightweight **`lxml`** parsers for **PubMed OA subset**, MEDLINE XML, some E-utilities helpers — geared toward **dict/list outputs** for NLP pipelines.

### Parsing stack

- **`read_xml`**: `lxml.etree.parse` or `fromstring`; for `.nxml` / `nxml=True`, **`remove_namespace`** strips `{uri}local` tags.
- Text often uses **`itertext()`** or **`stringify_children`** (join meaningful text nodes).

### Main functions (OA full-text)

| Function | Output |
|----------|--------|
| **`parse_pubmed_xml`** | One dict: title, abstract, journal, pmid/pmc/doi, authors + affiliation keys, dates, subjects, COI, … |
| **`parse_pubmed_paragraph`** | List of dicts: `text`, `section`, `reference_ids` per **`//body//p`**. |
| **`parse_pubmed_table`** | List of dicts: caption, label, `table_columns`, `table_values`, optional `table_xml`. Marked **WIP** in docs — builds columns from **`thead/tr`**, rows from **`tbody/tr/td`**, skips inconsistent rows. |
| **`parse_pubmed_references`** / **`parse_pubmed_caption`** | References and figures. |

**No built-in Markdown** — concatenate paragraphs or format yourself. **`unidecode`** used in table cells for ASCII normalization.

---

## Comparison table

| Aspect | pyEuropePMC | pubmed_parser |
|--------|-------------|----------------|
| XML library | `defusedxml` + `xml.etree` | `lxml` |
| Plaintext / Markdown | `to_plaintext()`, `to_markdown()` | No — roll your own from structures |
| Metadata | `extract_metadata()` etc. | `parse_pubmed_xml` dict |
| Tables | Richer (`table-wrap` + footer/colgroup) | `thead`/`tbody` heuristic; WIP |
| Namespaces | Documented (xlink/MathML) | Stripping optional for `.nxml` |

---

## Extra references

- pyEuropePMC **XML coverage / benchmarks**: `docs/xml_element_coverage_analysis.md` in their repo.  
- MEDLINE/PubMed **DTD** (different shape than full-text JATS, overlaps at metadata): see pubmed_parser wiki/docs or NLM documentation.

---

## Example PMC artifact (`PMC11370360.2`)

Illustrative JATS clues: **JATS archive + MathML3** DTD, `processing-meta` / `restricted-by` PMC, **`journal-meta`** (e.g. bioRxiv), **`article-meta`** with **`pub-id-type="pmcid-ver"`** (e.g. `PMC11370360.2`) for **versioned** PMC identifiers.

Many PMC downloads are **minified** (very long lines); **structure is in the element tree**, not in whitespace.

## Toolkit output shape

The toolkit should not expose raw JATS container names like `body` or `back` as
the main public API. Parse cached XML into readable categories instead:
`title`, `journal`, `article`, `affiliations`, `author_notes`,
`related_articles`, `custom_metadata`, `abstract`, `content`,
`acknowledgements`, `data_availability`, `competing_interests`,
`supplementary_media`, `references`, `figures`, and `tables`. This keeps the
default output comprehensive without turning it into a lossless XML-to-dict dump
of every tag and wrapper element.
