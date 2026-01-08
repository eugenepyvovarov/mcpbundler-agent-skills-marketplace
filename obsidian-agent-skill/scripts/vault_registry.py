#!/usr/bin/env python3
"""
Manage a local registry of Obsidian vault paths.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def utc_now_iso_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_workdir(raw: str) -> str:
    value = (raw or "").strip()
    if value in {"", ".", "./"}:
        return ""
    value = value.replace("\\", "/").strip("/")
    parts = [p for p in value.split("/") if p not in {"", "."}]
    if not parts:
        return ""
    if any(part == ".." for part in parts):
        raise ValueError("workdir must not contain '..'")
    return "/".join(parts)


def resolve_workdir_abs(vault_root: Path, workdir: str) -> Path:
    return vault_root if not workdir else (vault_root / workdir)


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


def registry_path(
    skill_root: Path,
    skill_name: str,
    data_root: Optional[str],
    project_root: Optional[str],
) -> Path:
    if data_root:
        data_root_path = Path(data_root).expanduser().resolve()
    else:
        project_root_path = guess_project_root(skill_root, project_root)
        data_root_path = project_root_path / ".skills-data"
    return data_root_path / skill_name / "vaults.json"


def load_registry(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {"schema_version": 1, "vaults": {}, "active": ""}
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "vaults": {}, "active": ""}
    if not isinstance(data, dict):
        return {"schema_version": 1, "vaults": {}, "active": ""}
    data.setdefault("schema_version", 1)
    data.setdefault("vaults", {})
    data.setdefault("active", "")
    if not isinstance(data["vaults"], dict):
        data["vaults"] = {}
    if not isinstance(data["active"], str):
        data["active"] = ""
    return data


def save_registry(path: Path, data: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def is_vault_root(path: Path) -> bool:
    obsidian_dir = path / ".obsidian"
    return path.exists() and path.is_dir() and obsidian_dir.exists()


def candidate_config_dirs() -> List[Path]:
    if sys.platform.startswith("darwin"):
        return [Path("~/Library/Application Support/Obsidian").expanduser()]
    if sys.platform.startswith("win"):
        dirs = []
        appdata = os.environ.get("APPDATA")
        localappdata = os.environ.get("LOCALAPPDATA")
        if appdata:
            dirs.append(Path(appdata) / "Obsidian")
        if localappdata:
            dirs.append(Path(localappdata) / "Obsidian")
        return dirs
    return [
        Path("~/.config/obsidian").expanduser(),
        Path("~/.config/Obsidian").expanduser(),
    ]


def candidate_config_files(explicit: Optional[str]) -> List[Path]:
    if explicit:
        return [Path(explicit).expanduser()]
    files: List[Path] = []
    for base in candidate_config_dirs():
        files.append(base / "vaults.json")
        files.append(base / "obsidian.json")
    return files


def extract_vault_entries(data: object) -> Iterable[Tuple[str, str]]:
    if isinstance(data, dict):
        vaults = data.get("vaults")
        if vaults is None:
            values = list(data.values())
            if values and all(isinstance(value, dict) and "path" in value for value in values):
                vaults = data
        if isinstance(vaults, dict):
            for value in vaults.values():
                if isinstance(value, dict):
                    path = value.get("path")
                    name = value.get("name") or value.get("label")
                    if path:
                        yield (name or Path(path).name, path)
        elif isinstance(vaults, list):
            for item in vaults:
                if isinstance(item, dict):
                    path = item.get("path")
                    name = item.get("name") or item.get("label")
                    if path:
                        yield (name or Path(path).name, path)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                path = item.get("path")
                name = item.get("name") or item.get("label")
                if path:
                    yield (name or Path(path).name, path)


def discover_vaults(config_path: Optional[str]) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    seen_paths = set()
    for path in candidate_config_files(config_path):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for name, vault_path in extract_vault_entries(data):
            resolved = str(Path(vault_path).expanduser())
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            results.append({
                "name": name,
                "path": resolved,
                "source": str(path),
            })
    return results


def cmd_list(args: argparse.Namespace) -> int:
    skill_root = Path(args.skill_root).expanduser().resolve()
    skill_name = resolve_skill_name(skill_root, args.skill_name or None)
    reg_path = registry_path(skill_root, skill_name, args.data_root, args.project_root)
    registry = load_registry(reg_path)
    vaults = registry.get("vaults", {})
    active = registry.get("active", "") if isinstance(registry, dict) else ""

    if args.json:
        print(json.dumps({"active": active, "vaults": vaults}, indent=2))
        return 0

    if not vaults:
        print("No vaults registered.")
        return 0

    for name in sorted(vaults.keys()):
        info = vaults[name]
        path = info.get("path", "") if isinstance(info, dict) else ""
        workdir = info.get("workdir", "") if isinstance(info, dict) else ""
        marker = "*" if name == active else " "
        rendered_workdir = workdir or "."
        print(f"{marker} {name}\t{path}\t{rendered_workdir}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    skill_root = Path(args.skill_root).expanduser().resolve()
    skill_name = resolve_skill_name(skill_root, args.skill_name or None)
    reg_path = registry_path(skill_root, skill_name, args.data_root, args.project_root)
    registry = load_registry(reg_path)
    vaults = registry.get("vaults", {})

    vault_path = Path(args.path).expanduser().resolve()
    if not args.allow_missing and not is_vault_root(vault_path):
        print(f"Not a vault root (missing .obsidian): {vault_path}", file=sys.stderr)
        return 1

    name = args.name or vault_path.name
    if name in vaults and not args.force:
        print(f"Vault name already exists: {name}", file=sys.stderr)
        return 1

    try:
        workdir = normalize_workdir(args.workdir)
    except ValueError as exc:
        print(f"Invalid --workdir: {exc}", file=sys.stderr)
        return 1

    if workdir:
        workdir_abs = resolve_workdir_abs(vault_path, workdir)
        if not workdir_abs.exists() and not args.allow_missing_workdir:
            print(f"Working dir does not exist: {workdir_abs}", file=sys.stderr)
            return 1
        if workdir_abs.exists() and not workdir_abs.is_dir():
            print(f"Working dir is not a directory: {workdir_abs}", file=sys.stderr)
            return 1

    vaults[name] = {
        "path": str(vault_path),
        "workdir": workdir,
        "source": args.source or "manual",
        "updated_at": utc_now_iso_z(),
    }
    registry["vaults"] = vaults
    if args.set_active:
        registry["active"] = name
    save_registry(reg_path, registry)
    print(f"Registered {name} -> {vault_path}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    skill_root = Path(args.skill_root).expanduser().resolve()
    skill_name = resolve_skill_name(skill_root, args.skill_name or None)
    reg_path = registry_path(skill_root, skill_name, args.data_root, args.project_root)
    registry = load_registry(reg_path)
    vaults = registry.get("vaults", {})

    if args.name not in vaults:
        print(f"Unknown vault name: {args.name}", file=sys.stderr)
        return 1

    vaults.pop(args.name)
    registry["vaults"] = vaults
    if registry.get("active") == args.name:
        registry["active"] = ""
    save_registry(reg_path, registry)
    print(f"Removed {args.name}")
    return 0


def cmd_active(args: argparse.Namespace) -> int:
    skill_root = Path(args.skill_root).expanduser().resolve()
    skill_name = resolve_skill_name(skill_root, args.skill_name or None)
    reg_path = registry_path(skill_root, skill_name, args.data_root, args.project_root)
    registry = load_registry(reg_path)
    vaults = registry.get("vaults", {})
    active = registry.get("active", "")

    payload = {}
    if isinstance(active, str) and active and isinstance(vaults, dict):
        info = vaults.get(active, {})
        path = info.get("path", "") if isinstance(info, dict) else ""
        workdir = info.get("workdir", "") if isinstance(info, dict) else ""
        workdir_path = ""
        if path:
            try:
                workdir_path = str(resolve_workdir_abs(Path(path), workdir))
            except (OSError, ValueError):
                workdir_path = ""
        payload = {
            "name": active,
            "path": path,
            "workdir": workdir,
            "workdir_path": workdir_path,
        }

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    if not payload:
        print("No active vault.")
        return 0

    print(f"{payload['name']}\t{payload['path']}")
    return 0


def cmd_set_active(args: argparse.Namespace) -> int:
    skill_root = Path(args.skill_root).expanduser().resolve()
    skill_name = resolve_skill_name(skill_root, args.skill_name or None)
    reg_path = registry_path(skill_root, skill_name, args.data_root, args.project_root)
    registry = load_registry(reg_path)
    vaults = registry.get("vaults", {})

    if args.name not in vaults:
        print(f"Unknown vault name: {args.name}", file=sys.stderr)
        return 1

    registry["active"] = args.name
    save_registry(reg_path, registry)
    print(f"Active vault set to {args.name}")
    return 0


def cmd_set_workdir(args: argparse.Namespace) -> int:
    skill_root = Path(args.skill_root).expanduser().resolve()
    skill_name = resolve_skill_name(skill_root, args.skill_name or None)
    reg_path = registry_path(skill_root, skill_name, args.data_root, args.project_root)
    registry = load_registry(reg_path)
    vaults = registry.get("vaults", {})

    name = args.name or registry.get("active", "")
    if not isinstance(name, str) or not name:
        print("No vault specified and no active vault set.", file=sys.stderr)
        return 1
    if name not in vaults:
        print(f"Unknown vault name: {name}", file=sys.stderr)
        return 1

    info = vaults.get(name, {})
    if not isinstance(info, dict):
        info = {}

    vault_path_str = info.get("path", "")
    if not isinstance(vault_path_str, str) or not vault_path_str:
        print(f"Vault path missing for {name}", file=sys.stderr)
        return 1

    try:
        workdir = normalize_workdir(args.workdir)
    except ValueError as exc:
        print(f"Invalid --workdir: {exc}", file=sys.stderr)
        return 1

    vault_path = Path(vault_path_str).expanduser().resolve()
    workdir_abs = resolve_workdir_abs(vault_path, workdir)
    if workdir and not workdir_abs.exists() and not args.allow_missing_workdir:
        print(f"Working dir does not exist: {workdir_abs}", file=sys.stderr)
        return 1
    if workdir_abs.exists() and not workdir_abs.is_dir():
        print(f"Working dir is not a directory: {workdir_abs}", file=sys.stderr)
        return 1

    info["workdir"] = workdir
    info["updated_at"] = utc_now_iso_z()
    vaults[name] = info
    registry["vaults"] = vaults
    save_registry(reg_path, registry)

    rendered = workdir or "."
    print(f"Working dir set for {name}: {rendered}")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    skill_root = Path(args.skill_root).expanduser().resolve()
    skill_name = resolve_skill_name(skill_root, args.skill_name or None)
    reg_path = registry_path(skill_root, skill_name, args.data_root, args.project_root)
    registry = load_registry(reg_path)
    vaults = registry.get("vaults", {})

    found = discover_vaults(args.config)
    if args.json and not args.merge:
        print(json.dumps(found, indent=2))
        return 0

    if args.merge:
        for entry in found:
            name = entry["name"]
            path = entry["path"]
            if name in vaults and not args.force:
                existing = vaults[name]
                existing_path = existing.get("path") if isinstance(existing, dict) else None
                if existing_path != path:
                    print(f"Skip {name}; already registered", file=sys.stderr)
                continue

            existing_workdir = ""
            if name in vaults and isinstance(vaults[name], dict):
                existing_workdir = str(vaults[name].get("workdir", "") or "")

            vaults[name] = {
                "path": path,
                "workdir": existing_workdir,
                "source": entry.get("source", "obsidian"),
                "updated_at": utc_now_iso_z(),
            }
        registry["vaults"] = vaults
        save_registry(reg_path, registry)
        print(f"Merged {len(found)} vault(s)")
        return 0

    if not found:
        print("No vaults discovered.")
        return 0

    for entry in found:
        print(f"{entry['name']}\t{entry['path']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Obsidian vault registry.")
    parser.add_argument("--skill-root", default=Path(__file__).resolve().parents[1], help="Path to the skill root")
    parser.add_argument("--skill-name", default="", help="Override skill name")
    parser.add_argument("--data-root", default="", help="Override data root")
    parser.add_argument("--project-root", default="", help="Override project root")

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List registered vaults")
    list_parser.add_argument("--json", action="store_true", help="Output JSON")
    list_parser.set_defaults(func=cmd_list)

    add_parser = subparsers.add_parser("add", help="Add a vault to the registry")
    add_parser.add_argument("--name", default="", help="Vault name")
    add_parser.add_argument("--path", required=True, help="Vault path")
    add_parser.add_argument(
        "--workdir",
        default="",
        help="Default working folder within the vault (relative path; empty for vault root)",
    )
    add_parser.add_argument(
        "--allow-missing-workdir",
        action="store_true",
        help="Allow setting workdir even if the folder does not exist",
    )
    add_parser.add_argument("--source", default="", help="Source label")
    add_parser.add_argument("--force", action="store_true", help="Overwrite existing name")
    add_parser.add_argument("--allow-missing", action="store_true", help="Skip .obsidian check")
    add_parser.add_argument("--set-active", action="store_true", help="Set this vault as active")
    add_parser.set_defaults(func=cmd_add)

    remove_parser = subparsers.add_parser("remove", help="Remove a vault from the registry")
    remove_parser.add_argument("--name", required=True, help="Vault name")
    remove_parser.set_defaults(func=cmd_remove)

    active_parser = subparsers.add_parser("active", help="Show active vault")
    active_parser.add_argument("--json", action="store_true", help="Output JSON")
    active_parser.set_defaults(func=cmd_active)

    set_active_parser = subparsers.add_parser("set-active", help="Set active vault")
    set_active_parser.add_argument("--name", required=True, help="Vault name")
    set_active_parser.set_defaults(func=cmd_set_active)

    set_workdir_parser = subparsers.add_parser(
        "set-workdir",
        help="Set default working folder for a vault (defaults to active)",
    )
    set_workdir_parser.add_argument("--name", default="", help="Vault name (defaults to active)")
    set_workdir_parser.add_argument(
        "--workdir",
        default="",
        help="Working folder within the vault (relative path; empty for vault root)",
    )
    set_workdir_parser.add_argument(
        "--allow-missing-workdir",
        action="store_true",
        help="Allow setting workdir even if the folder does not exist",
    )
    set_workdir_parser.set_defaults(func=cmd_set_workdir)

    discover_parser = subparsers.add_parser("discover", help="Discover vaults from Obsidian config")
    discover_parser.add_argument("--config", default="", help="Explicit config file path")
    discover_parser.add_argument("--merge", action="store_true", help="Merge into registry")
    discover_parser.add_argument("--force", action="store_true", help="Overwrite existing names")
    discover_parser.add_argument("--json", action="store_true", help="Output JSON when not merging")
    discover_parser.set_defaults(func=cmd_discover)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
