---
name: pmc-toolkit
description: Retrieve PubMed Central (PMC) Open Access article data from a PMCID or versioned PMCID, including version discovery, metadata, S3 file listings, downloads, cached XML parsing, structured article JSON, references, figures, tables, affiliations, author notes, funding, acknowledgements, data availability, competing interests, supplementary media, related articles, or custom metadata. Covers PMC Toolkit CLI and Python API workflows. Not for PubMed-only PMID lookup or general literature search without PMC OA article retrieval.
---

# PMC Toolkit

Use this skill to retrieve, download, and parse PMC Open Access article data with PMC Toolkit. Select commands by the data needed to complete the task, not by surface wording in the request.

## Operating Rules

- Run published-tool commands as `uvx pmc-toolkit ...`.
- Do not add installation guidance. If `uv` or `uvx` is unavailable, report that PMC Toolkit needs it and stop.
- Live lookups, listings, and downloads require network access to the PMC Open Access S3 dataset unless the needed data is already cached.
- Prefer targeted XML, metadata, and media retrieval over whole-PDF parsing. Use PDFs only when the user asks or just need to download for other reasons.

## Quick overview

1. Treat a base PMCID such as `<PMCID>` as the normal input. Convert it to an explicit versioned PMCID once, then reuse `<PMCID.N>` for downstream commands.
2. `versions <PMCID>` lists every published `<PMCID.N>`. Use it to enumerate versions or pin a concrete version for scripts (for example latest via `jq -r '.versions[-1]'`). Details: [references/cli-versions.md](references/cli-versions.md).
3. `metadata <PMCID>` or `metadata <PMCID.N>` returns bibliographic fields, OA flags, and S3 URL fields (`xml_url`, `pdf_url`, and so on). It is **not** the primary command for **resolving which `<PMCID.N>` exists or picking a version**. Details: [references/cli-metadata.md](references/cli-metadata.md).
4. `files <PMCID.N>` returns the complete S3 object-key inventory for that article version. It is the discovery step for available XML, PDFs, figures, media, and supplements.
5. `fetch <PMCID.N>` downloads all or filtered S3 objects into the local article cache. Add `--ext` for specific file types, `--cache-dir` for a task-specific cache, and `--force` to refresh cached files.
6. `parse <PMCID.N>` transforms cached full-text XML into normalized article JSON with top-level keys `article_info`, `content`, `references`, `figures`, `tables`, and `supporting_info`. Use it after XML is present in the selected cache; add `--force` to rebuild the extracted JSON cache. Details: [references/cli-parse.md](references/cli-parse.md).

## Context-first retrieval

Choose the smallest useful retrieval path for the question:

- Metadata, DOI, license, version, OA status, or file availability: run `versions` if a pinned version matters, then `metadata` or `files`.
- Abstract title, content sections, funding grants, authors, affiliations, references, figure captions, tables, or supporting statements, use `parse` to get the article JSON:
    - Figure questions: inspect `figures[]` from extracted JSON first; fetch only the referenced image extensions when the visual itself is needed.
    - Table questions: inspect `tables[]`; if it is empty, report that no structured XML tables were found rather than falling back to PDF parsing automatically.
    - Supplement, data availability, acknowledgements, competing interests, author contribution, or correspondence questions: inspect `supporting_info`.
    - Citation and evidence grounding: use link-aware paragraph fields (`source_id`, `reference_ids`, `figure_ids`, and `table_ids`) to retrieve only linked references, figures, or tables needed for the answer.

## Additional resources

- [references/cli-versions.md](references/cli-versions.md) — Examples for `versions`, including selecting the latest or a specific `<PMCID.N>`.
- [references/cli-metadata.md](references/cli-metadata.md) — Examples and field overview for `metadata`.
- [references/cli-parse.md](references/cli-parse.md) — Examples and field overview for `parse` output.

## Gotchas

- `versions` rejects versioned IDs; pass only a base PMCID.
- `metadata`, `files`, `fetch`, and `parse` accept base or versioned IDs. Passing a base ID makes those commands resolve the latest version at run time. Prefer `versions <PMCID>` (then reuse the chosen `<PMCID.N>`) when the work needs an explicit pinned version rather than repeating implicit latest-resolution on each command.
- `files` has no extension filter. Use `fetch --ext` for filtered downloads.
- `parse` needs `<cache>/<PMCID.N>/<PMCID.N>.xml`; run `fetch <PMCID.N> --ext xml` first when the XML is absent.
- `metadata` and `files` use the default OS user cache. `fetch` and `parse` can use `--cache-dir` or `PMC_TOOLKIT_CACHE`.
- Cache paths are per article version. Keep the same cache root across `fetch` and `parse`.
