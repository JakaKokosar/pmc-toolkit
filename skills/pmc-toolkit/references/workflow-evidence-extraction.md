# Workflow: Evidence Extraction

Use this workflow for article-content questions, evidence-grounded answers, section analysis, declarations, supplements, and claims that must be tied to PMC article evidence.

## Retrieval Loop

1. Resolve the PMCID to a pinned `<PMCID.N>`.
2. Fetch XML if needed:
   `uvx pmc-toolkit fetch <PMCID.N> --ext xml`
3. Inspect the outline first:
   `uvx pmc-toolkit parse <PMCID.N> | jq -c -f <SKILL_DIR>/scripts/content-outline.jq`
4. Use [data-locator.md](data-locator.md) to decide whether the answer lives in `article_info`, `content`, `supporting_info`, `figures`, `tables`, or `references`.
5. State the next retrieval plan before loading detailed evidence when the task needs multiple evidence targets.
6. Retrieve narrow evidence:
   `uvx pmc-toolkit parse <PMCID.N> | jq -c --arg id "<SOURCE_ID>" -f <SKILL_DIR>/scripts/query-id.jq`
7. For linked support, retrieve cited objects or reverse lookup citation context:
   `uvx pmc-toolkit parse <PMCID.N> | jq -c --arg xref references --arg id "<REFERENCE_ID>" -f <SKILL_DIR>/scripts/reverse-lookup-xref.jq`
8. If the user asks about the full text, abstract, authors, figures, tables, or evidence inside a referenced/cited article, inspect that reference's `identifiers`. If it has `pmcid`, continue with that PMCID. If it has `pmid` or `doi` but no `pmcid`, read [cli-idconv.md](cli-idconv.md) and run `idconv` before stopping.
9. Decide after each retrieval whether the evidence is sufficient. If not, choose the next source and repeat.
10. Stop when the answer is sufficiently supported or when the parsed JSON lacks the needed field. Report gaps explicitly.

## Evidence Selection

- Use article title, abstract, and outline to orient.
- Prefer sections whose titles match the task. Query leaf sections rather than broad parent sections when possible.
- For claims about results, methods, or discussion, use body paragraphs, not only the abstract.
- For declarations, use `supporting_info` first.
- For figure, table, or reference claims, inspect the object and linked paragraph context.
- For author/contributor claims, use the author workflow.

## Answer Requirements

Include in the final answer:

- Base PMCID and selected `<PMCID.N>`.
- Each claim with a human-readable locator.
- Stable `source_id` when useful for traceability.
- Short evidence summary or short quote from retrieved parsed JSON.
- Any gap, conflict, or mismatch.

Use these locators:

- Body text: `section_id` and section title, plus paragraph `source_id` when needed.
- Figures: figure `label`.
- Tables: table `label`.
- References: reference `label`.
- Supporting info: supporting-info category plus item `source_id` when available.
