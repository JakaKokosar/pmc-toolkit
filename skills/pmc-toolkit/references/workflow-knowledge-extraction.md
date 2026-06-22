# Workflow: Knowledge Extraction

Use this workflow for broad but structured tasks such as extracting key findings, mechanisms, datasets, claims, measurements, limitations, interventions, outcomes, or article-specific knowledge graphs. Keep the workflow generic; specialize the output schema to the user's task.

## Process

1. Resolve to `<PMCID.N>`.
2. Fetch XML and inspect the outline.
3. Read the abstract only for orientation:
   `uvx pmc-toolkit parse <PMCID.N> | jq -c '{title: .article_info.title, abstract: .article_info.abstract, keywords: .article_info.keywords}'`
4. Choose target sections from the outline. For most research extraction tasks, inspect methods, results, discussion, limitations, and any named domain sections.
5. Retrieve selected sections by `source_id` with `query-id.jq`.
6. Extract candidate knowledge records from retrieved evidence only.
7. If the task involves figures, tables, or references, retrieve those objects and their linked paragraph context.
8. Stop when the selected evidence covers the requested schema or when additional sections are unlikely to change the answer. Report uninspected sections when they are relevant but not loaded.

## Record Schema

Use or adapt this schema unless the user provides another:

- `item`: concise concept, claim, finding, method, variable, dataset, limitation, or outcome.
- `category`: user-relevant class such as method, result, mechanism, limitation, dataset, or evidence.
- `evidence_locator`: section title and `section_id`; figure/table/reference label if applicable.
- `source_id`: paragraph, section, figure, table, or reference ID.
- `evidence`: short quote or compact summary from retrieved parsed JSON.
- `confidence`: high, medium, or low based on specificity and directness of evidence.
- `gap`: missing context, ambiguity, or unsupported inference.

## Rules

- Separate article claims from your own synthesis.
- Do not use uninspected sections as evidence.
- Prefer direct result/method paragraphs over abstract-only evidence.
- Keep extraction records small enough to verify. If the task is large, produce a first-pass matrix and state what remains to inspect.
- Use [workflow-reporting.md](workflow-reporting.md) when the user asks for a polished report rather than raw records.



