#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="x-bookmarks-manager"
SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "$SKILL_ROOT/../../.." && pwd)"

SKILL_DATA_ROOT="$PROJECT_ROOT/.skills-data"
SKILL_DATA_DIR="$SKILL_DATA_ROOT/$SKILL_NAME"
NODE_PREFIX_DEFAULT="$SKILL_DATA_DIR/venv"
BIRD_BIN_DEFAULT="$NODE_PREFIX_DEFAULT/node_modules/.bin/bird"

mkdir -p "$SKILL_DATA_DIR/logs" "$SKILL_DATA_DIR/cache" "$SKILL_DATA_DIR/tmp" "$NODE_PREFIX_DEFAULT"

ENV_FILE="$SKILL_DATA_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  cat >"$ENV_FILE" <<EOF
SKILL_ROOT="$SKILL_ROOT"
SKILL_NAME="$SKILL_NAME"
SKILL_DATA_ROOT="$SKILL_DATA_ROOT"
SKILL_DATA_DIR="$SKILL_DATA_DIR"
NODE_PREFIX="$NODE_PREFIX_DEFAULT"
NODE_PATH="$NODE_PREFIX_DEFAULT/node_modules"
NPM_CONFIG_CACHE="$SKILL_DATA_DIR/cache/npm"
BIRD_BIN="$BIRD_BIN_DEFAULT"
BIRD_EXPECTED_USER=""
EOF
  echo "Wrote $ENV_FILE"
else
  echo "Exists: $ENV_FILE (leaving as-is)"
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

NODE_PREFIX="${NODE_PREFIX:-$NODE_PREFIX_DEFAULT}"
BIRD_BIN_DEFAULT="${BIRD_BIN_DEFAULT:-$NODE_PREFIX/node_modules/.bin/bird}"
BIRD_BIN="${BIRD_BIN:-$BIRD_BIN_DEFAULT}"
if [[ -x "$BIRD_BIN" ]]; then
  exit 0
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to install @steipete/bird. Install Node.js or set BIRD_BIN to an existing bird binary." >&2
  exit 1
fi

export NPM_CONFIG_CACHE="${NPM_CONFIG_CACHE:-$SKILL_DATA_DIR/cache/npm}"
mkdir -p "$NPM_CONFIG_CACHE" "$NODE_PREFIX"

echo "Installing bird via npm into $NODE_PREFIX"
npm install --prefix "$NODE_PREFIX" @steipete/bird

if [[ ! -x "$BIRD_BIN" ]]; then
  echo "bird was installed but the binary was not found at $BIRD_BIN." >&2
  echo "Check $NODE_PREFIX/node_modules/.bin or update BIRD_BIN in $ENV_FILE." >&2
  exit 1
fi

echo "Installed bird to $BIRD_BIN"
