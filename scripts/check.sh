#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[1/3] Python syntax checks"
python3 -m py_compile \
  "$REPO_ROOT/bin/axiom-send-markdown-mail" \
  "$REPO_ROOT/bin/axiom-teamcity-watch" \
  "$REPO_ROOT/bin/axiom-todo"

echo "[2/3] Installer shell syntax"
bash -n "$REPO_ROOT/scripts/install-local.sh"

echo "[3/3] Throwaway install smoke test"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

HOME="$tmpdir/home" mkdir -p "$tmpdir/home"
CODEX_HOME="$tmpdir/codex" HOME="$tmpdir/home" \
  "$REPO_ROOT/scripts/install-local.sh" >/dev/null

for helper in axiom-send-markdown-mail axiom-teamcity-watch axiom-todo; do
  target="$tmpdir/home/.local/bin/$helper"
  if [[ ! -e "$target" ]]; then
    echo "missing installed helper: $target" >&2
    exit 1
  fi
done

if [[ ! -e "$tmpdir/codex/skills/markdown-email/SKILL.md" ]]; then
  echo "missing installed skill: $tmpdir/codex/skills/markdown-email/SKILL.md" >&2
  exit 1
fi

echo "bot-tools checks passed"
