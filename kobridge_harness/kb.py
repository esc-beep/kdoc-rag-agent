"""Markdown KB and metadata persistence."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .models import Chunk, KnowledgeItem
from .text import slugify_name


class KnowledgeBase:
    def __init__(self, root: Path | str = "kb") -> None:
        self.root = Path(root)

    @property
    def db_path(self) -> Path:
        return self.root / "meta.db"

    def initialize(self) -> None:
        for directory in ["concepts", "entities", "sources", "chunks", "pending-updates"]:
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        self._write_once("SCHEMA.md", _schema_text())
        self._write_once("index.md", "# KoBridge KB Index\n\n")
        self._write_once("log.md", "# KoBridge KB Log\n\n")
        self._init_db()

    def add_document(
        self,
        source_path: str,
        title: str,
        doc_type: str,
        chunks: list[Chunk],
        concepts: list[KnowledgeItem],
        entities: list[KnowledgeItem],
        summary: str,
    ) -> str:
        self.initialize()
        doc_id = slugify_name(title or Path(source_path).stem)
        source_md = self.root / "sources" / f"{doc_id}.md"
        source_md.write_text(f"# {title}\n\n## Summary\n{summary}\n\nSource: `{source_path}`\n", encoding="utf-8")

        with self._connect() as conn:
            conn.execute(
                "insert or replace into documents(id, path, title, doc_type, parse_status, ingested_at) values (?, ?, ?, ?, ?, ?)",
                (doc_id, source_path, title, doc_type, "parsed", _now()),
            )
            for item in concepts:
                self._write_knowledge_item("concepts", item)
                conn.execute(
                    "insert or replace into concepts(name, slug, definition, links_json, sources_json) values (?, ?, ?, ?, ?)",
                    (
                        item.name,
                        slugify_name(item.name),
                        item.definition,
                        json.dumps(item.links, ensure_ascii=False),
                        json.dumps(item.sources, ensure_ascii=False),
                    ),
                )
            for item in entities:
                self._write_knowledge_item("entities", item)
            conn.commit()

        if chunks:
            self.add_chunks(doc_id, chunks)
        self._rebuild_index(concepts, entities)
        self.append_log(f"Ingested `{source_path}` as `{doc_id}` with {len(chunks)} chunks.")
        return doc_id

    def add_chunks(self, doc_id: str, chunks: list[Chunk | dict]) -> None:
        self.initialize()
        normalized = [_coerce_chunk(chunk) for chunk in chunks]
        chunk_path = self.root / "chunks" / f"{doc_id}.jsonl"
        with chunk_path.open("a", encoding="utf-8") as file_handle, self._connect() as conn:
            for chunk in normalized:
                file_handle.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")
                conn.execute(
                    "insert or replace into chunks(id, doc_id, heading, page, text, keywords_json, source_path) values (?, ?, ?, ?, ?, ?, ?)",
                    (
                        chunk.id,
                        chunk.doc_id,
                        chunk.heading,
                        chunk.page,
                        chunk.text,
                        json.dumps(chunk.keywords, ensure_ascii=False),
                        chunk.source_path,
                    ),
                )
            conn.commit()

    def load_chunks(self) -> list[Chunk]:
        self.initialize()
        with self._connect() as conn:
            rows = conn.execute(
                "select id, doc_id, heading, page, text, keywords_json, source_path from chunks"
            ).fetchall()
        return [
            Chunk(
                id=row["id"],
                doc_id=row["doc_id"],
                heading=row["heading"],
                page=row["page"],
                text=row["text"],
                source_path=row["source_path"],
                keywords=json.loads(row["keywords_json"] or "[]"),
            )
            for row in rows
        ]

    def append_log(self, message: str) -> None:
        self.initialize()
        with (self.root / "log.md").open("a", encoding="utf-8") as file_handle:
            file_handle.write(f"- {_now()} {message}\n")

    def save_pending_update(self, question: str, answer: str, compact_context: str) -> Path:
        self.initialize()
        path = self.root / "pending-updates" / f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.md"
        path.write_text(
            f"# Pending KB Update\n\n## Question\n{question}\n\n## Answer\n{answer}\n\n## Compact Context\n{compact_context}\n",
            encoding="utf-8",
        )
        self.append_log(f"Saved pending update `{path.relative_to(self.root)}`.")
        return path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                create table if not exists documents (
                    id text primary key,
                    path text not null,
                    title text not null,
                    doc_type text not null,
                    parse_status text not null,
                    ingested_at text not null
                );
                create table if not exists chunks (
                    id text primary key,
                    doc_id text not null,
                    heading text not null,
                    page integer,
                    text text not null,
                    keywords_json text not null,
                    source_path text not null
                );
                create table if not exists concepts (
                    name text primary key,
                    slug text not null,
                    definition text not null,
                    links_json text not null,
                    sources_json text not null
                );
                """
            )
            conn.commit()

    def _write_once(self, relative_path: str, content: str) -> None:
        path = self.root / relative_path
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    def _write_knowledge_item(self, folder: str, item: KnowledgeItem) -> None:
        path = self.root / folder / f"{slugify_name(item.name)}.md"
        links = "\n".join(f"- [[{link}]]" for link in item.links) or "- 없음"
        sources = "\n".join(f"- [{source}]({source})" for source in item.sources) or "- 없음"
        path.write_text(
            f"# {item.name}\n\n"
            f"## 정의\n{item.definition}\n\n"
            f"## 핵심 내용\n{item.summary}\n\n"
            f"## 관련 개념\n{links}\n\n"
            f"## 출처\n{sources}\n\n"
            f"## 실용 적용\n{item.practical_use or '문서 기반 Agent context 생성'}\n",
            encoding="utf-8",
        )

    def _rebuild_index(self, concepts: list[KnowledgeItem], entities: list[KnowledgeItem]) -> None:
        lines = ["# KoBridge KB Index", "", "## Concepts"]
        lines.extend(f"- [[{item.name}]]: {item.definition}" for item in concepts)
        lines.extend(["", "## Entities"])
        lines.extend(f"- [[{item.name}]]: {item.definition}" for item in entities)
        lines.append("")
        (self.root / "index.md").write_text("\n".join(lines), encoding="utf-8")


def _coerce_chunk(value: Chunk | dict) -> Chunk:
    if isinstance(value, Chunk):
        return value
    return Chunk(**value)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _schema_text() -> str:
    return """# KoBridge KB Schema

## Directories
- `sources/`: source document summaries and metadata
- `chunks/`: JSONL chunk store for runtime BM25 retrieval
- `concepts/`: reusable concept pages
- `entities/`: people, organizations, tools, and projects
- `pending-updates/`: user-approved candidates from query sessions

## Concept Template
# [Concept]
## 정의
## 핵심 내용
## 관련 개념
## 출처
## 실용 적용
"""
