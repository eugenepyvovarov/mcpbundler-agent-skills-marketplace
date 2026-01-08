# Obsidian vault discovery

## Vault identification
- Treat a vault as a folder that contains a `.obsidian/` directory.
- Notes are markdown files in the vault; attachments are any linked files.

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
- Validate the path contains `.obsidian/`.
- Register it manually.
