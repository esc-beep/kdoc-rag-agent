from kobridge_harness.chunking import chunk_markdown


def test_chunk_markdown_splits_by_headings_and_keeps_source_metadata():
    markdown = """# 문서 제목

도입 문단입니다.

## Context Compaction

긴 한국어 입력을 핵심 정보만 남긴 compact context로 줄입니다.

## RAG Retrieval

질문과 관련된 chunk를 검색합니다.
"""

    chunks = chunk_markdown(markdown, source_path="sources/demo.md", max_chars=120)

    assert [chunk.heading for chunk in chunks] == [
        "문서 제목",
        "Context Compaction",
        "RAG Retrieval",
    ]
    assert chunks[1].source_path == "sources/demo.md"
    assert "compact context" in chunks[1].text


def test_chunk_markdown_splits_long_sections_without_losing_heading():
    markdown = "# 긴 섹션\n\n" + ("한국어 검색 품질을 높이기 위한 내용입니다. " * 20)

    chunks = chunk_markdown(markdown, source_path="sources/long.md", max_chars=150)

    assert len(chunks) > 1
    assert {chunk.heading for chunk in chunks} == {"긴 섹션"}
    assert all(len(chunk.text) <= 180 for chunk in chunks)
