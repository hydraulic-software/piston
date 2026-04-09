#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

BIN_TARGET="${HOME}/.local/bin"
SKILLS_ROOT="${CODEX_HOME:-${HOME}/.codex}/skills"
SKILL_TARGET="${SKILLS_ROOT}/markdown-email"
MODE="symlink"

usage() {
  cat <<'EOF'
Usage: scripts/install-local.sh [--copy]

Install the staged bot-tools helpers into the current account.

Defaults:
- symlink bin/* into ~/.local/bin
- symlink skills/markdown-email into ${CODEX_HOME:-~/.codex}/skills/markdown-email

Options:
- --copy     copy files/directories instead of symlinking them
EOF
}

copy_file() {
  local src="$1"
  local dest="$2"
  install -m 0755 "$src" "$dest"
}

copy_dir() {
  local src="$1"
  local dest="$2"
  rm -rf "$dest"
  mkdir -p "$(dirname "$dest")"
  cp -R "$src" "$dest"
}

link_path() {
  local src="$1"
  local dest="$2"
  ln -sfn "$src" "$dest"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy)
      MODE="copy"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

mkdir -p "$BIN_TARGET" "$SKILLS_ROOT"

for helper in "$REPO_ROOT"/bin/*; do
  name="$(basename "$helper")"
  target="${BIN_TARGET}/${name}"
  if [[ "$MODE" == "copy" ]]; then
    copy_file "$helper" "$target"
  else
    link_path "$helper" "$target"
  fi
  echo "Installed helper: ${target}"
done

if [[ "$MODE" == "copy" ]]; then
  copy_dir "$REPO_ROOT/skills/markdown-email" "$SKILL_TARGET"
else
  rm -rf "$SKILL_TARGET"
  link_path "$REPO_ROOT/skills/markdown-email" "$SKILL_TARGET"
fi

echo "Installed skill: ${SKILL_TARGET}"
