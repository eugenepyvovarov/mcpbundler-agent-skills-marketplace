# Obsidian vault discovery

## Vault identification
- Treat a vault as a folder that contains a `.obsidian/` directory.
- Notes are markdown files in the vault; attachments are any linked files.

## Discovery source order for this skill
- Prefer Obsidian CLI discovery via `obsidian vaults` (CLI-first).
- If CLI is unavailable, fall back to local Obsidian config files in platform-specific locations.

## Global config locations
macOS:
- `~/Library/Application Support/Obsidian`

Linux:
- `~/.config/obsidian`
- `~/.config/Obsidian`

Windows:
- `%APPDATA%\\Obsidian`
- `%LOCALAPPDATA%\\Obsidian`

Look for:
- `vaults.json` (preferred)
- `obsidian.json` (older builds)

## vaults.json structure
Most configs expose a `vaults` map. Each entry usually has a `path` and sometimes a `name`.

Example:
```
{
  "vaults": {
    "abc123": { "path": "/Users/me/Vault", "name": "Vault" }
  }
}
```

## If discovery fails
- Ask the user for a vault path.
- Validate the path contains `.obsidian/` (or allow missing in manual exceptional flows).
- Register it manually.
