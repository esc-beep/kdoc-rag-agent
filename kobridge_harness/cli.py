"""Command line interface for KoBridge Harness."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import typer
from rich.console import Console

from .kb import KnowledgeBase
from .pipeline import ingest_markdown, ingest_text_document, query_kb
from .solar import SolarService
from .upstage import UpstageClient


app = typer.Typer(help="KoBridge Korean Document Wiki Agent / RAG Context Builder")
console = Console()


@app.command()
def ingest(
    file: Path,
    kb_path: Path = typer.Option(Path("kb"), "--kb", help="Knowledge base directory."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    kb = KnowledgeBase(kb_path)
    solar = SolarService(UpstageClient())
    if file.suffix.casefold() == ".pdf":
        parsed = solar.client.parse_document(file)
        result = ingest_markdown(parsed.markdown, str(file), parsed.title or file.stem, "pdf", kb, solar)
    else:
        result = ingest_text_document(file, kb, solar)
    _print(asdict(result), json_output)


@app.command()
def query(
    question: str,
    kb_path: Path = typer.Option(Path("kb"), "--kb", help="Knowledge base directory."),
    save: bool = typer.Option(False, "--save", help="Save answer as a pending KB update."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    kb = KnowledgeBase(kb_path)
    solar = SolarService(UpstageClient())
    result = query_kb(kb, question, solar, save=save)
    if json_output:
        _print(asdict(result), True)
        return
    console.print(f"[bold]Answer[/bold]\n{result.answer}\n")
    console.print("[bold]Sources[/bold]")
    for citation in result.citations:
        console.print(f"- {citation}")
    console.print("\n[bold]Compact Context[/bold]")
    console.print(result.compact_context)


@app.command()
def stats(kb_path: Path = typer.Option(Path("kb"), "--kb", help="Knowledge base directory.")) -> None:
    kb = KnowledgeBase(kb_path)
    chunks = kb.load_chunks()
    concept_count = len(list((kb.root / "concepts").glob("*.md")))
    entity_count = len(list((kb.root / "entities").glob("*.md")))
    console.print(f"Chunks: {len(chunks)}")
    console.print(f"Concepts: {concept_count}")
    console.print(f"Entities: {entity_count}")


def _print(payload: dict, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for key, value in payload.items():
            console.print(f"{key}: {value}")
