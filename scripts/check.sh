#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[1/5] Python syntax checks"
python3 -m py_compile \
  "$REPO_ROOT/bin/piston-autonomy-scheduler" \
  "$REPO_ROOT/bin/piston-backfill-codex-summaries" \
  "$REPO_ROOT/bin/piston-mail-filter" \
  "$REPO_ROOT/bin/piston-mail-context" \
  "$REPO_ROOT/bin/piston-render-codex-monitor" \
  "$REPO_ROOT/bin/piston-nightly-summary" \
  "$REPO_ROOT/bin/piston-review-followup" \
  "$REPO_ROOT/bin/piston-send-markdown-mail" \
  "$REPO_ROOT/bin/piston-teamcity-watch" \
  "$REPO_ROOT/bin/piston-todo"

echo "[2/5] Python tests"
python3 -m unittest discover -s "$REPO_ROOT/tests"

echo "[3/5] Installer shell syntax"
bash -n "$REPO_ROOT/bin/piston-codex-runner"
bash -n "$REPO_ROOT/bin/piston-update-codex"
bash -n "$REPO_ROOT/bin/piston-watch-codex-monitor"
bash -n "$REPO_ROOT/bin/piston-watch-mail"
bash -n "$REPO_ROOT/scripts/install-local.sh"
bash -n "$REPO_ROOT/scripts/update-local.sh"
bash -n "$REPO_ROOT/scripts/uninstall-local.sh"

# The Unix account is the automation security boundary; do not silently re-add
# Codex's inner sandbox when adjusting runner arguments.
if ! grep -q -- '--dangerously-bypass-approvals-and-sandbox' "$REPO_ROOT/bin/piston-codex-runner"; then
  echo "runner does not disable Codex approvals and sandboxing" >&2
  exit 1
fi

if ! grep -q -- 'BOT_REQUIRE_ALIGNED_DKIM' "$REPO_ROOT/config/environment.example"; then
  echo "environment example omits the unattended-mail authentication control" >&2
  exit 1
fi

if ! grep -q -- 'repeated, stable workflows' "$REPO_ROOT/bin/piston-codex-runner"; then
  echo "nightly prompt omits skill-curation guidance" >&2
  exit 1
fi

echo "[4/5] Throwaway install smoke test"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

mkdir -p "$tmpdir/home" "$tmpdir/home/.config/systemd/user"
CODEX_HOME="$tmpdir/codex" HOME="$tmpdir/home" \
  "$REPO_ROOT/scripts/install-local.sh" --systemd >/dev/null

for helper in piston-autonomy-scheduler piston-backfill-codex-summaries piston-codex-runner piston-mail-context piston-mail-filter piston-nightly-summary piston-render-codex-monitor piston-review-followup piston-send-markdown-mail piston-teamcity-watch piston-todo piston-update-codex piston-watch-codex-monitor piston-watch-mail; do
  target="$tmpdir/home/.local/bin/$helper"
  if [[ ! -e "$target" ]]; then
    echo "missing installed helper: $target" >&2
    exit 1
  fi
  legacy="$tmpdir/home/.local/bin/axiom-${helper#piston-}"
  if [[ ! -L "$legacy" || ! -e "$legacy" ]]; then
    echo "missing installed compatibility alias: $legacy" >&2
    exit 1
  fi
done

if [[ ! -e "$tmpdir/codex/skills/markdown-email/SKILL.md" ]]; then
  echo "missing installed skill: $tmpdir/codex/skills/markdown-email/SKILL.md" >&2
  exit 1
fi

for unit in piston-autonomy.service piston-autonomy.timer piston-codex-monitor.service piston-mail.path piston-mail.service piston-nightly.service piston-nightly.timer; do
  target="$tmpdir/home/.config/systemd/user/$unit"
  if [[ ! -e "$target" ]]; then
    echo "missing installed user unit: $target" >&2
    exit 1
  fi
  legacy="$tmpdir/home/.config/systemd/user/axiom-${unit#piston-}"
  if [[ ! -L "$legacy" || ! -e "$legacy" ]]; then
    echo "missing installed unit compatibility alias: $legacy" >&2
    exit 1
  fi
done

CODEX_HOME="$tmpdir/codex" HOME="$tmpdir/home" \
  "$REPO_ROOT/scripts/uninstall-local.sh" >/dev/null

for helper in piston-autonomy-scheduler piston-backfill-codex-summaries piston-codex-runner piston-mail-context piston-mail-filter piston-nightly-summary piston-render-codex-monitor piston-review-followup piston-send-markdown-mail piston-teamcity-watch piston-todo piston-update-codex piston-watch-codex-monitor piston-watch-mail; do
  target="$tmpdir/home/.local/bin/$helper"
  if [[ -e "$target" || -L "$target" ]]; then
    echo "helper still present after uninstall: $target" >&2
    exit 1
  fi
  legacy="$tmpdir/home/.local/bin/axiom-${helper#piston-}"
  if [[ -e "$legacy" || -L "$legacy" ]]; then
    echo "compatibility alias still present after uninstall: $legacy" >&2
    exit 1
  fi
done

if [[ -e "$tmpdir/codex/skills/markdown-email" || -L "$tmpdir/codex/skills/markdown-email" ]]; then
  echo "skill still present after uninstall: $tmpdir/codex/skills/markdown-email" >&2
  exit 1
fi

for unit in piston-autonomy.service piston-autonomy.timer piston-codex-monitor.service piston-mail.path piston-mail.service piston-nightly.service piston-nightly.timer; do
  target="$tmpdir/home/.config/systemd/user/$unit"
  if [[ -e "$target" || -L "$target" ]]; then
    echo "user unit still present after uninstall: $target" >&2
    exit 1
  fi
  legacy="$tmpdir/home/.config/systemd/user/axiom-${unit#piston-}"
  if [[ -e "$legacy" || -L "$legacy" ]]; then
    echo "unit compatibility alias still present after uninstall: $legacy" >&2
    exit 1
  fi
done

echo "[5/5] Throwaway managed update smoke test"
tmpdir2="$(mktemp -d)"
trap 'rm -rf "$tmpdir" "$tmpdir2"' EXIT

mkdir -p "$tmpdir2/home" "$tmpdir2/home/.config/systemd/user"
PISTON_HOME="$tmpdir2/store" CODEX_HOME="$tmpdir2/codex" HOME="$tmpdir2/home" \
  "$REPO_ROOT/scripts/update-local.sh" --systemd >/dev/null

if [[ ! -L "$tmpdir2/store/current" ]]; then
  echo "missing managed current symlink: $tmpdir2/store/current" >&2
  exit 1
fi

for helper in piston-autonomy-scheduler piston-backfill-codex-summaries piston-codex-runner piston-mail-context piston-mail-filter piston-nightly-summary piston-render-codex-monitor piston-review-followup piston-send-markdown-mail piston-teamcity-watch piston-todo piston-update-codex piston-watch-codex-monitor piston-watch-mail; do
  target="$tmpdir2/home/.local/bin/$helper"
  if [[ ! -L "$target" ]]; then
    echo "managed helper is not a symlink: $target" >&2
    exit 1
  fi
  legacy="$tmpdir2/home/.local/bin/axiom-${helper#piston-}"
  if [[ ! -L "$legacy" || ! -e "$legacy" ]]; then
    echo "missing managed compatibility alias: $legacy" >&2
    exit 1
  fi
done

for unit in piston-autonomy.service piston-autonomy.timer piston-codex-monitor.service piston-mail.path piston-mail.service piston-nightly.service piston-nightly.timer; do
  target="$tmpdir2/home/.config/systemd/user/$unit"
  legacy="$tmpdir2/home/.config/systemd/user/axiom-${unit#piston-}"
  if [[ ! -L "$target" || ! -L "$legacy" || ! -e "$legacy" ]]; then
    echo "missing managed user unit or compatibility alias: $unit" >&2
    exit 1
  fi
done

echo "piston checks passed"
