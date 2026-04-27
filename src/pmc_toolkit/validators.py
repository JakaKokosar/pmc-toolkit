import re

_PMCID_RE = re.compile(r"^PMC\d+$")
_INVALID_PMCID_MESSAGE = "Invalid PMC identifier: {value!r}. Expected format like 'PMC11370360' or 'PMC11370360.1'."


def normalize_pmcid(value: str) -> str:
    pmcid = value.strip().upper()

    if not _PMCID_RE.fullmatch(pmcid):
        raise ValueError(
            f"Invalid PMCID: {value!r}. Expected format like 'PMC11370360'."
        )

    return pmcid


def parse_pmcid(value: str) -> tuple[str, int | None]:
    requested_pmcid = value.strip().upper()
    pmcid, separator, raw_version = requested_pmcid.partition(".")
    normalized_pmcid = normalize_pmcid(pmcid)

    if not separator:
        return normalized_pmcid, None

    if "." in raw_version or not raw_version.isdigit():
        raise ValueError(_INVALID_PMCID_MESSAGE.format(value=value))

    version = int(raw_version)
    if version < 1:
        raise ValueError(_INVALID_PMCID_MESSAGE.format(value=value))

    return normalized_pmcid, version
