# Releasing

Pushing a `v*` git tag triggers [`release.yml`](.github/workflows/release.yml),
which builds with `uv build` and publishes to
[PyPI](https://pypi.org/project/pmc-toolkit/) via Trusted Publishing (OIDC,
no tokens).

## Release flow

```sh
# 1. Make sure main is green and up to date.
git switch main && git pull

# 2. Bump version ( major | minor | patch, or X.Y.Z for an exact version).
uv version --bump "<major | minor | patch>"
version="$(uv version --short)"

# 3. Commit, push, wait for CI to go green.
git add pyproject.toml uv.lock
git commit -m "release: v${version}"
git push

# 4. Tag and push — this triggers the publish.
git tag "v${version}"
git push origin "v${version}"
```

Watch the **Release** workflow in the Actions tab. Approve the `pypi`
deployment if the environment requires it. Smoke test:

```sh
uv run --with "pmc-toolkit==${version}" --no-project -- pmc-toolkit --help
```

From **v0.2.0**, the PyPI wheel exposes only the `pmc-toolkit` console script
(the previous `pmc` script was removed so the binary matches the distribution
name).

Optionally draft a GitHub Release from the tag for user-facing notes.

## Troubleshooting

- **`invalid-publisher`** — PyPI trusted-publisher fields don't match the
  workflow run (case-sensitive).
- **Tag/version mismatch** — fix `pyproject.toml` or delete the bad tag:
  `git tag -d vX.Y.Z && git push --delete origin vX.Y.Z`.
- **Bad release** — PyPI forbids re-uploading the same version. Yank it on
  PyPI, bump again, re-release.
