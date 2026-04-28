from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PMCVersions(BaseModel):
    pmcid: str
    versions: list[str]


class PMCMetadata(BaseModel):
    pmcid: str
    version: int
    pmid: int | None = None
    doi: str | None = None
    mid: str | None = None
    title: str | None = None
    citation: str | None = None
    is_pmc_openaccess: bool
    is_manuscript: bool
    is_historical_ocr: bool
    is_retracted: bool
    license_code: str | None = None
    xml_url: str
    pdf_url: str | None = None
    media_urls: list[str] = Field(default_factory=list)
    text_url: str


class PMCFiles(BaseModel):
    versioned_pmcid: str
    keys: list[str]


class FetchAction(str, Enum):
    DOWNLOADED = "downloaded"
    SKIPPED = "skipped"


class PMCFetchFile(BaseModel):
    key: str
    local_path: str
    action: FetchAction


class PMCFetchResult(BaseModel):
    versioned_pmcid: str
    cache_dir: str
    files: list[PMCFetchFile]


class PMCParseResult(BaseModel):
    versioned_pmcid: str
    xml_path: str
    data: dict[str, Any]
