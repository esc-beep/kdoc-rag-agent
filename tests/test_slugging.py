from kobridge_harness.text import slugify_name


def test_slugify_preserves_readable_korean_and_normalizes_symbols():
    assert slugify_name("Context Compaction / 한국어 RAG!") == "context-compaction-한국어-rag"


def test_slugify_falls_back_for_empty_names():
    assert slugify_name("!!!") == "untitled"
