#!/usr/bin/env python3
"""
Create the standard skill data layout under <project_root>/.skills-data/<skill-name>.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional


SUBDIRS = [
    "cache",
    "logs",
    "data",
    "tmp",
    "bin",
    "venv",
    "venv/python",
    "venv/node_modules",
    "venv/go",
    "venv/go/modcache",
    "venv/go/gocache",
    "venv/php",
    "venv/php/cache",
    "venv/php/vendor",
]


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


def ensure_dir(path: Path, dry_run: bool) -> None:
    if path.exists():
        return
    if dry_run:
        print(f"[DRY] mkdir -p {path}")
        return
    path.mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create standard skill data layout under <project_root>/.skills-data/<skill-name>.",
    )
    parser.add_argument("--skill-root", default=".", help="Path to the skill root")
    parser.add_argument("--skill-name", default="", help="Override skill name")
    parser.add_argument("--project-root", default="", help="Override project root")
    parser.add_argument("--data-root", default="", help="Override data directory")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument(
        "--skip-env",
        action="store_true",
        help="Skip writing .env in the data directory",
    )
    parser.add_argument(
        "--link-env",
        action="store_true",
        help="Create a .env symlink in the skill root pointing to data .env",
    )
    args = parser.parse_args()

    skill_root = Path(args.skill_root).expanduser().resolve()
    skill_name = resolve_skill_name(skill_root, args.skill_name or None)
    project_root = guess_project_root(skill_root, args.project_root or None)
    data_root = Path(args.data_root).expanduser().resolve() if args.data_root else project_root / ".skills-data"
    data_dir = data_root / skill_name

    print(f"Skill root: {skill_root}")
    print(f"Skill name: {skill_name}")
    print(f"Project root: {project_root}")
    print(f"Data dir:     {data_dir}")

    ensure_dir(data_root, args.dry_run)
    ensure_dir(data_dir, args.dry_run)
    for subdir in SUBDIRS:
        ensure_dir(data_dir / subdir, args.dry_run)

    config_path = data_dir / "config.json"
    if not config_path.exists():
        config_payload = {
            "schema_version": 1,
            "skill_name": skill_name,
            "skill_root": str(skill_root),
            "data_dir": str(data_dir),
        }
        if args.dry_run:
            print(f"[DRY] write {config_path}")
        else:
            config_path.write_text(json.dumps(config_payload, indent=2) + "\n")

    env_path = data_dir / ".env"
    if not args.skip_env:
        env_updates = {
            "SKILL_ROOT": str(skill_root),
            "SKILL_NAME": skill_name,
            "SKILL_DATA_ROOT": str(data_root),
            "SKILL_DATA_DIR": str(data_dir),
        }
        upsert_env(env_path, env_updates, args.dry_run)

    if args.link_env:
        target = env_path
        link_path = skill_root / ".env"
        if link_path.exists():
            print(f"[WARN] {link_path} already exists; skipping link")
        elif args.dry_run:
            print(f"[DRY] ln -s {target} {link_path}")
        else:
            link_path.symlink_to(target)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
