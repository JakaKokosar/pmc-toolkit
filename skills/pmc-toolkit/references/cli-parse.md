# CLI: `parse`

Use `parse <PMCID>` after cached full-text XML exists. The PMCID can be a base ID such as `PMC11370360` or a versioned ID such as `PMC11370360.1`; base IDs resolve to the latest version. Run `fetch <PMCID> --ext xml` first when cached XML is missing. The first run parses XML once, writes `<cache-root>/<versioned-PMCID>/.pmc-extracted-article.json`, and prints the extracted JSON; later runs reuse that cache unless `--force` is passed.

Add `--cache-dir` or `PMC_TOOLKIT_CACHE` when the XML was fetched outside the default OS user cache. Keep the same cache root across `fetch` and `parse`.

```bash
uvx pmc-toolkit fetch PMCxxxx --ext xml
uvx pmc-toolkit parse PMCxxxx
```

The `parse` command prints the extracted article JSON (`result.data`), not the `fetch` wrapper with `versioned_pmcid`, `cache_dir`, and downloaded `files`.

## Field shapes live in SKILL.md

The complete, closed-world field schema for every parsed object is in **SKILL.md** ("The Parsed Schema Is Closed"). Build every projection from it and do not guess field names; a name absent from that schema does not exist. This reference covers only how to *retrieve* slices efficiently.

Output always has exactly these six top-level keys: `article_info`, `content`, `references`, `figures`, `tables`, `supporting_info`. Do not probe with `jq 'keys'`.

Body prose is under `.content.sections[]` (recursive); each section's text is in its `paragraphs[].text`. A section's `source_id` is its native JATS id when the element has one (it is optional — some sections and most paragraphs have none), so address paragraphs through their enclosing section, not a guessed paragraph id. Each paragraph also carries the xref arrays `reference_ids` / `figure_ids` / `table_ids`.

## Narrow retrieval with jq

**Start here.** Full `parse` output is large. Pipe it through jq and load only the slice you need, always with `jq -c`.

For parsed article-content work, use the helper scripts before inventing jq filters. `content-outline.jq` inventories section structure, `query-id.jq` retrieves a chosen `source_id`, and `reverse-lookup-xref.jq` finds paragraph context for cited figures, tables, or references.

### Direct counts

For questions like "how many references/figures/tables?", count the top-level arrays:

```bash
uvx pmc-toolkit fetch PMCxxxx --ext xml >/dev/null && uvx pmc-toolkit parse PMCxxxx | jq '.references | length'
uvx pmc-toolkit fetch PMCxxxx --ext xml >/dev/null && uvx pmc-toolkit parse PMCxxxx | jq '.figures | length'
uvx pmc-toolkit fetch PMCxxxx --ext xml >/dev/null && uvx pmc-toolkit parse PMCxxxx | jq '.tables | length'
```

### Content outline (default first step)

`scripts/content-outline.jq` returns a nested section tree: article title plus `source_id`, optional logical `section_id`, and `title` for each section. This is the per-article structure the static schema cannot give you — run it for every article whose body you need.

```bash
uvx pmc-toolkit parse PMCxxxx | jq -c -f <SKILL_DIR>/scripts/content-outline.jq
```

Example output:

```json
{
  "title": "article title",
  "sections": [
    {"source_id": "S1", "section_id": "1", "title": "section title"},
    {"source_id": "S2", "section_id": "2", "title": "section title",
     "sections": [
       {"source_id": "S3", "section_id": "2.1", "title": "sub-section title"}
     ]}
  ]
}
```

The `source_id` values above (`S1`, `S2`, ...) are placeholders. Real ids are the article's native JATS element ids (e.g. `btpr70073-sec-0001`) and vary per article — always copy them from this outline (or from paragraph xref arrays), never construct or guess them.

Use this to pick relevant sections by title before loading detail, then pass a copied `source_id` to `<SKILL_DIR>/scripts/query-id.jq` to fetch that section.

### Drill down by ID

`scripts/query-id.jq` returns the first object whose `source_id` matches. After the content outline, pass a chosen ID:

**Section** — paragraph text and xref links for that section:

```bash
uvx pmc-toolkit parse PMCxxxx | jq -c --arg id "S3" -f <SKILL_DIR>/scripts/query-id.jq
```

Query sections by their `source_id`; paragraphs usually have no `source_id` of their own, so you reach paragraph text and its xref arrays through the parent section, not by querying a paragraph id.

Some sections are containers only — a Results section may have child sections but no paragraphs of its own; the text lives in its leaf subsections. Query those leaf section ids (sections with no nested `sections` in the outline), not the parent.

**Figure, table, or reference** — same script, different ID prefix:

```bash
uvx pmc-toolkit parse PMCxxxx | jq -c --arg id "F1" -f <SKILL_DIR>/scripts/query-id.jq
uvx pmc-toolkit parse PMCxxxx | jq -c --arg id "R1" -f <SKILL_DIR>/scripts/query-id.jq
uvx pmc-toolkit parse PMCxxxx | jq -c --arg id "T1" -f <SKILL_DIR>/scripts/query-id.jq
```

Use paragraph `reference_ids`, `figure_ids`, and `table_ids` to fetch linked entries with `scripts/query-id.jq`. A figure lookup returns one `.figures[]` object, a reference lookup one `.references[]` object, a table lookup one `.tables[]` object — shapes are in the SKILL.md schema.

### Reverse lookup by xref

`query-id.jq` resolves an ID to its object. `reverse-lookup-xref.jq` finds every paragraph that cites a given reference, figure, or table. Pass `--arg xref` as `references`, `figures`, or `tables`:

```bash
uvx pmc-toolkit parse PMCxxxx | jq -c --arg xref references --arg id "R1" -f <SKILL_DIR>/scripts/reverse-lookup-xref.jq
uvx pmc-toolkit parse PMCxxxx | jq -c --arg xref figures --arg id "F1" -f <SKILL_DIR>/scripts/reverse-lookup-xref.jq
uvx pmc-toolkit parse PMCxxxx | jq -c --arg xref tables --arg id "T1" -f <SKILL_DIR>/scripts/reverse-lookup-xref.jq
```

Each match returns `{section_id, section_title, text, <xref array>}` — the paragraph `text` is the citation context, and `section_id`/`section_title` locate it (figures and tables have no section backref of their own, so this is how you answer "which section is figure/table X in"). `section_id` is `null` only for the rare paragraph outside any section.
