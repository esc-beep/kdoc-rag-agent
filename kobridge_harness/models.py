"""Shared data models for KoBridge Harness."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ParsedDocument:
    markdown: str
    title: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    id: str
    doc_id: str
    heading: str
    text: str
    source_path: str
    page: int | None = None
    keywords: list[str] = field(default_factory=list)


@dataclass(slots=True)
class KnowledgeItem:
    name: str
    definition: str
    summary: str
    links: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    practical_use: str = ""


@dataclass(slots=True)
class RetrievalResult:
    chunk: Chunk
    score: float
    matched_terms: list[str]


@dataclass(slots=True)
class AnswerResult:
    answer: str
    compact_context: str
    citations: list[str]
    token_stats: dict[str, int] = field(default_factory=dict)
