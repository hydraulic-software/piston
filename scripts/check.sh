#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[1/3] Python syntax checks"
python3 -m py_compile \
  "$REPO_ROOT/bin/axiom-autonomy-scheduler" \
  "$REPO_ROOT/bin/axiom-mail-filter" \
  "$REPO_ROOT/bin/axiom-render-codex-monitor" \
  "$REPO_ROOT/bin/axiom-send-markdown-mail" \
  "$REPO_ROOT/bin/axiom-teamcity-watch" \
  "$REPO_ROOT/bin/axiom-todo"

echo "[2/3] Installer shell syntax"
bash -n "$REPO_ROOT/bin/axiom-codex-runner"
bash -n "$REPO_ROOT/bin/axiom-watch-codex-monitor"
bash -n "$REPO_ROOT/scripts/install-local.sh"
bash -n "$REPO_ROOT/scripts/uninstall-local.sh"

echo "[3/3] Throwaway install smoke test"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

mkdir -p "$tmpdir/home" "$tmpdir/home/.config/systemd/user"
CODEX_HOME="$tmpdir/codex" HOME="$tmpdir/home" \
  "$REPO_ROOT/scripts/install-local.sh" --systemd >/dev/null

for helper in axiom-autonomy-scheduler axiom-codex-runner axiom-mail-filter axiom-render-codex-monitor axiom-send-markdown-mail axiom-teamcity-watch axiom-todo axiom-watch-codex-monitor; do
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

for unit in axiom-autonomy.service axiom-autonomy.timer axiom-codex-monitor.service axiom-mail.path axiom-mail.service axiom-nightly.service axiom-nightly.timer; do
  target="$tmpdir/home/.config/systemd/user/$unit"
  if [[ ! -e "$target" ]]; then
    echo "missing installed user unit: $target" >&2
    exit 1
  fi
done

CODEX_HOME="$tmpdir/codex" HOME="$tmpdir/home" \
  "$REPO_ROOT/scripts/uninstall-local.sh" >/dev/null

for helper in axiom-autonomy-scheduler axiom-codex-runner axiom-mail-filter axiom-render-codex-monitor axiom-send-markdown-mail axiom-teamcity-watch axiom-todo axiom-watch-codex-monitor; do
  target="$tmpdir/home/.local/bin/$helper"
  if [[ -e "$target" || -L "$target" ]]; then
    echo "helper still present after uninstall: $target" >&2
    exit 1
  fi
done

if [[ -e "$tmpdir/codex/skills/markdown-email" || -L "$tmpdir/codex/skills/markdown-email" ]]; then
  echo "skill still present after uninstall: $tmpdir/codex/skills/markdown-email" >&2
  exit 1
fi

for unit in axiom-autonomy.service axiom-autonomy.timer axiom-codex-monitor.service axiom-mail.path axiom-mail.service axiom-nightly.service axiom-nightly.timer; do
  target="$tmpdir/home/.config/systemd/user/$unit"
  if [[ -e "$target" || -L "$target" ]]; then
    echo "user unit still present after uninstall: $target" >&2
    exit 1
  fi
done

echo "bot-tools checks passed"
