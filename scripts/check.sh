#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[1/5] Python syntax checks"
python3 -m py_compile \
  "$REPO_ROOT/bin/axiom-autonomy-scheduler" \
  "$REPO_ROOT/bin/axiom-backfill-codex-summaries" \
  "$REPO_ROOT/bin/axiom-mail-filter" \
  "$REPO_ROOT/bin/axiom-mail-context" \
  "$REPO_ROOT/bin/axiom-render-codex-monitor" \
  "$REPO_ROOT/bin/axiom-review-followup" \
  "$REPO_ROOT/bin/axiom-send-markdown-mail" \
  "$REPO_ROOT/bin/axiom-teamcity-watch" \
  "$REPO_ROOT/bin/axiom-todo"

echo "[2/5] Python tests"
python3 -m unittest discover -s "$REPO_ROOT/tests"

echo "[3/5] Installer shell syntax"
bash -n "$REPO_ROOT/bin/axiom-codex-runner"
bash -n "$REPO_ROOT/bin/axiom-update-codex"
bash -n "$REPO_ROOT/bin/axiom-watch-codex-monitor"
bash -n "$REPO_ROOT/scripts/install-local.sh"
bash -n "$REPO_ROOT/scripts/update-local.sh"
bash -n "$REPO_ROOT/scripts/uninstall-local.sh"

# The Unix account is the automation security boundary; do not silently re-add
# Codex's inner sandbox when adjusting runner arguments.
if ! grep -q -- '--dangerously-bypass-approvals-and-sandbox' "$REPO_ROOT/bin/axiom-codex-runner"; then
  echo "runner does not disable Codex approvals and sandboxing" >&2
  exit 1
fi

echo "[4/5] Throwaway install smoke test"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

mkdir -p "$tmpdir/home" "$tmpdir/home/.config/systemd/user"
CODEX_HOME="$tmpdir/codex" HOME="$tmpdir/home" \
  "$REPO_ROOT/scripts/install-local.sh" --systemd >/dev/null

for helper in axiom-autonomy-scheduler axiom-backfill-codex-summaries axiom-codex-runner axiom-mail-context axiom-mail-filter axiom-render-codex-monitor axiom-review-followup axiom-send-markdown-mail axiom-teamcity-watch axiom-todo axiom-update-codex axiom-watch-codex-monitor; do
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

for helper in axiom-autonomy-scheduler axiom-backfill-codex-summaries axiom-codex-runner axiom-mail-context axiom-mail-filter axiom-render-codex-monitor axiom-review-followup axiom-send-markdown-mail axiom-teamcity-watch axiom-todo axiom-update-codex axiom-watch-codex-monitor; do
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

echo "[5/5] Throwaway managed update smoke test"
tmpdir2="$(mktemp -d)"
trap 'rm -rf "$tmpdir" "$tmpdir2"' EXIT

mkdir -p "$tmpdir2/home" "$tmpdir2/home/.config/systemd/user"
BOT_TOOLS_HOME="$tmpdir2/store" CODEX_HOME="$tmpdir2/codex" HOME="$tmpdir2/home" \
  "$REPO_ROOT/scripts/update-local.sh" --systemd >/dev/null

if [[ ! -L "$tmpdir2/store/current" ]]; then
  echo "missing managed current symlink: $tmpdir2/store/current" >&2
  exit 1
fi

for helper in axiom-autonomy-scheduler axiom-backfill-codex-summaries axiom-codex-runner axiom-mail-context axiom-mail-filter axiom-render-codex-monitor axiom-review-followup axiom-send-markdown-mail axiom-teamcity-watch axiom-todo axiom-update-codex axiom-watch-codex-monitor; do
  target="$tmpdir2/home/.local/bin/$helper"
  if [[ ! -L "$target" ]]; then
    echo "managed helper is not a symlink: $target" >&2
    exit 1
  fi
done

echo "bot-tools checks passed"
