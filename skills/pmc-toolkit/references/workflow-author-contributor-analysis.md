# Workflow: Author And Contributor Analysis

Use this workflow for author lists, affiliations, ORCIDs, corresponding authors, equal-contribution notes, contributor notes, author-focused reports, and author-related declarations.

## Source Priority

1. Use `metadata` for PMCID version, title, DOI, citation, OA flags, and retraction status.
2. Use `parse` for author names, resolved affiliations, ORCIDs, and author notes.
3. Use `supporting_info.author_notes` for equal contribution, correspondence, and other notes.
4. Use `supporting_info.acknowledgements`, `competing_interests`, and `data_availability` only when the author task asks for declarations or report context.

## Retrieval

Resolve the version and fetch XML:

```bash
uvx pmc-toolkit metadata <PMCID.N>
uvx pmc-toolkit fetch <PMCID.N> --ext xml
uvx pmc-toolkit parse <PMCID.N> | jq -c '{title: .article_info.title, authors: .article_info.authors, author_notes: .supporting_info.author_notes}'
```

If declarations or report context are requested:

```bash
uvx pmc-toolkit parse <PMCID.N> | jq -c '.supporting_info | {acknowledgements, competing_interests, data_availability, author_notes}'
```

## Interpretation Rules

- Preserve author order from `.article_info.authors[]`.
- Treat missing `orcid` fields as absent ORCIDs. Do not infer ORCIDs.
- Treat missing affiliation text as absent affiliation data. Do not invent institutional names.
- Identify equal contribution only from `author_notes`, not from author order or symbols unless the note explains the symbol.
- Identify corresponding authors only from correspondence entries or explicit author notes.
- If author notes mention symbols but the parsed author list does not connect symbols to names, report the limitation instead of forcing a mapping.

## Output Patterns

For a compact author answer, include:

- Selected `<PMCID.N>`.
- Article title and DOI when available.
- Ordered author list.
- Affiliation and ORCID fields when requested or relevant.
- Author-note evidence with `supporting_info.author_notes` and item `source_id` when available.
- Clear gaps for missing ORCIDs, affiliations, equal-contribution notes, or correspondence.

For an author report, use [workflow-reporting.md](workflow-reporting.md) and include an evidence table for author-note claims.
