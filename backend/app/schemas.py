from pydantic import BaseModel, Field, HttpUrl
from typing import Any


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class AnalyzeResponse(BaseModel):
    comparison_id: int | None = None
    product: dict[str, Any]
    retailers: list[dict[str, Any]] = []
    notice: str = ""
    sources: list[dict[str, str]] = []


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1500)
    comparison_id: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict[str, str]] = []


class IngestTextRequest(BaseModel):
    title: str = Field(default="Product notes", min_length=1, max_length=300)
    content: str = Field(min_length=30, max_length=50000)
    source_url: str = Field(default="", max_length=2000)
