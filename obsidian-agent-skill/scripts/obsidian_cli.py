#!/usr/bin/env python3
"""
Machine-friendly wrapper around the Obsidian CLI.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence


def utc_now_iso_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _default_cli_binary() -> str:
    return "obsidian"


def _load_binary(override: str) -> str:
    candidate = (override or "").strip() or os.environ.get("OBSIDIAN_CLI_BIN", "")
    if candidate:
        return candidate
    return _default_cli_binary()


def _to_iso_jsonable(obj: object) -> object:
    if isinstance(obj, dict):
        return {k: _to_iso_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_iso_jsonable(v) for v in obj]
    return obj


def _is_destructive(command: List[str], force_delete: bool) -> Optional[str]:
    if not command:
        return None
    primary = command[0]
    flags = set(command[1:])

    if primary == "delete" and "permanent" in flags and not force_delete:
        return "delete-permanent"
    if primary == "delete" and not force_delete:
        return "delete"
    if primary == "plugin:uninstall" and not force_delete:
        return "plugin-uninstall"
    if primary == "publish:remove" and not force_delete:
        return "publish-remove"
    if primary == "workspace:delete" and not force_delete:
        return "workspace-delete"
    if primary.endswith(":delete") and primary != "task:delete" and not force_delete:
        return f"command-{primary}"
    return None


def _is_json_text(text: str) -> bool:
    return bool(text) and text[0] in ("{", "[")


def _safe_parse_json(text: str) -> Optional[object]:
    if not _is_json_text(text):
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _parse_vaults_text(text: str) -> List[Dict[str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    entries: List[Dict[str, str]] = []
    seen = set()
    for line in lines:
        if line.lower().startswith("name") and "path" in line.lower():
            continue
        if "\t" in line:
            left, right = line.split("\t", 1)
            name = left.strip()
            path = right.strip()
        else:
            pieces = [p.strip() for p in line.split(" ") if p.strip()]
            if len(pieces) < 2:
                continue
            name = pieces[0]
            path = pieces[-1]

        if not name or not path:
            continue
        if "/" not in path and not path.startswith(".") and not path.startswith("~"):
            continue
        key = (name, path)
        if key in seen:
            continue
        seen.add(key)
        entries.append({"name": name, "path": path})
    return entries


def _extract_vaults_from_payload(payload: object) -> List[Dict[str, str]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        extracted: List[Dict[str, str]] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            path = item.get("path")
            if isinstance(name, str) and isinstance(path, str):
                extracted.append({"name": name, "path": path})
        return extracted

    if isinstance(payload, dict):
        extracted: List[Dict[str, str]] = []
        candidates = [payload]
        nested = payload.get("vaults")
        if isinstance(nested, list):
            candidates = nested
        elif isinstance(nested, dict):
            candidates = list(nested.values())
        if not isinstance(nested, (list, dict)) and "name" in payload and "path" in payload:
            # direct object with top-level name/path
            candidates = [payload]
        for item in candidates:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("label")
            path = item.get("path")
            if isinstance(name, str) and isinstance(path, str):
                extracted.append({"name": name, "path": path})
        return extracted
    return []


def discover_vaults(binary: str) -> List[Dict[str, str]]:
    result = run_obsidian(
        command=("vaults", "verbose"),
        binary=binary,
        parse_output=True,
        force_delete=True,
    )
    if not result.get("ok"):
        return []

    payload = result.get("parsed")
    if payload is not None:
        entries = _extract_vaults_from_payload(payload)
        if entries:
            return entries

    return _parse_vaults_text(result.get("stdout", ""))


def _command_needs_vault(command: Sequence[str]) -> bool:
    return bool(command) and command[0] not in {
        "help",
        "version",
        "reload",
        "restart",
        "vault",
        "vaults",
        "vault:open",
    }


def run_obsidian(
    command: Sequence[str],
    *,
    vault: str = "",
    binary: str = "",
    force_delete: bool = False,
    parse_output: bool = True,
) -> Dict[str, object]:
    command_list = list(command)
    if not command_list:
        return {
            "ok": False,
            "command": [],
            "exit_code": 1,
            "stdout": "",
            "stderr": "No command provided.",
            "parsed": None,
            "raw": "",
            "binary": binary,
            "vault": vault,
            "ts": utc_now_iso_z(),
        }

    binary_path = _load_binary(binary)
    resolved_binary = shutil.which(binary_path) or (binary_path if Path(binary_path).exists() else None)
    if not resolved_binary:
        return {
            "ok": False,
            "command": command_list,
            "exit_code": 1,
            "stdout": "",
            "stderr": f"Obsidian CLI not found: {binary_path}",
            "parsed": None,
            "raw": "",
            "binary": binary_path,
            "vault": vault,
            "ts": utc_now_iso_z(),
        }

    if _command_needs_vault(command_list):
        if vault:
            if not any(part.startswith("vault=") for part in command_list):
                command_list = [f"vault={vault}"] + command_list
        elif any(part.startswith("vault=") for part in command_list):
            vault = ""

    blocked_reason = _is_destructive(command_list, force_delete=force_delete)
    if blocked_reason:
        return {
            "ok": False,
            "command": command_list,
            "exit_code": 1,
            "stdout": "",
            "stderr": f"Refusing destructive operation ({blocked_reason}) without --force-delete.",
            "parsed": None,
            "raw": "",
            "binary": resolved_binary,
            "vault": vault,
            "ts": utc_now_iso_z(),
        }

    completed = subprocess.run(
        [resolved_binary, *command_list],
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    parsed = _safe_parse_json(stdout) if parse_output else None

    payload = {
        "ok": completed.returncode == 0,
        "command": command_list,
        "exit_code": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "parsed": parsed,
        "raw": stdout.strip(),
        "binary": resolved_binary,
        "vault": vault,
        "ts": utc_now_iso_z(),
    }
    if parse_output and parsed is None and not stdout.strip():
        payload["output_stderr_only"] = bool(stderr.strip())
    return _to_iso_jsonable(payload)


def cmd_exec(args: argparse.Namespace) -> int:
    command = list(args.command) if isinstance(args.command, list) else []
    if not command:
        print(json.dumps({"ok": False, "stderr": "No command provided."}, indent=2))
        return 1

    result = run_obsidian(
        command=command,
        vault=args.vault,
        binary=args.binary,
        force_delete=args.force_delete,
        parse_output=not args.raw,
    )

    if args.raw:
        if result.get("stdout"):
            print(result["stdout"], end="")
        if result.get("stderr"):
            print(result["stderr"], file=sys.stderr)
        return int(0 if result.get("ok") else 1)

    print(json.dumps(result, indent=2, default=str))
    return int(0 if result.get("ok") else 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Obsidian CLI command through a machine-first adapter.")
    parser.add_argument("--binary", default="", help="Override Obsidian CLI binary/path")
    parser.add_argument("--vault", default="", help="Target vault name")
    parser.add_argument("--raw", action="store_true", help="Passthrough raw stdout/stderr instead of JSON envelope")
    parser.add_argument("--force-delete", action="store_true", help="Allow destructive commands")

    parser.add_argument("command", nargs=argparse.REMAINDER, help="Obsidian CLI command and args")
    parser.set_defaults(func=cmd_exec)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.print_usage()
        return 1
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
