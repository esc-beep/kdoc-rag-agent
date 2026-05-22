"""Upstage API adapter with explicit mock support."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

from .models import ParsedDocument


class UpstageConfigurationError(RuntimeError):
    pass


class UpstageClient:
    def __init__(
        self,
        api_key: str | None = None,
        fixture_dir: Path | str = "tests/fixtures",
        chat_url: str | None = None,
        parse_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        load_dotenv(dotenv_path=Path.cwd() / ".env")
        self.api_key = api_key or os.getenv("UPSTAGE_API_KEY")
        self.fixture_dir = Path(fixture_dir)
        self.mock = os.getenv("KOBRIDGE_MOCK", "").casefold() == "true"
        self.chat_url = chat_url or os.getenv(
            "UPSTAGE_CHAT_URL", "https://api.upstage.ai/v1/chat/completions"
        )
        self.parse_url = parse_url or os.getenv(
            "UPSTAGE_DOCUMENT_PARSE_URL", "https://api.upstage.ai/v1/document-ai/document-parse"
        )
        self.model = model or os.getenv("UPSTAGE_SOLAR_MODEL", "solar-pro3")
        self.timeout = timeout

    def parse_document(self, file_path: Path | str, mode: str = "standard") -> ParsedDocument:
        if self.mock:
            payload = self._read_fixture("document_parse.json")
            return _parsed_document_from_payload(payload)
        self._ensure_api_key()
        path = Path(file_path)
        with path.open("rb") as file_handle:
            response = httpx.post(
                self.parse_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"ocr": "auto", "output_formats": "markdown", "model": mode},
                files={"document": (path.name, file_handle, "application/pdf")},
                timeout=self.timeout,
            )
        response.raise_for_status()
        return _parsed_document_from_payload(response.json())

    def chat_json(
        self,
        system: str,
        user: str,
        schema_hint: str | None = None,
        fixture_name: str = "chat_extract_knowledge.json",
    ) -> dict[str, Any]:
        if self.mock:
            return self._read_fixture(fixture_name)
        self._ensure_api_key()
        prompt = user if schema_hint is None else f"{user}\n\nReturn JSON matching this shape:\n{schema_hint}"
        response = httpx.post(
            self.chat_url,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return _loads_json_content(content)

    def _ensure_api_key(self) -> None:
        if not self.api_key:
            raise UpstageConfigurationError(
                "UPSTAGE_API_KEY is required. For offline tests or demos, set KOBRIDGE_MOCK=true."
            )

    def _read_fixture(self, name: str) -> dict[str, Any]:
        path = self.fixture_dir / name
        return json.loads(path.read_text(encoding="utf-8"))


def _parsed_document_from_payload(payload: dict[str, Any]) -> ParsedDocument:
    content = payload.get("content", payload)
    markdown = (
        content.get("markdown")
        or payload.get("markdown")
        or payload.get("text")
        or content.get("text")
        or ""
    )
    title = payload.get("title") or content.get("title")
    return ParsedDocument(markdown=markdown, title=title, metadata=payload)


def _loads_json_content(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        stripped = stripped.removeprefix("json").strip()
    return json.loads(stripped)
