---
name: pmc-toolkit
description: Work with PubMed Central Open Access articles by PMCID using PMC Toolkit. Use for version resolution, metadata and file inventory, downloads, parsed article evidence extraction, authors and contributor analysis, figures, tables, references, supplements, declarations, knowledge extraction, and report-style summaries. Can convert PMID/DOI to PMCID only to continue PMC full-text workflows; not for keyword literature search or non-PMC article analysis.
---

# PMC Toolkit

Use this skill to retrieve, download, parse, and cite PMC Open Access article data with PMC Toolkit. Select commands by the data needed to complete the task, not by surface wording in the request.

## Operating Rules

- Run published-tool commands as `uvx pmc-toolkit ...`.
- Do not add installation guidance. If `uv` or `uvx` is unavailable, report that PMC Toolkit needs it and stop.
- Live lookups, listings, and downloads require network access to the PMC Open Access S3 dataset unless the needed data is already cached.
- Resolve bundled helper paths relative to this skill directory, for example `<SKILL_DIR>/scripts/content-outline.jq`.
- Do not load, dump, grep, or search raw XML or PDF files directly for article-content tasks. Fetch XML only as parser input, then use `parse` output and bundled JSON helpers for evidence extraction.
- When piping PMC Toolkit JSON through `jq`, use `jq -c` unless pretty-printed JSON is explicitly needed for human inspection. Prefer compact JSON to avoid bloating context.
- For simple extraction requests where the command output is already the user-facing answer, do not repeat large text in the final response. Return only a brief label or status plus the exact command output when needed; for long abstracts, tables, or lists, prefer telling the user the command printed the requested value instead of restating it.
- Do not invent missing declarations, author notes, figures, tables, or references. Report the missing parsed field or empty list.

## Task Router

Choose the smallest route that answers the request. Prefer a direct CLI route when one command output is enough; use a workflow route when the task needs multi-step retrieval, synthesis, or evidence reporting. If using a direct CLI route, make the shell command do the final formatting so the assistant response can stay minimal.

### Direct CLI Routes

- PMCID availability and version resolution: read [references/cli-versions.md](references/cli-versions.md) for `versions` command details.
- PMID/DOI to PMCID conversion for continuing PMC workflows: read [references/cli-idconv.md](references/cli-idconv.md) for `idconv` command details.
- DOI, title, journal, license, OA flags, retraction flags, and S3 URL fields: read [references/cli-metadata.md](references/cli-metadata.md) for `metadata` command details.
- File inventory or downloads for XML, PDF, text, figures, media, or supplements: read [references/cli-files.md](references/cli-files.md) for `files` and `fetch` command details.
- Parsed article JSON, body sections, supporting info, parsed authors, figures, tables, references, or helper `jq` usage: run `fetch --ext xml` as needed, then `parse`. Read [references/cli-parse.md](references/cli-parse.md) for `parse` output shape and helper-script usage.
- If `parse` is needed but the right parsed field is not obvious, read [references/data-locator.md](references/data-locator.md) before retrieving detailed evidence.
- When a task asks about a referenced/cited article and the parsed reference has `identifiers.pmid` or `identifiers.doi` but no `identifiers.pmcid`, use `idconv` before stopping.

### Workflow Routes

- Article-content questions, passage finding, section analysis, support for claims, declarations, supplements, or evidence-grounded answers: read [references/workflow-evidence-extraction.md](references/workflow-evidence-extraction.md).
- Author, affiliation, ORCID, equal-contribution, corresponding-author, contributor, or author-note tasks: read [references/workflow-author-contributor-analysis.md](references/workflow-author-contributor-analysis.md).
- Knowledge extraction, claim extraction, evidence matrices, mechanism summaries, or structured fact extraction: read [references/workflow-knowledge-extraction.md](references/workflow-knowledge-extraction.md).
- Figure interpretation, graphics lookup, panel questions, or visual inspection: read [references/workflow-figure-image-analysis.md](references/workflow-figure-image-analysis.md). Fetch image files only when visual inspection is required.
- Report-style summaries, author reports, evidence reports, or deliverables combining several data types: read [references/workflow-reporting.md](references/workflow-reporting.md), then load only the source-specific workflow references required by the report.

## Bundled Resources

Open references only after choosing a route above, when command-specific details, output shapes, or workflow details are needed.

- [references/data-locator.md](references/data-locator.md) - task-to-parsed-JSON-field routing.
- [references/workflow-evidence-extraction.md](references/workflow-evidence-extraction.md) - detailed evidence retrieval loop and answer contract.
- [references/workflow-author-contributor-analysis.md](references/workflow-author-contributor-analysis.md) - author, affiliation, correspondence, and contributor-note workflow.
- [references/workflow-knowledge-extraction.md](references/workflow-knowledge-extraction.md) - generic structured extraction workflow.
- [references/workflow-figure-image-analysis.md](references/workflow-figure-image-analysis.md) - figure caption, linked text, and visual-inspection workflow.
- [references/workflow-reporting.md](references/workflow-reporting.md) - report assembly pattern for mixed data tasks.
- [references/cli-versions.md](references/cli-versions.md) - `versions` examples and version selection.
- [references/cli-idconv.md](references/cli-idconv.md) - `idconv` examples and missing-PMC handling.
- [references/cli-metadata.md](references/cli-metadata.md) - `metadata` examples and field overview.
- [references/cli-files.md](references/cli-files.md) - `files` and `fetch` output shapes.
- [references/cli-parse.md](references/cli-parse.md) - `parse` output shape and helper-script usage.
- [references/cli-parse-figures.md](references/cli-parse-figures.md) - figure lookup shape and citation context.
- [references/cli-parse-tables.md](references/cli-parse-tables.md) - table lookup shape and citation context.
- [references/cli-parse-references.md](references/cli-parse-references.md) - reference lookup shape and citation context.
- `<SKILL_DIR>/scripts/content-outline.jq` - paper outline first step for evidence extraction.
- `<SKILL_DIR>/scripts/query-id.jq` - lookup sections, paragraphs, figures, tables, and references by `source_id`.
- `<SKILL_DIR>/scripts/reverse-lookup-xref.jq` - find paragraphs that cite a figure, table, or reference.

## Gotchas

- `files` has no extension filter. Use `fetch --ext` for filtered downloads.
- Parsed reference records often omit PMCID even when they include PMID or DOI. Use `idconv` to test whether PMC has a matching article before saying PMC full text is unavailable.
- `parse` needs cached XML; run `fetch <PMCID.N> --ext xml` first when XML is absent.
- `fetch` and `parse` use the default PMC Toolkit cache unless `--cache-dir` or `PMC_TOOLKIT_CACHE` is provided. Use custom cache paths only when there is a concrete reason.
- Cache paths are per article version. Keep the same cache root across `fetch` and `parse` if a custom cache is used.
