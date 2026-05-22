"""Keyword and BM25 retrieval over Markdown KB chunks."""

from __future__ import annotations

import re
from collections import Counter

from rank_bm25 import BM25Okapi

from .models import Chunk, RetrievalResult

try:  # pragma: no cover - optional speed/quality path
    from kiwipiepy import Kiwi
except Exception:  # pragma: no cover - optional dependency
    Kiwi = None


_KIWI = Kiwi() if Kiwi else None


def tokenize_korean(text: str) -> list[str]:
    lowered = text.casefold()
    tokens: list[str] = []
    if _KIWI:
        for token in _KIWI.tokenize(lowered):
            if token.tag.startswith(("N", "V", "SL", "SN")) and len(token.form) >= 2:
                tokens.append(token.form)
    else:
        tokens.extend(re.findall(r"[a-z0-9]+|[가-힣]{2,}", lowered))

    expanded: list[str] = []
    for token in tokens:
        expanded.append(token)
        if "필요" in token and token != "필요":
            expanded.append("필요")
        if token.endswith(("합니다", "합니다.", "합니다요")) and len(token) > 3:
            expanded.append(token.removesuffix("합니다").removesuffix("요"))
    return _dedupe(expanded)


def retrieve_chunks(query: str, chunks: list[Chunk], limit: int = 5) -> list[RetrievalResult]:
    if not chunks:
        return []

    query_tokens = tokenize_korean(query)
    corpus = [_chunk_tokens(chunk) for chunk in chunks]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query_tokens)

    results: list[RetrievalResult] = []
    for chunk, tokens, score in zip(chunks, corpus, scores, strict=True):
        matched = [term for term in query_tokens if term in tokens]
        fallback = sum(Counter(tokens)[term] for term in matched)
        final_score = float(score) if score > 0 else float(fallback)
        if final_score > 0:
            results.append(RetrievalResult(chunk=chunk, score=final_score, matched_terms=matched))

    results.sort(key=lambda item: item.score, reverse=True)
    return results[:limit]


def _chunk_tokens(chunk: Chunk) -> list[str]:
    joined = " ".join([chunk.heading, chunk.text, *chunk.keywords])
    return tokenize_korean(joined)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            deduped.append(value)
            seen.add(value)
    return deduped
