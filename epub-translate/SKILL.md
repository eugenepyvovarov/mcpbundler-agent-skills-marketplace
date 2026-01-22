---
name: epub-translate
description: Translate EPUB (.epub) ebooks to another language by unpacking the EPUB container, extracting XHTML block-level fragments into JSONL translation units, translating them via the OpenAI Responses API (e.g. gpt-5.1 / gpt-5-mini) while preserving markup, updating language metadata, and repackaging a valid EPUB (mimetype-first and uncompressed). Use when Codex needs to translate and rebuild EPUB files.
---

# EPUB Translate

## Workflow
1. One-time setup (writes `.skills-data/epub-translate/.env`): `scripts/epub-translate setup`
2. Extract translation units: `scripts/epub-translate extract --epub /path/book.epub`
3. Translate via OpenAI API: `scripts/epub-translate translate --job-dir <job-dir> --target-lang <bcp47> [--fraction 0.1]`
4. Apply + repack: `scripts/epub-translate apply --job-dir <job-dir> --translations <job-dir>/translations.jsonl --target-lang <bcp47> --out-epub /path/book.<bcp47>.epub`
5. Optional: validate output: `scripts/epub-translate validate --epub /path/book.<bcp47>.epub`

## Commands
- `scripts/epub-translate setup`:
  - Prompts for `OPENAI_API_KEY` (saved to `.skills-data/epub-translate/.env`).
  - Prompts for default `OPENAI_MODEL` (e.g. `gpt-5.1`, `gpt-5-mini`).
- `scripts/epub-translate extract ...`:
  - Unzips the EPUB into a per-run job dir under `.skills-data/epub-translate/tmp/`.
  - Parses `META-INF/container.xml` → package document (`.opf`) → manifest/spine.
  - Extracts XHTML `<head><title>` and leaf block-level XHTML fragments (inner HTML) in reading order into `units.jsonl`.
  - Optional: include OPF `dc:title` via `--include-opf-title`.
- `scripts/epub-translate translate ...`:
  - Reads `<job-dir>/units.jsonl` and writes `<job-dir>/translations.jsonl`.
  - Uses the OpenAI Responses API (`https://api.openai.com/v1/responses`).
  - Resume-safe by default: if `translations.jsonl` already contains some ids, they are skipped.
- `scripts/epub-translate apply ...`:
  - Applies translated fragments back into the unpacked XHTML files.
  - Updates `dc:language` in the OPF and `xml:lang` in the XHTML.
  - Repackages as a valid EPUB (writes `mimetype` first, stored/uncompressed).
- `scripts/epub-translate validate ...`: checks basic EPUB container invariants.

## JSONL formats
`units.jsonl` (input to translation) has one JSON object per line, e.g.:
```json
{"id":1,"kind":"xhtml-fragment","doc_path":"EPUB/chapter1.xhtml","xpath":"/html[1]/body[1]/p[3]","tag":"p","source_inner_html":"Hello <em>world</em>!","source_markup_hash":"..."}
```

`translations.jsonl` (output from translation) must contain:
```json
{"id":1,"translated_inner_html":"Hola <em>mundo</em>!"}
```

## Translation rules (markup-safe)
- Translate only human-readable text, not markup.
- Do not change any tags, nesting, attribute names, attribute values, URLs, IDs, or filenames.
- Keep entities/character references as-is (e.g. `&amp;`, `&#160;`).
- If a fragment contains non-translatable text (code, formulas, URLs), leave it unchanged.

## Local data and env
- Store all mutable state under <project_root>/.skills-data/<skill-name>/.
- Keep config and registries in .skills-data/<skill-name>/ (for example: config.json, <feature>.json).
- Use .skills-data/<skill-name>/.env for SKILL_ROOT, SKILL_DATA_DIR, and any per-skill env keys.
- Install local tools into .skills-data/<skill-name>/bin and prepend it to PATH when needed.
- Install dependencies under .skills-data/<skill-name>/venv:
  - Python: .skills-data/<skill-name>/venv/python
  - Node: .skills-data/<skill-name>/venv/node_modules
  - Go: .skills-data/<skill-name>/venv/go (modcache, gocache)
  - PHP: .skills-data/<skill-name>/venv/php (cache, vendor)
- Write logs/cache/tmp under .skills-data/<skill-name>/logs, .skills-data/<skill-name>/cache, .skills-data/<skill-name>/tmp.
- Keep automation in <skill-root>/scripts and read SKILL_DATA_DIR (default to <project_root>/.skills-data/<skill-name>/).
- Do not write outside <skill-root> and <project_root>/.skills-data/<skill-name>/ unless the user requests it.

### OpenAI config keys
Stored in `.skills-data/epub-translate/.env` (created by `scripts/epub-translate setup`):
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default: `gpt-5-mini`; change via `setup --model ...`, editing `.env`, or `translate --model ...`)
- `OPENAI_BASE_URL` (default: `https://api.openai.com/v1`)
- `OPENAI_REASONING_EFFORT` (default: `low`; change via `setup --reasoning-effort ...` or editing `.env`)
