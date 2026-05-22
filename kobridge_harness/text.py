"""Text normalization helpers."""

from __future__ import annotations

import re
import unicodedata


def slugify_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = normalized.replace("_", "-")
    slug = re.sub(r"[^\w가-힣]+", "-", normalized, flags=re.UNICODE)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "untitled"


def estimate_tokens(text: str) -> int:
    # Rough demo metric: Korean chars tend to be costlier, but this keeps stats
    # deterministic without requiring tokenizer-specific dependencies.
    if not text:
        return 0
    korean_chars = len(re.findall(r"[가-힣]", text))
    other_terms = len(re.findall(r"[A-Za-z0-9_]+", text))
    return korean_chars + other_terms
