# Parsed Data Locator

Use this file after choosing `parse` when the right parsed JSON field is not obvious. It maps task intent to the lowest-cost parsed field or helper command. For command selection before parsing, use the router in `SKILL.md` and the CLI references.

## Parsed JSON Routing

Use `uvx pmc-toolkit parse <PMCID.N> | jq -c '<filter>'` for compact retrieval.

| Task | First parsed source | Notes |
| --- | --- | --- |
| Article identity from XML | `.article_info` | Use when XML-derived identity is needed. For DOI, title, journal, license, OA flags, and S3 URLs alone, prefer `metadata`. |
| Abstract | `.article_info.abstract` | Use before body sections for high-level study orientation. |
| Body section discovery | `<SKILL_DIR>/scripts/content-outline.jq` | Always inspect outline before loading body text. |
| Body passages | `query-id.jq` on selected `content.sections[].source_id` | Prefer leaf sections when parent sections only group subsections. |
| Standalone body paragraphs | `.content.paragraphs[]?` | Some XML has top-level body paragraphs outside sections. |
| Authors and affiliations | `.article_info.authors[]` | Authors include resolved affiliation text when available. |
| ORCID | `.article_info.authors[].orcid` | Report absent ORCIDs as absent, not unknown. |
| Equal contribution, author notes, correspondence | `.supporting_info.author_notes` | Use with `.article_info.authors[]`; do not infer equal contribution from author order alone. |
| Funding | `.article_info.funding_grants[]`, then `.supporting_info` | Some articles encode funding in article metadata, some in acknowledgements. |
| Acknowledgements | `.supporting_info.acknowledgements[]` | Cite paragraph `source_id` when available. |
| Competing interests | `.supporting_info.competing_interests[]` | Preserve exact statement and report absence if empty. |
| Data availability | `.supporting_info.data_availability[]` | Preserve accessions, repository names, URLs, and restrictions. |
| Supplementary media | `.supporting_info.supplementary_media[]` | Use `files` only when local download or object-key inventory is needed. |
| Related articles | `.supporting_info.related_articles[]` | Useful for preprint to published article links. |
| Custom PMC/JATS metadata | `.supporting_info.custom_metadata` | Use for PMC properties that are not normal article fields. |
| Figures | `.figures[]` | Start with label, caption, graphics. Use linked paragraphs before fetching images unless visual inspection is requested. |
| Tables | `.tables[]` | Contains XML-extracted rows and footnotes only. Do not assume PDF-only tables are available. |
| References | `.references[]` | Use identifiers and labels. Reverse lookup paragraphs that cite a reference for context. |
| Figure, table, or reference citation context | `reverse-lookup-xref.jq` | Pass `--arg xref figures`, `tables`, or `references`. |

## Retrieval Shortcuts

- Author summary:
  `uvx pmc-toolkit parse <PMCID.N> | jq -c '{title: .article_info.title, authors: .article_info.authors, author_notes: .supporting_info.author_notes}'`
- Declarations:
  `uvx pmc-toolkit parse <PMCID.N> | jq -c '.supporting_info | {acknowledgements, competing_interests, data_availability, author_notes}'`
- Figure inventory:
  `uvx pmc-toolkit parse <PMCID.N> | jq -c '.figures[] | {source_id, label, caption, graphics}'`
- Table inventory:
  `uvx pmc-toolkit parse <PMCID.N> | jq -c '.tables[] | {source_id, label, caption, rows, footnotes}'`
- Reference inventory:
  `uvx pmc-toolkit parse <PMCID.N> | jq -c '.references[] | {source_id, label, article_title, source, year, identifiers}'`
