"""NCBI PMC ID Converter client."""

from collections.abc import Sequence
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ID_CONVERTER_URL = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"


def convert_to_pmcids(
    identifiers: Sequence[str],
    *,
    idtype: str | None = None,
    email: str | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    params = {
        "tool": "pmc_toolkit",
        "format": "json",
        "ids": ",".join(identifiers),
    }
    if idtype:
        params["idtype"] = idtype
    if email:
        params["email"] = email

    url = f"{ID_CONVERTER_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "pmc-toolkit"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(
            f"ID converter request failed with HTTP {exc.code}."
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"ID converter request failed: {exc.reason}.") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("ID converter returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("ID converter returned an unexpected response.")
    return payload
