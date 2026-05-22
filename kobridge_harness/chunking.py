"""Markdown chunking for KB ingestion."""

from __future__ import annotations

import re
from pathlib import Path

from .models import Chunk


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def chunk_markdown(markdown: str, source_path: str, max_chars: int = 1800) -> list[Chunk]:
    sections = _split_sections(markdown)
    doc_id = Path(source_path).stem
    chunks: list[Chunk] = []
    counter = 1
    for heading, body in sections:
        section_text = body.strip()
        if not section_text:
            continue
        for part in _split_long_text(section_text, max_chars=max_chars):
            chunks.append(
                Chunk(
                    id=f"{doc_id}-{counter:03d}",
                    doc_id=doc_id,
                    heading=heading,
                    text=part.strip(),
                    source_path=source_path,
                )
            )
            counter += 1
    if not chunks and markdown.strip():
        chunks.append(
            Chunk(
                id=f"{doc_id}-001",
                doc_id=doc_id,
                heading=Path(source_path).stem,
                text=markdown.strip(),
                source_path=source_path,
            )
        )
    return chunks


def _split_sections(markdown: str) -> list[tuple[str, str]]:
    matches = list(HEADING_RE.finditer(markdown))
    if not matches:
        return [("Document", markdown)]

    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        heading = match.group(2).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()
        if body:
            sections.append((heading, body))
    return sections


def _split_long_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?。！？\n])\s+", text)
    parts: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                parts.append(current.strip())
                current = ""
            parts.extend(sentence[i : i + max_chars] for i in range(0, len(sentence), max_chars))
            continue
        candidate = f"{current} {sentence}".strip()
        if len(candidate) > max_chars and current:
            parts.append(current.strip())
            current = sentence
        else:
            current = candidate
    if current:
        parts.append(current.strip())
    return parts
