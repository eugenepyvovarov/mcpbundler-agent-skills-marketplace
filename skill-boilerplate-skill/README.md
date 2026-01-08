# Skill Boilerplate

This skill documents the standard local data layout and required guidance to embed in new skills.
Its purpose is to standardize how skills set themselves up and operate by storing data and configs in
defined folders and by installing dependencies locally (not globally) under the project root.
Use it when starting a new skill and you need to define where to store data, env files, local binaries,
and dependencies under the project root.

## What it does

- Defines how to determine `project_root` and the per-skill data directory.
- Provides a mandatory `SKILL.md` section to copy into new skills.
- Lists required environment variables and optional language-specific keys.
- Points to helper script snippets and optional OS utilities guidance.

## What it does not do

- It does not create or modify any folders or files on disk.
- It does not install dependencies or tools.

## Key paths

- Skill root: the folder containing `SKILL.md`.
- Data dir: `<project_root>/.skills-data/<skill-name>/`.

## Example data layout

```text
<project_root>/
  .skills-data/
    <skill-name>/
      .env
      bin/
      cache/
      logs/
      tmp/
      venv/
        python/
        node_modules/
        go/
        php/
```

## Mandatory SKILL.md note

This skill provides this section to put in every new skill to keep data, env, and dependencies localized:

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

## Related files

- `SKILL.md` contains the full instructions to follow.
- `references/boilerplate-functions.md` includes script snippets.
- `references/os-install.md` lists optional OS utilities installation guidance.

## Example helper functions

These are shown in `references/boilerplate-functions.md` as copy-ready snippets:

- `guess_project_root`: resolve the project root from a skill path or override.
- `resolve_data_dir`: compute `.skills-data/<skill-name>/` based on the project root.
- `upsert_env`: write or update required keys in the per-skill `.env` file.
- `create language env folders` (shell): create standard bin/cache/logs/tmp/venv directories.
- `python venv setup` (shell): create a venv under the skill data folder and install requirements.
- `node setup` (shell): install Node dependencies under the skill data folder.
- `go cache env` (shell): point Go caches at the skill data folder.
- `php composer env` (shell): point Composer caches and vendor dir at the skill data folder.
