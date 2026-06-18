---
name: pmc-toolkit
description: Work with PubMed Central Open Access articles by PMCID using PMC Toolkit. Use for version resolution, metadata, file listings, downloads, and evidence extraction, including text, figures, tables, references, supplements, and declarations. Not for PMID lookup, keyword literature search, or non-PMC Open Access articles.
---

# PMC Toolkit

Use this skill to retrieve, download, and parse PMC Open Access article data with PMC Toolkit. Select commands by the data needed to complete the task, not by surface wording in the request.

## Operating Rules

- Run published-tool commands as `uvx pmc-toolkit ...`.
- Do not add installation guidance. If `uv` or `uvx` is unavailable, report that PMC Toolkit needs it and stop.
- Live lookups, listings, and downloads require network access to the PMC Open Access S3 dataset unless the needed data is already cached.
- Resolve bundled helper paths relative to this skill directory, for example `<SKILL_DIR>/scripts/content-outline.jq`.
- Do not load, dump, grep, or search raw XML or PDF files directly for article-content tasks. Fetch XML only as parser input, then use `parse` output and bundled JSON helpers for evidence extraction. 
- When piping PMC Toolkit JSON through `jq`, use `jq -c` unless pretty-printed JSON is explicitly needed for human inspection. Prefer compact JSON to avoid bloating context.

## Core Workflows

Choose the smallest workflow that answers the request.

### Article Version Resolution

Use this workflow to convert a base PMCID into an explicit versioned PMCID for deterministic downstream commands.

1. If the user provides a base PMCID such as `<PMCID>`, run:
   `uvx pmc-toolkit versions <PMCID>`

2. If `.versions` is empty, stop for that article and report that no PMC Open Access version was found.

3. Select an explicit `<PMCID.N>`. Use the latest version unless the user asks for a specific version:
   `jq -c -r '.versions[-1]'`

4. Reuse the selected `<PMCID.N>` for downstream `metadata`, `files`, `fetch`, and `parse` commands.

5. If the user already provides a versioned PMCID such as `<PMCID.N>`, treat it as pinned. Do not pass versioned IDs to `versions`, because `versions` accepts only base PMCIDs.

Details: [references/cli-versions.md](references/cli-versions.md).

### Evidence Extraction

Use this workflow for article-content, question-answer support, passage finding, section analysis, figure/table/reference support, or citation-grounded answers.

1. Resolve the article with **Article Version Resolution**.

2. Fetch XML:
   `uvx pmc-toolkit fetch <PMCID.N> --ext xml`

3. Parse the article:
   `uvx pmc-toolkit parse <PMCID.N>`

4. Load the paper outline first with the bundled helper:
   `uvx pmc-toolkit parse <PMCID.N> | jq -c -f <SKILL_DIR>/scripts/content-outline.jq`

5. Use the outline to choose the first likely evidence targets. State the next retrieval plan before loading detailed evidence.

6. Iteratively retrieve only the evidence needed to answer the request:
   - Drill into selected sections, paragraphs, figures, tables, or references with:
     `uvx pmc-toolkit parse <PMCID.N> | jq -c --arg id "<SOURCE_ID>" -f <SKILL_DIR>/scripts/query-id.jq`
   - When tracing figure, table, or reference support, use reverse lookup:
     `uvx pmc-toolkit parse <PMCID.N> | jq -c --arg xref figures --arg id "<FIGURE_ID>" -f <SKILL_DIR>/scripts/reverse-lookup-xref.jq`
   - After each retrieval, decide whether the evidence is sufficient. If not, state the next target and repeat this step.

7. Stop retrieving when the answer is sufficiently supported or when the parsed JSON lacks the needed evidence. Report gaps explicitly.

8. Ground final answers in retrieved JSON evidence. Use human-readable locators in the final answer: section `section_id` + title for text, figure/table/reference `label` for non-text objects. Keep `source_id` as the stable internal lookup key and include it only when useful for traceability.

## Evidence Targets

- For figure questions, inspect `figures[]` and linked paragraphs first; fetch image files only when the visual itself is needed.
- For table questions, inspect `tables[]`. If no structured XML tables are present, report that instead of falling back to PDF parsing automatically.
- For acknowledgements, funding, data availability, competing interests, author notes, correspondence, supplements, or related articles, inspect `supporting_info`.
- For citation and evidence grounding, use paragraph `source_id`, `reference_ids`, `figure_ids`, and `table_ids`.

## Evidence Answer Contract

For Evidence Extraction tasks, include evidence locators in the first final answer. Do not offer citations, source IDs, or compact citation format as a follow-up.

For each question or claim, include:

- PMCID and selected `<PMCID.N>`, or the exact stop reason if no version exists.
- Human-readable evidence locators:
  - For article text, cite `section_id` and section title.
  - For figures, cite figure `label`.
  - For tables, cite table `label`.
  - For references, cite reference `label`.
- Stable `source_id`s when needed for traceability, especially for paragraphs or when the human-readable locator is ambiguous.
- A short evidence summary or short quote from retrieved parsed JSON.
- Any gap, conflict, or mismatch between the proposed answer and the retrieved evidence.

Do not present evidence bullets without human-readable locators for Evidence Extraction tasks.

Details: [references/cli-parse.md](references/cli-parse.md).

### Metadata And File Availability

Use this workflow for DOI, title, authors, journal, license, publication date, OA status, available S3 objects, XML/PDF/image/supplement availability, or file inventory questions.

1. Resolve the article with **Article Version Resolution** when the user provides a base PMCID or when reproducibility matters.

2. For bibliographic and OA fields, run:
   `uvx pmc-toolkit metadata <PMCID.N>`

3. For available XML, PDFs, figures, media, and supplements, run:
   `uvx pmc-toolkit files <PMCID.N>`

4. Do not fetch or parse XML for metadata-only or file-availability tasks unless article content evidence is also needed.

5. Use `fetch --ext <EXT>` only after `files` or the user’s request makes the needed file type clear.

Details: [references/cli-metadata.md](references/cli-metadata.md).



## Bundled Resources

Open references only after choosing the workflow above, when command-specific details or output shapes are needed.

- [references/cli-versions.md](references/cli-versions.md) — `versions` examples and version selection.
- [references/cli-metadata.md](references/cli-metadata.md) — `metadata` examples and field overview.
- [references/cli-parse.md](references/cli-parse.md) — `parse` output shape and helper-script usage.
- `<SKILL_DIR>/scripts/content-outline.jq` — paper outline first step for evidence extraction.
- `<SKILL_DIR>/scripts/query-id.jq` — lookup sections, paragraphs, figures, tables, and references by `source_id`.
- `<SKILL_DIR>/scripts/reverse-lookup-xref.jq` — find paragraphs that cite a figure, table, or reference.

## Gotchas

- `files` has no extension filter. Use `fetch --ext` for filtered downloads.
- `parse` needs cached XML; run `fetch <PMCID.N> --ext xml` first when XML is absent.
- `fetch` and `parse` use the default PMC Toolkit cache unless `--cache-dir` or `PMC_TOOLKIT_CACHE` is provided. Use custom cache paths only when there is a concrete reason.
- Cache paths are per article version. Keep the same cache root across `fetch` and `parse` if a custom cache is used.