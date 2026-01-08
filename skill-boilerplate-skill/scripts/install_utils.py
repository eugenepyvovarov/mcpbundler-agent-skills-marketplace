#!/usr/bin/env python3
"""
Install common utilities with an OS-aware package manager. Dry-run by default.
"""

import argparse
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


def read_os_release() -> Dict[str, str]:
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return {}
    data: Dict[str, str] = {}
    for line in os_release.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"')
        data[key] = value
    return data


def detect_linux_manager() -> Optional[str]:
    info = read_os_release()
    distro_id = info.get("ID", "").lower()
    like = info.get("ID_LIKE", "").lower()

    def matches(token: str) -> bool:
        return token in distro_id or token in like

    if matches("arch"):
        return "pacman"
    if matches("alpine"):
        return "apk"
    if matches("suse"):
        return "zypper"
    if matches("debian") or distro_id in {"debian", "ubuntu", "linuxmint", "pop", "raspbian"}:
        return "apt"
    if matches("rhel") or matches("fedora") or distro_id in {
        "fedora",
        "rhel",
        "centos",
        "rocky",
        "almalinux",
    }:
        if shutil.which("dnf"):
            return "dnf"
        return "yum"

    for candidate in ["apt", "dnf", "yum", "pacman", "apk", "zypper"]:
        if shutil.which(candidate):
            return candidate

    return None


def build_install_commands(manager: str, packages: List[str], use_sudo: bool) -> List[List[str]]:
    prefix = ["sudo"] if use_sudo else []
    if manager == "brew":
        return [["brew", "install", *packages]]
    if manager == "apt":
        return [
            [*prefix, "apt-get", "update"],
            [*prefix, "apt-get", "install", "-y", *packages],
        ]
    if manager == "dnf":
        return [[*prefix, "dnf", "install", "-y", *packages]]
    if manager == "yum":
        return [[*prefix, "yum", "install", "-y", *packages]]
    if manager == "pacman":
        return [[*prefix, "pacman", "-S", "--noconfirm", *packages]]
    if manager == "apk":
        return [[*prefix, "apk", "add", *packages]]
    if manager == "zypper":
        return [[*prefix, "zypper", "install", "-y", *packages]]
    raise ValueError(f"Unsupported manager: {manager}")


def normalize_utils(raw: List[str]) -> List[str]:
    utils: List[str] = []
    for entry in raw:
        for token in entry.split(","):
            token = token.strip()
            if token:
                utils.append(token)
    return utils


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install utilities with an OS-aware package manager (dry-run by default).",
    )
    parser.add_argument("--utils", nargs="+", required=True, help="Utilities to install")
    parser.add_argument("--apply", action="store_true", help="Run install commands")
    parser.add_argument("--no-sudo", action="store_true", help="Do not prefix with sudo")
    parser.add_argument(
        "--include-installed",
        action="store_true",
        help="Include utilities even if already on PATH",
    )
    args = parser.parse_args()

    utils = normalize_utils(args.utils)
    if not utils:
        print("No utilities requested.")
        return 0

    missing = utils
    if not args.include-installed:
        missing = [util for util in utils if shutil.which(util) is None]

    if not missing:
        print("All utilities already available.")
        return 0

    system = platform.system().lower()
    manager: Optional[str] = None
    if system == "darwin":
        manager = "brew"
    elif system == "linux":
        manager = detect_linux_manager()

    if not manager:
        print("Unable to detect a supported package manager.")
        return 1

    commands = build_install_commands(manager, missing, use_sudo=not args.no_sudo)

    print(f"Manager: {manager}")
    print(f"Utilities: {', '.join(missing)}")
    for cmd in commands:
        print("$ " + " ".join(cmd))

    if not args.apply:
        print("Dry-run only. Re-run with --apply to install.")
        return 0

    for cmd in commands:
        subprocess.run(cmd, check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
