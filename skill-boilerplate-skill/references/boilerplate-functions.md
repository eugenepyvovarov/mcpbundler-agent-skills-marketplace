# Boilerplate helper functions

Copy these into a skill's scripts/ directory when setup automation is needed. Keep them opt-in and document usage in that skill's SKILL.md. Adjust paths to match the skill name.

## Resolve project_root and data dir (Python)

```
from pathlib import Path
from typing import Optional


def guess_project_root(skill_root: Path, override: Optional[str] = None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    resolved = skill_root.resolve()
    # If skills live under <container>/skills/<skill-name>, hop two levels above skills.
    if resolved.parent.name == "skills" and len(resolved.parents) >= 3:
        return resolved.parents[2]
    return resolved.parent


def resolve_data_dir(skill_root: Path, skill_name: str, project_root: Optional[str] = None) -> Path:
    root = guess_project_root(skill_root, project_root)
    return root / ".skills-data" / skill_name
```

## Write .env keys (Python)

```
from pathlib import Path
from typing import Dict, List


def upsert_env(env_path: Path, updates: Dict[str, str]) -> None:
    lines: List[str] = []
    index: Dict[str, int] = {}
    if env_path.exists():
        lines = env_path.read_text().splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key = line.split("=", 1)[0].strip()
            if key:
                index[key] = i
    for key, value in updates.items():
        rendered = f"{key}={value}"
        if key in index:
            lines[index[key]] = rendered
        else:
            index[key] = len(lines)
            lines.append(rendered)
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(lines) + "\n")
```

## Create language env folders (shell)

```
DATA_DIR="${SKILL_DATA_DIR:-$PROJECT_ROOT/.skills-data/$SKILL_NAME}"
mkdir -p "$DATA_DIR" \
  "$DATA_DIR/bin" \
  "$DATA_DIR/cache" \
  "$DATA_DIR/logs" \
  "$DATA_DIR/tmp" \
  "$DATA_DIR/venv/python" \
  "$DATA_DIR/venv/node_modules" \
  "$DATA_DIR/venv/go/modcache" \
  "$DATA_DIR/venv/go/gocache" \
  "$DATA_DIR/venv/php/cache" \
  "$DATA_DIR/venv/php/vendor"
```

## Python venv setup (shell)

```
python3 -m venv "$DATA_DIR/venv/python"
"$DATA_DIR/venv/python/bin/pip" install -r requirements.txt
```

## Node setup (shell)

```
cd "$DATA_DIR/venv"
npm init -y
npm install <pkg>
```

## Go cache env (shell)

```
export GOMODCACHE="$DATA_DIR/venv/go/modcache"
export GOCACHE="$DATA_DIR/venv/go/gocache"
```

## PHP composer env (shell)

```
export COMPOSER_CACHE_DIR="$DATA_DIR/venv/php/cache"
export COMPOSER_VENDOR_DIR="$DATA_DIR/venv/php/vendor"
export COMPOSER_HOME="$DATA_DIR/venv/php"
```
