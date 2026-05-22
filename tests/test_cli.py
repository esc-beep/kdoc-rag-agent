from typer.testing import CliRunner

from kobridge_harness.cli import app


def test_cli_ingest_and_query_work_in_explicit_mock_mode(monkeypatch, tmp_path):
    monkeypatch.setenv("KOBRIDGE_MOCK", "true")
    source = tmp_path / "demo.md"
    kb_path = tmp_path / "kb"
    source.write_text(
        "# Context Compaction\n\n긴 한국어 입력에서 핵심 요구사항과 제약조건만 남깁니다.",
        encoding="utf-8",
    )
    runner = CliRunner()

    ingest_result = runner.invoke(app, ["ingest", str(source), "--kb", str(kb_path), "--json"])
    query_result = runner.invoke(
        app,
        ["query", "Context Compaction이 왜 필요한가?", "--kb", str(kb_path), "--json"],
    )

    assert ingest_result.exit_code == 0
    assert '"concept_count": 1' in ingest_result.output
    assert query_result.exit_code == 0
    assert "핵심 정보만 남겨 Agent가 쓸 수 있게 합니다" in query_result.output
