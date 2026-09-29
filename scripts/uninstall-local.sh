#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

BIN_TARGET="${HOME}/.local/bin"
SKILLS_ROOT="${CODEX_HOME:-${HOME}/.codex}/skills"
SKILL_TARGET="${SKILLS_ROOT}/markdown-email"
SYSTEMD_TARGET="${HOME}/.config/systemd/user"

usage() {
  cat <<'EOF'
Usage: scripts/uninstall-local.sh

Remove the staged piston helpers and skill from the current account.

This removes:
- ~/.local/bin/piston-send-markdown-mail
- ~/.local/bin/piston-teamcity-watch
- ~/.local/bin/piston-todo
- ${CODEX_HOME:-~/.codex}/skills/markdown-email
- matching example user units from ~/.config/systemd/user

It only removes the exact installed entry names from this staged slice.
EOF
}

remove_if_present() {
  local path="$1"
  if [[ -e "$path" || -L "$path" ]]; then
    rm -rf "$path"
    echo "Removed: $path"
  else
    echo "Already absent: $path"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
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

for helper in "$REPO_ROOT"/bin/*; do
  [[ -f "$helper" ]] || continue
  name="$(basename "$helper")"
  remove_if_present "${BIN_TARGET}/${name}"
  remove_if_present "${BIN_TARGET}/axiom-${name#piston-}"
done

remove_if_present "$SKILL_TARGET"
remove_if_present "${HOME}/.local/share/piston/codex-version"

for unit in "$REPO_ROOT"/systemd/user/*; do
  [[ -f "$unit" ]] || continue
  name="$(basename "$unit")"
  remove_if_present "${SYSTEMD_TARGET}/${name}"
  remove_if_present "${SYSTEMD_TARGET}/axiom-${name#piston-}"
done
