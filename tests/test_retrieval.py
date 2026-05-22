from kobridge_harness.models import Chunk
from kobridge_harness.retrieval import retrieve_chunks, tokenize_korean


def test_tokenize_korean_extracts_korean_and_english_terms():
    tokens = tokenize_korean("Context Compaction이 왜 필요한가요?")

    assert "context" in tokens
    assert "compaction" in tokens
    assert "필요" in tokens or "필요한가요" in tokens


def test_retrieve_chunks_ranks_relevant_korean_chunk_first():
    chunks = [
        Chunk(
            id="c1",
            doc_id="doc",
            heading="Context Compaction",
            text="Context Compaction은 긴 한국어 입력에서 핵심 요구사항과 제약조건만 남깁니다.",
            source_path="sources/a.md",
            page=None,
            keywords=["context", "compaction"],
        ),
        Chunk(
            id="c2",
            doc_id="doc",
            heading="Document Parse",
            text="Document Parse는 PDF의 표와 헤더 구조를 Markdown으로 변환합니다.",
            source_path="sources/a.md",
            page=None,
            keywords=["document", "parse"],
        ),
    ]

    results = retrieve_chunks("Context Compaction이 왜 필요한가?", chunks, limit=1)

    assert results[0].chunk.id == "c1"
    assert results[0].score > 0
    assert "context" in results[0].matched_terms
