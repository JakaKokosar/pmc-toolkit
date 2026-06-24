---
name: pmc-toolkit
description: Work with PubMed Central Open Access articles by PMCID using PMC Toolkit. Use for version resolution, metadata and file inventory, downloads, parsed article evidence extraction, authors and contributor analysis, figures, tables, references, supplements, declarations, knowledge extraction, and report-style summaries. Can convert PMID/DOI to PMCID only to continue PMC full-text workflows; not for keyword literature search or non-PMC article analysis.
---

# PMC Toolkit

Use this skill to retrieve, download, parse, and cite PMC Open Access article data with PMC Toolkit. Select commands by the data needed to complete the task, not by surface wording in the request.

## Operating Rules

- Run published-tool commands as `uvx pmc-toolkit ...`.
- Do not add installation guidance. If `uv`/`uvx` is unavailable, report that PMC Toolkit needs it and stop.
- Live lookups, listings, and downloads need network access to the PMC Open Access S3 dataset unless the data is already cached.
- For `metadata`, `files`, `fetch`, and `parse`, pass the requested PMCID directly. Base PMCIDs resolve to the latest version; resolve a version only for version-specific tasks.
- `parse` needs cached XML: run `fetch <PMCID> --ext xml` first when XML is absent.
- Resolve bundled helper paths relative to this skill directory, e.g. `<SKILL_DIR>/scripts/content-outline.jq`.
- Never load, dump, grep, or search raw XML or PDF files for content tasks. Fetch XML only as parser input, then work from `parse` output.
- Do not invent missing data (declarations, author notes, figures, tables, references). Report the missing field or empty list.
- For extraction requests where the command output is already the answer, do not restate large text in your reply. Return a brief label or status; for long abstracts, tables, or lists, tell the user the command printed the value instead of repeating it.

## The Parsed Schema Is Closed — Build Every jq From It, Never From Memory

The schema below is the **complete and exhaustive** field dictionary of `parse` output, derived from the parser source. It is **closed-world**: a field name that does not appear here **does not exist** — never project it, never guess it. The recurring failure this prevents is inventing a plausible-sounding key (`heading`, `name`, `body`, `content.text`) that the parser never emits. When you need a field, copy its exact name and path from this schema.

This static schema is **not** a substitute for `content-outline.jq`. The schema tells you a section object has a `title` and a `source_id`; the outline tells you **this article's** actual titles and `source_id` values. The schema never changes between articles and is always in context here; the outline must be run for every article to discover its real ids. Use the schema to know *what a field is called*, the outline to know *what this paper contains*.

Notation: `?` marks an optional field — the parser drops empty/absent values, so an optional field is simply absent (projects to `null`); never assume it is present. Fields without `?` are always present but their **array/object value may be empty** (`[]` / `{}`). All leaf values are plain strings unless shown otherwise. Capitalized names (`Author`, `Section`, `Para`, `Reference`, …) are reusable **shape definitions, not keys** — they never appear in the JSON; substitute the shape wherever it is referenced (so body prose is `.content.sections[].paragraphs[].text`, never `.Section...`).

```
parse <PMCID> emits EXACTLY these six top-level keys — nothing else:

{
  article_info: {
    title?:            str
    abstract?:         str          # plain string; abstract subsection structure is NOT preserved
    article_type?:     str
    publication_date?: str          # "YYYY" | "YYYY-MM" | "YYYY-MM-DD"
    article_ids?:      { doi?, pmid?, pmcid? }       # strings; whole object absent if no ids
    journal?:          { name?, publisher?, issn? }  # strings; issn = first issn value
    license?:          { type?, url?, text? }        # strings
    keywords:          [str]                         # always present, may be []
    authors:           [Author]                      # always present, may be []
    funding_grants:    [{ institution?, award_id? }] # always present, may be []
  }
  content: {
    sections:    [Section]   # always present, may be []
    paragraphs?: [Para]      # rare: paragraphs directly under <body>, outside any section
  }
  references: [Reference]    # always present, may be []
  figures:    [Figure]       # always present, may be []
  tables:     [Table]        # always present, may be []
  supporting_info: {         # all seven keys always present (values may be empty)
    acknowledgements:    [SectionLike]
    competing_interests: [{ source_id?, text? }]
    data_availability:   [SectionLike]
    supplementary_media: [{ source_id?, paragraphs: [{ source_id?, text? }], links: [Link] }]
    author_notes:        { notes: [Note], correspondence: [Corresp] }   # OBJECT, both keys always present
    related_articles:    [RelatedArticle]
    custom_metadata:     { <name>: <value> }   # flat string→string map, may be {}
  }
}

Author        = { given_names?, surname?, full_name?, orcid?, affiliations: [str] }
Section       = { source_id?, section_id?, title?, paragraphs: [Para], sections: [Section] }   # recursive
SectionLike   = { source_id?, title?, paragraphs: [Para], sections: [Section] }   # ack & data_availability: like Section but no section_id
Para          = { source_id?, text?, reference_ids: [str], figure_ids: [str], table_ids: [str] }
Reference     = { source_id?, label?, text?, publication_type?, identifiers?: {doi?, pmid?, pmcid?}, article_title?, source?, year?, volume?, issue?, pages? }
Figure        = { source_id?, label?, caption?, graphics: [str] }      # graphics = image filenames
Table         = { source_id?, label?, caption?, rows: [[str]], footnotes: [str] }   # rows = array of cell-arrays
Link          = { href?, text?, type? }
Note          = { source_id?, type?, label?, text? }
Corresp       = { source_id?, text?, emails: [str] }
RelatedArticle= { type?, href?, title?, source?, volume?, issue?, pages?, date?, identifiers: {doi?, pmid?, pmcid?} }
```

Two rules the schema cannot state for itself:

- Body prose lives **only** in `.content.sections[].paragraphs[].text` — reach a section with `query-id.jq` on its `source_id` rather than guessing a path, since the path depends on nesting depth.
- Do not probe structure: never run `jq 'keys'`, `jq 'paths'`, or dump a whole top-level object. You already hold the complete schema, so there is nothing to discover. Always pipe projections through `jq -c`.

## Task Router

Choose the smallest route that answers the request. Prefer a single command whose output is the answer, and let the shell command do the final formatting so your reply stays minimal. The right-hand column gives the parsed field to project (names from the schema above) or the CLI reference.

| Need | Route |
| --- | --- |
| Title / type / dates / keywords | `parse` → `.article_info` `{title, article_type, publication_date, keywords}` |
| Journal / IDs / license | `parse` → `.article_info.journal`, `.article_info.article_ids`, `.article_info.license`. For these plus OA/retraction flags and S3 URLs **without** parsing: [references/cli-metadata.md](references/cli-metadata.md) (`metadata`). |
| Abstract | `parse` → `.article_info.abstract` (string) |
| Authors + affiliations + ORCID | `parse` → `.article_info.authors[]` `{full_name, given_names, surname, affiliations, orcid}` |
| Funding | `parse` → `.article_info.funding_grants[]` `{institution, award_id}`; prose funding in `.supporting_info.acknowledgements` |
| Equal contribution / correspondence / author notes | `parse` → `.supporting_info.author_notes` `{notes[], correspondence[]}` (object). Read equal contribution from `notes[]`; do not infer it from author order. |
| Acknowledgements / data availability | `parse` → `.supporting_info.acknowledgements[]` / `.data_availability[]` (SectionLike; text in `.paragraphs[].text`) |
| Competing interests | `parse` → `.supporting_info.competing_interests[]` `{source_id, text}` |
| Supplements / related / custom meta | `parse` → `.supporting_info.supplementary_media[]`, `.related_articles[]`, `.custom_metadata` |
| Body structure, then a section | `content-outline.jq`, then `query-id.jq` on the chosen section `source_id` |
| Figures | `parse` → `.figures[]` `{source_id, label, caption, graphics}` |
| Tables | `parse` → `.tables[]` `{source_id, label, caption, rows, footnotes}` |
| References | `parse` → `.references[]` `{source_id, label, article_title, source, year, volume, pages, identifiers, text}` |
| Counts | `parse` → `.figures \| length`, `.tables \| length`, `.references \| length` |
| Which section cites figure/table/ref X | `reverse-lookup-xref.jq` (figures/tables have no section backref; it returns citing paragraphs tagged with their section) |
| Version availability / selection / resolved versioned PMCID | [references/cli-versions.md](references/cli-versions.md) (`versions`) |
| PMID/DOI → PMCID to continue a PMC workflow | [references/cli-idconv.md](references/cli-idconv.md) (`idconv`). Use when a parsed reference has `identifiers.pmid`/`doi` but no `identifiers.pmcid`. |
| File inventory or downloads (xml/pdf/text/figures/media/supplements) | [references/cli-files.md](references/cli-files.md) (`files`, `fetch`) |

For parsed-content tasks, the parse command details and jq retrieval patterns are in [references/cli-parse.md](references/cli-parse.md).

Example — authors, affiliations, and funding in one command:

```bash
uvx pmc-toolkit fetch <PMCID> --ext xml >/dev/null
uvx pmc-toolkit parse <PMCID> | jq -c '{authors: [.article_info.authors[] | {full_name, affiliations, orcid}], funding: .article_info.funding_grants, funding_ack: .supporting_info.acknowledgements}'
```

## Helper Scripts

Fetch XML once if needed, then retrieve the smallest parsed slice:

```bash
uvx pmc-toolkit parse <PMCID> | jq -c -f <SKILL_DIR>/scripts/content-outline.jq
uvx pmc-toolkit parse <PMCID> | jq -c --arg id "<SOURCE_ID>" -f <SKILL_DIR>/scripts/query-id.jq
uvx pmc-toolkit parse <PMCID> | jq -c --arg xref references --arg id "<REFERENCE_ID>" -f <SKILL_DIR>/scripts/reverse-lookup-xref.jq
```

`content-outline.jq` inventories sections (the per-article structure the schema cannot give you), `query-id.jq` fetches any known `source_id`, and `reverse-lookup-xref.jq` (`--arg xref` = `references` | `figures` | `tables`) returns each citing paragraph tagged with its enclosing section (`{section_id, section_title, text, <xref array>}`).

`source_id` is the article's native JATS id and is the key both lookup scripts match on. It is optional in the schema: a section or paragraph whose XML element carried no id has no `source_id`, so address such paragraphs through their enclosing section, never by a guessed id.

## Gotchas 

- `files` has no extension filter; use `fetch --ext` for filtered downloads.
- Parsed references often omit `identifiers.pmcid` even when they include `pmid` or `doi`, and may omit `identifiers` entirely. Use `idconv` to test for a matching PMC article before saying PMC full text is unavailable.
- Tables are XML-extracted only (`rows`/`footnotes`); a table that exists only in the PDF will not appear in `.tables[]`.
- `fetch`/`parse` use the default PMC Toolkit cache unless `--cache-dir` or `PMC_TOOLKIT_CACHE` is set; keep one cache root across both. Cache is per article version.
