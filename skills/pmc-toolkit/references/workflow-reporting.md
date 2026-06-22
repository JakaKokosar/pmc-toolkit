# Workflow: Reporting

Use this workflow when the user asks for a report, memo, evidence brief, author report, structured summary, or deliverable that combines multiple PMC Toolkit data sources.

## Process

1. Infer the report scope from the request. Ask a question only when the deliverable cannot be scoped safely.
2. Resolve to `<PMCID.N>` and collect metadata for the report header.
3. Use the router in `SKILL.md` to choose command and workflow sources. Load [data-locator.md](data-locator.md) only when parsed JSON fields are not obvious.
4. Load only the source-specific workflow references required by the report.
5. Retrieve evidence in small slices. Keep a scratch list of every claim with its locator.
6. Assemble the report from retrieved evidence only.
7. Include a limitations or gaps section when data is absent, ambiguous, or not inspected.

## Suggested Sections

Use these sections when they fit the task:

- Article: PMCID, selected version, title, DOI, journal/citation, date, license/OA status.
- Scope: what the report covers.
- Findings: grouped by the user's task.
- Evidence Table: claim, locator, source ID, short evidence, gap.
- Files Or Artifacts: available XML/PDF/media/supplements when relevant.
- Gaps: absent parsed fields, unavailable XML/files, or uninspected sections.

## Rules

- Do not make report sections that hide evidence gaps.
- Do not over-fetch. A report can combine metadata, author notes, and a few body sections without loading the entire parsed article.
- Use concise quotations only when they add auditability.
- For author reports, use [workflow-author-contributor-analysis.md](workflow-author-contributor-analysis.md).
- For broad extraction reports, use [workflow-knowledge-extraction.md](workflow-knowledge-extraction.md).
