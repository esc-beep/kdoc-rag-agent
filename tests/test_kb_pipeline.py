from pathlib import Path

from kobridge_harness.kb import KnowledgeBase
from kobridge_harness.models import KnowledgeItem
from kobridge_harness.pipeline import IngestResult, ingest_text_document, query_kb


class FakeSolar:
    def extract_knowledge(self, markdown: str):
        return {
            "summary": "Context Compaction과 RAG 검색을 설명하는 문서입니다.",
            "concepts": [
                {
                    "name": "Context Compaction",
                    "definition": "긴 입력에서 핵심 정보만 보존하는 과정",
                    "summary": "요구사항, 제약조건, 성공 기준을 보존합니다.",
                    "links": ["RAG Retrieval"],
                    "sources": ["demo.md"],
                    "practical_use": "Agent-ready context 생성",
                }
            ],
            "entities": [],
        }

    def build_answer(self, question: str, compact_context: str):
        return {
            "answer": "Context Compaction은 긴 한국어 문서에서 핵심 정보만 남겨 Agent가 쓸 수 있게 합니다.",
            "evidence": ["Context Compaction"],
        }


def test_ingest_text_document_creates_markdown_kb_and_metadata(tmp_path):
    source = tmp_path / "demo.md"
    source.write_text(
        "# Context Compaction\n\n긴 한국어 입력에서 핵심 요구사항과 제약조건만 남깁니다.",
        encoding="utf-8",
    )
    kb = KnowledgeBase(tmp_path / "kb")

    result = ingest_text_document(source, kb, FakeSolar())

    assert isinstance(result, IngestResult)
    assert (tmp_path / "kb" / "SCHEMA.md").exists()
    assert (tmp_path / "kb" / "index.md").exists()
    assert (tmp_path / "kb" / "concepts" / "context-compaction.md").exists()
    assert (tmp_path / "kb" / "chunks" / "demo.jsonl").exists()
    assert result.concept_count == 1
    assert result.chunk_count >= 1


def test_query_kb_returns_answer_with_citations_without_saving_by_default(tmp_path):
    kb = KnowledgeBase(tmp_path / "kb")
    kb.initialize()
    kb.add_document(
        source_path="sources/demo.md",
        title="demo",
        doc_type="markdown",
        chunks=[],
        concepts=[
            KnowledgeItem(
                name="Context Compaction",
                definition="긴 입력에서 핵심 정보만 보존하는 과정",
                summary="요구사항과 제약조건을 보존합니다.",
                links=[],
                sources=["sources/demo.md"],
                practical_use="Agent-ready context 생성",
            )
        ],
        entities=[],
        summary="요약",
    )
    kb.add_chunks(
        "demo",
        [
            {
                "id": "demo-001",
                "doc_id": "demo",
                "heading": "Context Compaction",
                "text": "Context Compaction은 긴 한국어 입력에서 핵심 요구사항만 남깁니다.",
                "source_path": "sources/demo.md",
                "page": None,
                "keywords": ["context", "compaction", "요구사항"],
            }
        ],
    )
    before_log = (tmp_path / "kb" / "log.md").read_text(encoding="utf-8")

    result = query_kb(kb, "Context Compaction이 왜 필요한가?", FakeSolar(), save=False)

    assert "핵심 정보" in result.answer
    assert result.citations == ["sources/demo.md"]
    assert "Relevant knowledge" in result.compact_context
    assert (tmp_path / "kb" / "log.md").read_text(encoding="utf-8") == before_log
