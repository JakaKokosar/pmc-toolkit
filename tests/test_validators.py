import pytest

from pmc_toolkit.validators import normalize_pmcid, parse_pmcid


def test_normalize_pmcid_accepts_valid_value() -> None:
    assert normalize_pmcid("pmc11370360") == "PMC11370360"


def test_normalize_pmcid_rejects_invalid_value() -> None:
    with pytest.raises(ValueError):
        normalize_pmcid("11370360")


def test_parse_pmcid_accepts_base_pmcid() -> None:
    assert parse_pmcid("pmc11370360") == ("PMC11370360", None)


def test_parse_pmcid_accepts_versioned_pmcid() -> None:
    assert parse_pmcid("pmc11370360.2") == ("PMC11370360", 2)


def test_parse_pmcid_rejects_invalid_value() -> None:
    with pytest.raises(ValueError):
        parse_pmcid("11370360")


def test_parse_pmcid_rejects_invalid_pmcid_in_versioned_value() -> None:
    with pytest.raises(ValueError):
        parse_pmcid("11370360.2")


def test_parse_pmcid_rejects_non_positive_version() -> None:
    with pytest.raises(ValueError):
        parse_pmcid("PMC11370360.0")


def test_parse_pmcid_rejects_non_numeric_version() -> None:
    with pytest.raises(ValueError):
        parse_pmcid("PMC11370360.Z")


def test_parse_pmcid_rejects_multiple_version_separators() -> None:
    with pytest.raises(ValueError):
        parse_pmcid("PMC11370360.1.2")
