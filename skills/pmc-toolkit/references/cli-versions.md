# CLI: `versions`

Use `versions <PMCID>` to list published versioned PMCID strings (`PMCxxxx.1`, `PMCxxxx.2`, ...) for a **base** PMCID only. Use this for version questions, version selection, or reporting the resolved versioned PMCID. For `metadata`, `files`, `fetch`, and `parse`, pass the user's PMCID directly unless a specific non-latest version is required.

```bash
uvx pmc-toolkit versions PMCxxxx
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

`.versions` is an array of strings. The latest versioned PMCID is `.versions[-1]`.

If `.versions` is empty, stop for that PMCID and report that no PMC Open Access version was found. Do not continue to `metadata`, `files`, `fetch`, or `parse` for that PMCID.

## Pick the latest versioned PMCID

```bash
uvx pmc-toolkit versions PMCxxxx | jq -c -r '.versions[-1]'
```

## Pick a non-latest version

Select an element of `.versions` by index (for example `.versions[0]` for the first published version).

## Next steps

Use the selected version string only when the task requires a specific version. Otherwise, continue with the user's base PMCID as described in the main skill.
