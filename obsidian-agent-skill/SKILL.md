---
name: obsidian-vault-manager
description: Manage local Obsidian vaults and markdown notes. Use when Codex needs to connect to local Obsidian vaults, register vault paths, or create/edit/refactor/search notes, frontmatter, links, tags, and attachments within a vault.
---

# Obsidian Vault Manager

## Quick start
- Register or discover vaults:
  - `python3 scripts/vault_registry.py discover --merge`
  - `python3 scripts/vault_registry.py add --path "/path/to/Vault" --name "Vault"`
- List vaults: `python3 scripts/vault_registry.py list`
- Set active vault: `python3 scripts/vault_registry.py set-active --name "Vault"`
- Set default working folder (within the vault): `python3 scripts/vault_registry.py set-workdir --name "Vault" --workdir "path/inside/vault"`
- Show active vault: `python3 scripts/vault_registry.py active`
- Pick a vault and confirm its path contains `.obsidian/`.
- Perform note operations with file edits and `rg`.

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
1. Prefer explicit vault path from the user.
2. If missing, attempt discovery with `scripts/vault_registry.py discover`.
3. Validate the vault root by checking for `.obsidian/`.
4. Register the vault in `.skills-data/obsidian-vault-manager/vaults.json`.
5. Set the active vault with `scripts/vault_registry.py set-active --name <name>`.
6. Ask the user for the default working folder inside the vault (relative path), defaulting to the vault root (`.`).
7. Save it with `scripts/vault_registry.py set-workdir --name <name> --workdir <relative/path>`.
8. Confirm the chosen vault name, vault path, and working folder before edits.

## Working rules
- Use the configured working folder as the default root for searches and edits (do not roam the entire vault unless requested).
- Edit only note content and attachments unless the user asks to change `.obsidian` settings.
- Preserve existing frontmatter keys; add new keys without reordering unless requested.
- Keep internal links valid after rename/move; update `[[Wiki Links]]` and markdown links.
- Confirm before delete, rename, or bulk changes.

## Common tasks
### Search and review
- Use `rg --glob '*.md' <pattern> <vault_path>` to find notes and references.
- Summarize matching files before edits.

### Create a note
- Choose a filename that matches the main title.
- Add YAML frontmatter when needed (tags, aliases, status).
- Save as UTF-8 with a trailing newline.
- depending on the note type use next documentation to properly edit:
  - `references/obsidian-markdown-skill.md`: markdown content (format rules, links, tasks).
  - `references/obsidian-json-canvas-skill.md`: canvas content.
  - `references/obsidian-bases-skill.md`: Bases content.

### Edit or refactor
- Keep headings and block IDs stable unless requested.
- When moving sections across notes, update inbound links and mentions.
- depending on the note type use next documentation to properly edit:
  - `references/obsidian-markdown-skill.md`: markdown content (format rules, links, tasks).
  - `references/obsidian-json-canvas-skill.md`: canvas content.
  - `references/obsidian-bases-skill.md`: Bases content.

### Rename or move
- Rename the file and update links across the vault.
- For wiki links, update `[[Old Name]]` and `[[path/Old Name|alias]]`.

### Attachments
- Keep attachment paths relative when possible.
- Update embeds and markdown links if a file is moved.

## Scripts
- `scripts/vault_registry.py`: list, add, remove, set active, set default working folder, show active, and discover vaults; writes registry to `.skills-data/obsidian-vault-manager/vaults.json` (override with `--project-root` or `--data-root`).

## References
- `references/obsidian-vaults.md`: config locations and vault discovery details.
- `references/obsidian-markdown-skill.md`: rules of editing Obsidian markdown content (format rules, links, tasks).
- `references/obsidian-json-canvas-skill.md`: rules of editing JSON canvas content.
- `references/obsidian-bases-skill.md`: rules of editing Bases content.
