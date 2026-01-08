# OS Utilities Install Notes

Use this reference only when you need extra detail on how install_utils.py chooses a package manager
or when you must run install commands manually.

## How manager detection works

- macOS: uses Homebrew (`brew`).
- Linux: reads `/etc/os-release` and maps to:
  - Debian/Ubuntu/Mint/Pop: `apt-get`
  - Fedora/RHEL/CentOS/Rocky/Alma: `dnf` (falls back to `yum`)
  - Arch/Manjaro: `pacman`
  - Alpine: `apk`
  - openSUSE/SLES: `zypper`

If the distro is unknown, it picks the first available manager from: apt, dnf, yum, pacman, apk, zypper.

## Manual install examples

macOS:

```
brew install rg jq git
```

Debian/Ubuntu:

```
sudo apt-get update
sudo apt-get install -y rg jq git
```

Fedora:

```
sudo dnf install -y rg jq git
```

Arch:

```
sudo pacman -S --noconfirm rg jq git
```

Alpine:

```
sudo apk add rg jq git
```

openSUSE:

```
sudo zypper install -y rg jq git
```
