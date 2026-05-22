from pathlib import Path

import pytest

from kobridge_harness.upstage import UpstageClient, UpstageConfigurationError


def test_client_requires_explicit_mock_mode_when_api_key_is_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("UPSTAGE_API_KEY", raising=False)
    monkeypatch.delenv("KOBRIDGE_MOCK", raising=False)
    monkeypatch.chdir(tmp_path)

    client = UpstageClient(fixture_dir=tmp_path)

    with pytest.raises(UpstageConfigurationError, match="KOBRIDGE_MOCK=true"):
        client.chat_json("system", "user")


def test_client_loads_api_key_from_dotenv_file(monkeypatch, tmp_path):
    monkeypatch.delenv("UPSTAGE_API_KEY", raising=False)
    monkeypatch.delenv("KOBRIDGE_MOCK", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("UPSTAGE_API_KEY=from-dotenv\n", encoding="utf-8")

    client = UpstageClient(fixture_dir=tmp_path)

    assert client.api_key == "from-dotenv"


def test_client_uses_upstage_chat_completion_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("UPSTAGE_API_KEY", "test-key")
    monkeypatch.delenv("UPSTAGE_CHAT_URL", raising=False)
    monkeypatch.delenv("UPSTAGE_SOLAR_MODEL", raising=False)
    monkeypatch.chdir(tmp_path)

    client = UpstageClient(fixture_dir=tmp_path)

    assert client.chat_url == "https://api.upstage.ai/v1/chat/completions"
    assert client.model == "solar-pro3"


def test_client_reads_mock_chat_response_when_mock_mode_enabled(monkeypatch, tmp_path):
    monkeypatch.delenv("UPSTAGE_API_KEY", raising=False)
    monkeypatch.setenv("KOBRIDGE_MOCK", "true")
    fixture = tmp_path / "chat_extract_knowledge.json"
    fixture.write_text('{"summary":"요약","concepts":[],"entities":[]}', encoding="utf-8")

    client = UpstageClient(fixture_dir=tmp_path)

    assert client.chat_json("system", "user", fixture_name="chat_extract_knowledge.json") == {
        "summary": "요약",
        "concepts": [],
        "entities": [],
    }


def test_client_reads_mock_parse_response_when_mock_mode_enabled(monkeypatch, tmp_path):
    monkeypatch.setenv("KOBRIDGE_MOCK", "true")
    fixture = tmp_path / "document_parse.json"
    fixture.write_text('{"content":{"markdown":"# Parsed"}}', encoding="utf-8")
    source = tmp_path / "demo.pdf"
    source.write_bytes(b"%PDF")

    client = UpstageClient(fixture_dir=tmp_path)

    assert client.parse_document(source).markdown == "# Parsed"
