# EPUB Translate (Codex skill)

Translate `.epub` ebooks to another language by unpacking the EPUB container, extracting block-level XHTML fragments into JSONL translation units, translating them via the OpenAI Responses API, and repackaging a valid EPUB while preserving markup.

## What it does
- Unpacks an EPUB (zip), reads `META-INF/container.xml`, parses the OPF, and follows the spine (reading order).
- Extracts translation units (XHTML `<title>` + leaf block-level fragments like `p`, `li`, headings, etc.) into `units.jsonl`.
- Translates `units.jsonl` to `translations.jsonl` via `https://api.openai.com/v1/responses` (resume-safe by default).
- Applies translations back into the unpacked XHTML, updates OPF/XHTML language metadata, and repacks a standards-compliant EPUB (`mimetype` first, stored/uncompressed).
- Validates basic EPUB container invariants.

## Quickstart
1. One-time setup (writes `.skills-data/epub-translate/.env`): `scripts/epub-translate setup`
2. Extract translation units: `scripts/epub-translate extract --epub /path/book.epub`
3. Translate: `scripts/epub-translate translate --job-dir <job-dir> --target-lang <bcp47>`
4. Apply + repack: `scripts/epub-translate apply --job-dir <job-dir> --translations <job-dir>/translations.jsonl --target-lang <bcp47> --out-epub /path/book.<bcp47>.epub`
5. Validate output: `scripts/epub-translate validate --epub /path/book.<bcp47>.epub`

## Requirements
- Python 3 (`scripts/epub-translate` runs `python3`).
- OpenAI API key (set `OPENAI_API_KEY` or run `scripts/epub-translate setup`).
- Network access for translation calls.

## Installation (as a Codex skill)
Copy this folder into your project as: `<project_root>/.codex/skills/epub-translate/` (folder name matters for where the skill stores `.skills-data`).

## Where state is stored
All mutable state lives under your host project:
- `<project_root>/.skills-data/epub-translate/`
  - `.env` (OpenAI config)
  - `tmp/` (per-run job dirs created by `extract`)
  - `cache/` (Python bytecode cache via `PYTHONPYCACHEPREFIX`)

## Notes
- Markup safety is enforced: if a model changes tags/attributes, `apply` fails.
- This is optimized for XHTML-based EPUBs; complex edge cases may require tweaks.
