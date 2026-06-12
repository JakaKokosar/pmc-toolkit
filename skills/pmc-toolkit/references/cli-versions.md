# CLI: `versions`

Use `versions <PMCID>` to list every published versioned PMCID string (`PMCxxxx.1`, `PMCxxxx.2`, …) for a **base** PMCID only. `versions` rejects versioned IDs.

```bash
uv run pmc-toolkit versions PMCxxxx
```

Example output shape:

```json
{
  "pmcid": "PMCxxxx",
  "versions": [
    "PMCxxxx.1",
    "PMCxxxx.2"
  ]
}
```

## Pick the latest `<PMCID.N>`

```bash
uv run pmc-toolkit versions PMCxxxx | jq -r '.versions[-1]'
```

## Pick a non-latest version

Select an element of `.versions` by index (for example `.versions[0]` for the first published version).

## Next steps

After you have `<PMCID.N>`, continue with `metadata`, `files`, `fetch`, and `parse` as described in the main skill.
