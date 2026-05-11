from pydantic import BaseModel


class SerpResult(BaseModel):
    position: int
    url: str
    title: str
    snippet: str


class ScrapedPage(BaseModel):
    url: str
    position: int
    h1: str
    meta_title: str
    meta_description: str
    site_structure: list[str] = []
    error: str | None = None


class SheetRow(BaseModel):
    row_index: int
    keyword: str
    geo: str
    language: str
    result: str = ""


class GeneratedMeta(BaseModel):
    h1: str
    meta_title: str
    meta_description: str
