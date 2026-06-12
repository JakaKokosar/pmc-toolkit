# CLI: `parse`

Use `parse <PMCID.N>` after cached full-text XML exists. Run `fetch <PMCID.N> --ext xml` first when `<cache>/<PMCID.N>/<PMCID.N>.xml` is missing. The first run parses XML once, writes `<cache-root>/<PMCID.N>/.pmc-extracted-article.json`, and prints the extracted JSON; later runs reuse that cache unless `--force` is passed.

Add `--cache-dir` or `PMC_TOOLKIT_CACHE` when the XML was fetched outside the default OS user cache. Keep the same cache root across `fetch` and `parse`.

```bash
uvx pmc-toolkit fetch PMCxxxx.N --ext xml
uvx pmc-toolkit parse PMCxxxx.N
```

## Extracted JSON top-level keys

- **article_info** — `journal`, `article_ids`, `title`, `publication_date`, `article_type`, `license`, `keywords`, `authors[]`, `abstract`, `funding_grants[]`
- **content** — `paragraphs[]` and `sections[]`; items include `source_id`, `section_id`, `title`, `text`, `reference_ids`, `figure_ids`, and `table_ids`
- **references** — `references[]` with `source_id`, `label`, `text`, `publication_type`, `identifiers`, `article_title`, `source`, `year`, `volume`, `issue`, and `pages`
- **figures** — `figures[]` with `source_id`, `label`, `caption`, and `graphics`
- **tables** — `tables[]` with `source_id`, `label`, `caption`, `rows`, and `footnotes`
- **supporting_info** — `acknowledgements`, `competing_interests`, `data_availability`, `supplementary_media`, `author_notes`, `related_articles`, and `custom_metadata`

## Narrow retrieval with jq

**Start here.** Full `parse` output is large. Pipe it through jq and load only the slice you need.

### Content outline (default first step)

`scripts/content-outline.jq` returns a nested section tree: article title plus `section_id` and `title` for each section.

```bash
uvx pmc-toolkit parse PMCxxxx.N | jq -f scripts/content-outline.jq
```

Example output:

```json
{
  "title": "journal title",
  "sections": [
    {
      "section_id": "S1",
      "title": "section title"
    },
    {
      "section_id": "S2",
      "title": "section title",
      "sections": [
        {
          "section_id": "S3",
          "title": "sub-section title"
        }
      ]
    }
  ]
}
```
Use this to pick relevant sections (based on their titles) before loading detailed information. 
The `section_id` values are XML source IDs (`S1`, `S2`, …) — use them with `scripts/query-id.jq` to fetch detailed section data.

### Drill down by ID

`scripts/query-id.jq` returns the first object whose `source_id` matches. After the content outline, pass a chosen ID:

| Prefix | Meaning | Example |
| --- | --- | --- |
| `S*` | Section | `S3` |
| `P*` | Paragraph | `P9` |
| `F*` | Figure | `F1` |
| `R*` | Reference | `R1` |
| `T*` | Table | `T1` |

**Section** — paragraph text and xref links for that section:

```bash
uvx pmc-toolkit parse PMCxxxx.N | jq --arg id "S3" -f scripts/query-id.jq
```

Example output:

```json
{
  "source_id": "S3",
  "section_id": "2.1",
  "title": "sub-section title",
  "paragraphs": [
    {
      "source_id": "P9",
      "text": "paragraph text",
      "reference_ids": ["R1", "R18"],
      "figure_ids": ["F1", "F5"],
      "table_ids": ["T1"]
    }
  ],
  "sections": []
}
```

Some sections are containers only. In the outline, `S2` (Results) has child sections but no paragraphs of its own — the text lives in `S3`, `S4`, etc. 
Query those leaf `S*` IDs (sections with no nested `sections` in the outline), not the parent, to load only the subsection you need.

**Figure, table, or reference** — same script, different ID prefix:

```bash
uvx pmc-toolkit parse PMCxxxx.N | jq --arg id "F1" -f scripts/query-id.jq
uvx pmc-toolkit parse PMCxxxx.N | jq --arg id "R1" -f scripts/query-id.jq
uvx pmc-toolkit parse PMCxxxx.N | jq --arg id "T1" -f scripts/query-id.jq
```

Use paragraph `reference_ids`, `figure_ids`, and `table_ids` to fetch linked entries with `scripts/query-id.jq`. Output shapes:

- [cli-parse-references.md](cli-parse-references.md) — `R*` lookup
- [cli-parse-figures.md](cli-parse-figures.md) — `F*` lookup
- [cli-parse-tables.md](cli-parse-tables.md) — `T*` lookup

### Reverse lookup by xref

`query-id.jq` resolves an ID to its object. `reverse-lookup-xref.jq` finds every paragraph that cites a given reference, figure, or table. Pass `--arg xref` as `references`, `figures`, or `tables`:

```bash
uvx pmc-toolkit parse PMCxxxx.N | jq --arg xref references --arg id "R1" -f scripts/reverse-lookup-xref.jq
uvx pmc-toolkit parse PMCxxxx.N | jq --arg xref figures --arg id "F1" -f scripts/reverse-lookup-xref.jq
uvx pmc-toolkit parse PMCxxxx.N | jq --arg xref tables --arg id "T1" -f scripts/reverse-lookup-xref.jq
```
