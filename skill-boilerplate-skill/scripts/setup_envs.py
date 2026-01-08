#!/usr/bin/env python3
"""
Bootstrap isolated language environments under .skills-data/<skill-name>/venv.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


def parse_skill_name_from_skill_md(skill_root: Path) -> Optional[str]:
    skill_md = skill_root / "SKILL.md"
    if not skill_md.exists():
        return None
    try:
        lines = skill_md.read_text().splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


def resolve_skill_name(skill_root: Path, override: Optional[str]) -> str:
    if override:
        return override.strip()
    from_md = parse_skill_name_from_skill_md(skill_root)
    if from_md:
        return from_md
    return skill_root.name


def guess_project_root(skill_root: Path, override: Optional[str]) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    resolved = skill_root.resolve()
    if resolved.parent.name == "skills" and len(resolved.parents) >= 3:
        return resolved.parents[2]
    return resolved.parent


def ensure_dir(path: Path, dry_run: bool) -> None:
    if path.exists():
        return
    if dry_run:
        print(f"[DRY] mkdir -p {path}")
        return
    path.mkdir(parents=True, exist_ok=True)


def upsert_env(env_path: Path, updates: Dict[str, str], dry_run: bool) -> None:
    lines: List[str] = []
    index: Dict[str, int] = {}

    if env_path.exists():
        try:
            lines = env_path.read_text().splitlines()
        except OSError:
            lines = []
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

    if dry_run:
        print(f"[DRY] write {env_path}")
        return

    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(lines) + "\n")


def create_python_venv(venv_dir: Path, dry_run: bool) -> None:
    if (venv_dir / "bin").exists() or (venv_dir / "Scripts").exists():
        return
    if dry_run:
        print(f"[DRY] {sys.executable} -m venv {venv_dir}")
        return
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)


def ensure_node_layout(venv_root: Path, skill_name: str, dry_run: bool) -> None:
    ensure_dir(venv_root / "node_modules", dry_run)
    package_json = venv_root / "package.json"
    if package_json.exists():
        return
    payload = {
        "name": f"{skill_name}-venv",
        "private": True,
    }
    if dry_run:
        print(f"[DRY] write {package_json}")
        return
    package_json.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap isolated language environments under .skills-data/<skill-name>/venv.",
    )
    parser.add_argument("--skill-root", default=".", help="Path to the skill root")
    parser.add_argument("--skill-name", default="", help="Override skill name")
    parser.add_argument(
        "--project-root",
        "--repo-root",
        dest="project_root",
        default="",
        help="Override project root",
    )
    parser.add_argument("--data-root", default="", help="Override data root")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument("--no-env", action="store_true", help="Skip updating .env")
    parser.add_argument("--all", action="store_true", help="Enable all language setups")
    parser.add_argument("--python", action="store_true", help="Set up Python venv")
    parser.add_argument("--node", action="store_true", help="Set up Node layout")
    parser.add_argument("--go", action="store_true", help="Set up Go caches")
    parser.add_argument("--php", action="store_true", help="Set up PHP composer dirs")
    args = parser.parse_args()

    if not any([args.all, args.python, args.node, args.go, args.php]):
        args.all = True

    skill_root = Path(args.skill_root).expanduser().resolve()
    skill_name = resolve_skill_name(skill_root, args.skill_name or None)
    project_root = guess_project_root(skill_root, args.project_root or None)
    data_root = Path(args.data_root).expanduser().resolve() if args.data_root else project_root / ".skills-data"
    data_dir = data_root / skill_name
    venv_root = data_dir / "venv"

    print(f"Skill root: {skill_root}")
    print(f"Skill name: {skill_name}")
    print(f"Project root: {project_root}")
    print(f"Data dir:     {data_dir}")

    ensure_dir(data_dir, args.dry_run)
    ensure_dir(venv_root, args.dry_run)

    env_updates: Dict[str, str] = {}

    if args.all or args.python:
        python_venv = venv_root / "python"
        ensure_dir(python_venv, args.dry_run)
        create_python_venv(python_venv, args.dry_run)
        env_updates["PYTHON_VENV"] = str(python_venv)

    if args.all or args.node:
        ensure_node_layout(venv_root, skill_name, args.dry_run)
        npm_cache = data_dir / "cache" / "npm"
        ensure_dir(npm_cache, args.dry_run)
        env_updates["NODE_PATH"] = str(venv_root / "node_modules")
        env_updates["NPM_CONFIG_CACHE"] = str(npm_cache)

    if args.all or args.go:
        go_root = venv_root / "go"
        go_modcache = go_root / "modcache"
        go_cache = go_root / "gocache"
        ensure_dir(go_modcache, args.dry_run)
        ensure_dir(go_cache, args.dry_run)
        env_updates["GOMODCACHE"] = str(go_modcache)
        env_updates["GOCACHE"] = str(go_cache)

    if args.all or args.php:
        php_root = venv_root / "php"
        composer_cache = php_root / "cache"
        composer_vendor = php_root / "vendor"
        ensure_dir(composer_cache, args.dry_run)
        ensure_dir(composer_vendor, args.dry_run)
        env_updates["COMPOSER_CACHE_DIR"] = str(composer_cache)
        env_updates["COMPOSER_VENDOR_DIR"] = str(composer_vendor)
        env_updates["COMPOSER_HOME"] = str(php_root)

    if not args.no_env and env_updates:
        env_path = data_dir / ".env"
        upsert_env(env_path, env_updates, args.dry_run)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
