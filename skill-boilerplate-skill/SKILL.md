---
name: skill-boilerplate
description: Define a standard per-skill local data layout at <project_root>/.skills-data/<skill-name> and required SKILL.md guidance for env/config/deps/tools. Use when starting a new skill and you must specify where to store data, env files, local binaries, and dependencies.
---

# Skill Boilerplate

## Purpose

Document the mandatory local data layout and instructions to embed in new skills. This skill does not create any folders or files.

## Determine project_root and data dir

- Let <skill-root> be the folder containing SKILL.md.
- If <skill-root>/.. is `skills`, guess project_root as two levels above the `skills` folder (i.e. <skill-root>/../../..).
- This works when skills are stored as <project_root>/<container>/skills/<skill-name>, where <container> can be .codex, .claude, .github, or any other parent.
- Ask the user to confirm the guess; if it is wrong, request project_root.
- If the skill is not under a `skills` directory, do not guess; ask the user for project_root.
- Data dir: <project_root>/.skills-data/<skill-name>/.

## Mandatory SKILL.md section (copy into every new skill)

```markdown
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
```

## Environment variables

Write these keys into .skills-data/<skill-name>/.env:

- SKILL_ROOT: absolute path to the skill directory
- SKILL_NAME: skill name
- SKILL_DATA_ROOT: absolute path to <project_root>/.skills-data
- SKILL_DATA_DIR: absolute path to <project_root>/.skills-data/<skill-name>

Optional language-specific keys (use only if the skill needs that runtime):

- PYTHON_VENV
- NODE_PATH
- NPM_CONFIG_CACHE
- GOMODCACHE
- GOCACHE
- COMPOSER_CACHE_DIR
- COMPOSER_VENDOR_DIR
- COMPOSER_HOME

## Boilerplate helper functions

If a skill needs setup automation, add helper scripts under that skill's `scripts/` directory. Keep them opt-in and document them in that skill's SKILL.md. Use `references/boilerplate-functions.md` for copy-ready snippets.

## OS utilities (optional)

If a skill needs system utilities (rg, jq, git), document manual install commands and reference `references/os-install.md`.
