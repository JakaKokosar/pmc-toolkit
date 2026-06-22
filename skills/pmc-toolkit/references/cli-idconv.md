# CLI: `idconv`

Use `idconv <ID...>` to convert PMID, DOI, PMCID, or MID values to PMC identifiers through the PMC ID Converter API. Use this only as a bridge back into PMC full-text workflows, for example when a parsed reference has `identifiers.pmid` or `identifiers.doi` but no `identifiers.pmcid`.

```bash
uvx pmc-toolkit idconv 23193287
uvx pmc-toolkit idconv 10.1093/nar/gks1195 --idtype doi
```

Example output shape:

```json
[
  {
    "requested-id": "23193287",
    "pmid": 23193287,
    "pmcid": "PMC3531190",
    "doi": "10.1093/nar/gks1195"
  }
]
```

When a record has `status: "error"` or no `pmcid`, stop the PMC full-text workflow for that referenced article and report that no matching PMC record was found. Do not summarize from the title alone.

After a record returns `pmcid`, run `versions <PMCID>` and continue with `metadata`, `fetch`, and `parse`.
