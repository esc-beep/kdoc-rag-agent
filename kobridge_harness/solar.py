"""Solar prompts used by the document wiki pipeline."""

from __future__ import annotations

from typing import Protocol

from .upstage import UpstageClient


class SolarLike(Protocol):
    def extract_knowledge(self, markdown: str) -> dict: ...

    def build_answer(self, question: str, compact_context: str) -> dict: ...


class SolarService:
    def __init__(self, client: UpstageClient) -> None:
        self.client = client

    def extract_knowledge(self, markdown: str) -> dict:
        return self.client.chat_json(
            "You extract reusable Korean document knowledge for a Markdown wiki.",
            markdown,
            schema_hint=(
                '{"summary": "string", "concepts": [{"name": "string", '
                '"definition": "string", "summary": "string", "links": ["string"], '
                '"sources": ["string"], "practical_use": "string"}], "entities": []}'
            ),
            fixture_name="chat_extract_knowledge.json",
        )

    def build_answer(self, question: str, compact_context: str) -> dict:
        return self.client.chat_json(
            "Answer in Korean using only the provided cited context. Do not guess.",
            f"Question:\n{question}\n\nContext:\n{compact_context}",
            schema_hint='{"answer": "string", "evidence": ["string"]}',
            fixture_name="chat_answer.json",
        )
