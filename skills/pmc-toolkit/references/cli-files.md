# CLI: `files` And `fetch`

Use `files <PMCID>` to list every S3 object key under the resolved article version prefix. Use `fetch <PMCID>` to download all or selected object extensions into the local cache. The PMCID can be a base ID or a versioned ID.

## `files`

`files` has no extension filter.

```bash
uvx pmc-toolkit files PMCxxxx
```

Example output:

```json
{
  "versioned_pmcid": "PMCxxxx.N",
  "keys": [
    "PMCxxxx.N/PMCxxxx.N.xml",
    "PMCxxxx.N/PMCxxxx.N.pdf",
    "PMCxxxx.N/media-1.jpg"
  ]
}
```

Use `files` for inventory, not for local paths.

## `fetch`

Use `fetch` when a file must exist locally for parsing, inspection, or user delivery.

Example for downloading all files listed in above `files` output:
```bash
uvx pmc-toolkit fetch PMCxxxx --ext xml,pdf,jpg
```

Example output:

```json
{
  "versioned_pmcid": "PMCxxxx.N",
  "cache_dir": "/cache/root/PMCxxxx.N",
  "files": [
    {
      "key": "PMCxxxx.N/PMCxxxx.N.xml",
      "local_path": "/cache/root/PMCxxxx.N/PMCxxxx.N.xml",
      "action": "downloaded"
    }, ...
  ]
}
```

Use `local_path` if you need access to the downloaded files.

## Cache Notes

- `metadata` and `files` use the default OS user cache for metadata/manifests.
- `fetch` and `parse` can use `--cache-dir` or `PMC_TOOLKIT_CACHE`; keep the same cache root across both commands.
- Cache paths are per article version under `<cache_root>/<versioned-PMCID>/`.
