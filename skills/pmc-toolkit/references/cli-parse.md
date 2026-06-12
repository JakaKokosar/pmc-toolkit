# CLI: `parse`

Use `parse <PMCID.N>` after cached full-text XML exists. Run `fetch <PMCID.N> --ext xml` first when `<cache>/<PMCID.N>/<PMCID.N>.xml` is missing. The first run parses XML once, writes `<cache-root>/<PMCID.N>/.pmc-extracted-article.json`, and prints the extracted JSON; later runs reuse that cache unless `--force` is passed.

Add `--cache-dir` or `PMC_TOOLKIT_CACHE` when the XML was fetched outside the default OS user cache. Keep the same cache root across `fetch` and `parse`.

Example:

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

After parsing, pipe the JSON through the skill jq helpers instead of loading the full article into context:

```bash
uvx pmc-toolkit parse PMCxxxx.N | jq -f skills/pmc-toolkit/scripts/section-index.jq
uvx pmc-toolkit parse PMCxxxx.N | jq --arg keyword "decoder" -f skills/pmc-toolkit/scripts/search-content.jq
uvx pmc-toolkit parse PMCxxxx.N | jq --arg keyword "funding" -f skills/pmc-toolkit/scripts/query-keyword.jq
uvx pmc-toolkit parse PMCxxxx.N | jq --arg id "F3" -f skills/pmc-toolkit/scripts/query-id.jq
```
