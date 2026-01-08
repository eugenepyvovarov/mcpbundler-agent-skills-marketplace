# Obsidian Vault Manager (Codex skill)

Manage local Obsidian vaults and markdown notes. Use this skill when Codex needs to connect to local Obsidian vaults, register vault paths, or create/edit/refactor/search notes, frontmatter, links, tags, and attachments within a vault.

## What it does
- Registers one or more Obsidian vaults 
- Tracks an **active vault** and an optional **working folder** inside that vault.
- Supports note operations via normal file edits plus fast search with `rg`.

## Where config/state is stored

Skill uses ideas from https://github.com/eugenepyvovarov/skill-boilerplate-skill to store config/data in common location for skills in current project folder.

This skill keeps all **mutable** state in a deterministic, git-ignorable location under your project root.

- **`project_root`**: the root of your project/repository (the place you’d typically put your `.gitignore`).
- **Skill data dir**: `<project_root>/.skills-data/obsidian-vault-manager/`
  - Vault registry: `.skills-data/obsidian-vault-manager/vaults.json`
  - Env file: `.skills-data/obsidian-vault-manager/.env`
  - Local tools: `.skills-data/obsidian-vault-manager/bin/` (prepend to `PATH` when needed)
  - Dependencies: `.skills-data/obsidian-vault-manager/venv/`
  - Logs/cache/tmp: `.skills-data/obsidian-vault-manager/logs/`, `cache/`, `tmp/`

## Safety (isolation)
By default, automation lives in `scripts/` and should only write to:
- this repo folder (the skill root), and
- `<project_root>/.skills-data/obsidian-vault-manager/`

Anything outside those locations should be an explicit user request.

## References
See `references/` for content rules (markdown, canvas, Bases) and vault details.
