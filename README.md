# KoBridge Harness

Korean Document Wiki Agent / RAG Context Builder prototype.

The MVP is a Python CLI harness that turns Korean PDF, Markdown, and text
documents into a reusable Markdown knowledge base, retrieves relevant chunks,
and builds compact agent-ready context with source citations.

## Setup

```bash
uv sync --extra dev
```

For optional Korean morphological tokenization:

```bash
uv sync --extra dev --extra korean
```

## Offline Demo

The CLI never silently falls back to fake API data. To use fixture-backed demo
responses, explicitly enable mock mode:

```bash
export KOBRIDGE_MOCK=true
uv run kobridge ingest path/to/document.md --kb kb --json
uv run kobridge query "Context Compaction이 왜 필요한가?" --kb kb --json
uv run kobridge stats --kb kb
```

Mock mode reads JSON fixtures from `tests/fixtures/`.

## Real Upstage API Mode

Copy `.env.example` to `.env` or export the variables directly:

```bash
export UPSTAGE_API_KEY=...
export KOBRIDGE_MOCK=false
```

Then ingest PDFs through Document Parse and answer from the generated KB:

```bash
uv run kobridge ingest "한국어 문서.pdf" --kb kb
uv run kobridge query "이 문서에서 RAG를 쓸 때 주의할 점은?" --kb kb
```

## Generated KB Shape

```text
kb/
├── SCHEMA.md
├── index.md
├── log.md
├── meta.db
├── sources/
├── chunks/
├── concepts/
├── entities/
└── pending-updates/
```

`sources/`, `concepts/`, and `entities/` are human-readable Markdown. `meta.db`
stores metadata for stats and runtime retrieval. BM25 is built at query time
from the stored chunks.

## Safety Defaults

- Query sessions are read-only by default.
- `kobridge query --save` writes proposed updates to `pending-updates/` rather
  than directly editing concept/entity pages.
- If `UPSTAGE_API_KEY` is missing and `KOBRIDGE_MOCK=true` is not set, the CLI
  fails with an explicit configuration message.
