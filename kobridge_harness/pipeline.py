"""Ingest and query orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .chunking import chunk_markdown
from .kb import KnowledgeBase
from .models import AnswerResult, KnowledgeItem
from .retrieval import retrieve_chunks
from .solar import SolarLike
from .text import estimate_tokens


@dataclass(slots=True)
class IngestResult:
    doc_id: str
    concept_count: int
    entity_count: int
    chunk_count: int


def ingest_text_document(source: Path | str, kb: KnowledgeBase, solar: SolarLike) -> IngestResult:
    path = Path(source)
    markdown = path.read_text(encoding="utf-8")
    return ingest_markdown(markdown, source_path=str(path), title=path.stem, doc_type=path.suffix.lstrip("."), kb=kb, solar=solar)


def ingest_markdown(
    markdown: str,
    source_path: str,
    title: str,
    doc_type: str,
    kb: KnowledgeBase,
    solar: SolarLike,
) -> IngestResult:
    knowledge = solar.extract_knowledge(markdown)
    concepts = [_knowledge_item(item, fallback_source=source_path) for item in knowledge.get("concepts", [])]
    entities = [_knowledge_item(item, fallback_source=source_path) for item in knowledge.get("entities", [])]
    chunks = chunk_markdown(markdown, source_path=source_path)
    summary = knowledge.get("summary", "")
    doc_id = kb.add_document(
        source_path=source_path,
        title=title,
        doc_type=doc_type,
        chunks=chunks,
        concepts=concepts,
        entities=entities,
        summary=summary,
    )
    return IngestResult(doc_id=doc_id, concept_count=len(concepts), entity_count=len(entities), chunk_count=len(chunks))


def query_kb(kb: KnowledgeBase, question: str, solar: SolarLike, save: bool = False, limit: int = 5) -> AnswerResult:
    chunks = kb.load_chunks()
    results = retrieve_chunks(question, chunks, limit=limit)
    if not results:
        return AnswerResult(
            answer="KB에서 충분한 근거를 찾지 못했습니다.",
            compact_context="",
            citations=[],
            token_stats={"retrieved_tokens": 0, "compact_context_tokens": 0},
        )

    compact_context = build_compact_context(question, results)
    answer_payload = solar.build_answer(question, compact_context)
    citations = sorted({result.chunk.source_path for result in results})
    answer = answer_payload.get("answer", "KB에서 충분한 근거를 찾지 못했습니다.")
    if save:
        kb.save_pending_update(question, answer, compact_context)
    return AnswerResult(
        answer=answer,
        compact_context=compact_context,
        citations=citations,
        token_stats={
            "retrieved_tokens": sum(estimate_tokens(result.chunk.text) for result in results),
            "compact_context_tokens": estimate_tokens(compact_context),
        },
    )


def build_compact_context(question: str, results) -> str:
    lines = [
        "Relevant knowledge for Korean document QA.",
        f"User question: {question}",
        "",
        "Relevant Chunks:",
    ]
    for index, result in enumerate(results, start=1):
        chunk = result.chunk
        lines.extend(
            [
                f"{index}. {chunk.heading}",
                f"   Source: {chunk.source_path}",
                f"   Relevance: {result.score:.3f}",
                f"   Content: {chunk.text}",
            ]
        )
    lines.extend(["", "Answer in Korean. Cite only the listed sources."])
    return "\n".join(lines)


def _knowledge_item(payload: dict, fallback_source: str) -> KnowledgeItem:
    sources = payload.get("sources") or [fallback_source]
    return KnowledgeItem(
        name=payload.get("name", "Untitled"),
        definition=payload.get("definition", ""),
        summary=payload.get("summary", ""),
        links=list(payload.get("links", [])),
        sources=list(sources),
        practical_use=payload.get("practical_use", ""),
    )
