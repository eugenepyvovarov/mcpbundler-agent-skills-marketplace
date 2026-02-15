---
name: obsidian-vault-manager
description: Manage local Obsidian vaults and markdown notes. Use when Codex needs to connect to local Obsidian vaults, register vault paths, or create/edit/refactor/search notes, frontmatter, links, tags, and attachments within a vault.
---

# Obsidian Vault Manager

## Quick start
- Register or discover vaults with Obsidian CLI first:
  - `python3 scripts/vault_registry.py discover --merge`
  - `python3 scripts/vault_registry.py list`
- Add a vault manually when needed:
  - `python3 scripts/vault_registry.py add --path "/path/to/Vault" --name "Vault"`
- Manage active workspace:
  - `python3 scripts/vault_registry.py set-active --name "Vault"`
  - `python3 scripts/vault_registry.py set-workdir --name "Vault" --workdir "path/inside/vault"`
  - `python3 scripts/vault_registry.py active`
- Run full Obsidian CLI command surface via `obsidian` subcommand (machine-first by default):
  - `python3 scripts/vault_registry.py obsidian --vault "Vault" search query="meeting notes"`
  - `python3 scripts/vault_registry.py obsidian --raw --vault "Vault" read file="Project.md"`
- Enable destructive commands with `--force-delete`:
  - `python3 scripts/vault_registry.py obsidian --force-delete --vault "Vault" delete file="Old.md" permanent`
- Pick a vault and confirm its path contains `.obsidian/` for manual adds.

## Local data and env
- If <skill-root>/.. is `skills`, project_root is two levels above the `skills` folder (<skill-root>/../../..). Confirm with the user if unsure.
- Store all mutable state under <project_root>/.skills-data/obsidian-vault-manager/.
- Keep the vault registry at .skills-data/obsidian-vault-manager/vaults.json.
- Use .skills-data/obsidian-vault-manager/.env for SKILL_ROOT, SKILL_DATA_DIR, and per-skill env keys.
- Install local tools into .skills-data/obsidian-vault-manager/bin and prepend it to PATH when needed.
- Install dependencies under .skills-data/obsidian-vault-manager/venv (python/node/go/php).
- Write logs/cache/tmp under .skills-data/obsidian-vault-manager/logs, .skills-data/obsidian-vault-manager/cache, .skills-data/obsidian-vault-manager/tmp.
- Keep automation in <skill-root>/scripts and do not write outside <skill-root> and <project_root>/.skills-data/obsidian-vault-manager/ unless the user requests it.

## Vault connection workflow
1. Attempt CLI-first discovery with `scripts/vault_registry.py discover`; keep `.skills-data/obsidian-vault-manager/vaults.json` as the skill-owned state.
2. Register or confirm vault entries in `vaults.json`.
3. Set active vault with `scripts/vault_registry.py set-active --name <name>`.
4. Ask the user for default working folder (relative path), defaulting to vault root (`.`).
5. Save it with `scripts/vault_registry.py set-workdir --name <name> --workdir <relative/path>`.
6. Confirm the chosen vault name, vault path, and working folder before edits.

## Working rules
- Use the configured working folder as the default root for searches and edits (do not roam the entire vault unless requested).
- Edit only note content and attachments unless the user asks to change `.obsidian` settings.
- Preserve existing frontmatter keys; add new keys without reordering unless requested.
- Keep internal links valid after rename/move; update `[[Wiki Links]]` and markdown links.
- For `obsidian` passthrough commands, destructive actions require explicit `--force-delete` when supported by the command.
- Confirm before delete, rename, or bulk changes.

## Common tasks
### Search and review
- Use `rg --glob '*.md' <pattern> <vault_path>` to find notes and references.
- Summarize matching files before edits.

### Create a note
- Choose a filename that matches the main title.
- Add YAML frontmatter when needed (tags, aliases, status).
- Save as UTF-8 with a trailing newline.

### Edit or refactor
- Keep headings and block IDs stable unless requested.
- When moving sections across notes, update inbound links and mentions.

### Rename or move
- Rename the file and update links across the vault.
- For wiki links, update `[[Old Name]]` and `[[path/Old Name|alias]]`.

### Attachments
- Keep attachment paths relative when possible.
- Update embeds and markdown links if a file is moved.

## Scripts
- `scripts/vault_registry.py`: list, add, remove, set active, set default working folder, show active, discover vaults, and full CLI passthrough via `obsidian` subcommand; writes registry to `.skills-data/obsidian-vault-manager/vaults.json` (override with `--project-root` or `--data-root`).
- `scripts/obsidian_cli.py`: machine-first wrapper used for structured command execution and CLI discovery.

## References
- `references/obsidian-vaults.md`: config locations and vault discovery details.
- `references/obsidian-markdown-skill.md`: upstream Obsidian markdown skill content (format rules, links, tasks).
- `references/obsidian-json-canvas-skill.md`: upstream JSON canvas skill content.
- `references/obsidian-bases-skill.md`: upstream Bases skill content.
