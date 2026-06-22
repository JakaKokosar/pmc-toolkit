# CLI: `metadata`

Use `metadata <PMCID.N>` to fetch bibliographic fields, Open Access flags, and S3 URL fields (for example `xml_url`, `pdf_url`, `media_urls`, `text_url`), plus `pmid` and `doi`.

Example:
```bash
uvx pmc-toolkit metadata PMCxxxx.N
```

Example output:

```json
{
  "pmcid": "PMCxxxx",
  "version": N,
  "pmid": 12345678,
  "doi": "10.1234/example.doi",
  "mid": null,
  "title": "Example article title",
  "citation": "Journal Name",
  "is_pmc_openaccess": true/false,
  "is_manuscript": true/false,
  "is_historical_ocr": true/false,
  "is_retracted": true/false,
  "license_code": "license code",
  "xml_url": "s3://pmc-oa-opendata/PMCxxxx.N/PMCxxxx.N.xml?md5=<hex>",
  "pdf_url": "s3://pmc-oa-opendata/PMCxxxx.N/PMCxxxx.N.pdf?md5=<hex>",
  "media_urls": [
    "s3://pmc-oa-opendata/PMCxxxx.N/media-1.jpg?md5=<hex>",
    ...
  ],
  "text_url": "s3://pmc-oa-opendata/PMCxxxx.N/PMCxxxx.N.txt?md5=<hex>"
}
```
