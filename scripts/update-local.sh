#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PISTON_HOME="${PISTON_HOME:-${BOT_TOOLS_HOME:-${HOME}/.local/share/piston}}"
BIN_TARGET="${HOME}/.local/bin"
SKILLS_ROOT="${CODEX_HOME:-${HOME}/.codex}/skills"
SKILL_TARGET="${SKILLS_ROOT}/markdown-email"
SYSTEMD_TARGET="${HOME}/.config/systemd/user"
INSTALL_SYSTEMD=0
RESTART_RUNNING=0

usage() {
  cat <<'EOF'
Usage: scripts/update-local.sh [--systemd] [--restart-running]

Install/update this repo as a managed local release snapshot.

What it does:
- copies the current repo slice into ~/.local/share/piston/releases/<id>
- atomically repoints ~/.local/share/piston/current to that snapshot
- refreshes stable symlinks in ~/.local/bin and ${CODEX_HOME:-~/.codex}/skills
- optionally refreshes ~/.config/systemd/user links too

Options:
- --systemd          also refresh example user-unit links
- --restart-running  after daemon-reload, restart running piston services/units
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --systemd)
      INSTALL_SYSTEMD=1
      shift
      ;;
    --restart-running)
      RESTART_RUNNING=1
      INSTALL_SYSTEMD=1
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

release_id="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"
if [[ -n "$(git -C "$REPO_ROOT" status --porcelain 2>/dev/null || true)" ]]; then
  release_id+="-dirty-$(date +%Y%m%d%H%M%S)"
fi

release_root="${PISTON_HOME}/releases"
release_dir="${release_root}/${release_id}"
current_link="${PISTON_HOME}/current"
tmp_link="${PISTON_HOME}/.current.tmp"

mkdir -p "$release_root" "$BIN_TARGET" "$SKILLS_ROOT"

if [[ ! -d "$release_dir" ]]; then
  mkdir -p "$release_dir"
  cp -R "$REPO_ROOT/bin" "$release_dir/bin"
  cp -R "$REPO_ROOT/config" "$release_dir/config"
  cp -R "$REPO_ROOT/skills" "$release_dir/skills"
  if [[ -d "$REPO_ROOT/systemd" ]]; then
    cp -R "$REPO_ROOT/systemd" "$release_dir/systemd"
  fi
  cat > "${release_dir}/release.json" <<EOF
{
  "release_id": "${release_id}",
  "source_repo": "${REPO_ROOT}",
  "generated_at": "$(date --iso-8601=seconds)"
}
EOF
fi

ln -sfn "$release_dir" "$tmp_link"
mv -Tf "$tmp_link" "$current_link"

for helper in "$current_link"/bin/*; do
  [[ -f "$helper" ]] || continue
  helper_name="$(basename "$helper")"
  legacy_name="axiom-${helper_name#piston-}"
  ln -sfn "$helper" "${BIN_TARGET}/${helper_name}"
  ln -sfn "$helper_name" "${BIN_TARGET}/${legacy_name}"
  echo "Updated helper: ${BIN_TARGET}/${helper_name}"
  echo "Updated compatibility alias: ${BIN_TARGET}/${legacy_name}"
done

rm -rf "$SKILL_TARGET"
ln -sfn "$current_link/skills/markdown-email" "$SKILL_TARGET"
echo "Updated skill: ${SKILL_TARGET}"

if [[ "$INSTALL_SYSTEMD" == "1" ]]; then
  mkdir -p "$SYSTEMD_TARGET"
  for unit in "$current_link"/systemd/user/*; do
    [[ -f "$unit" ]] || continue
    unit_name="$(basename "$unit")"
    legacy_name="axiom-${unit_name#piston-}"
    ln -sfn "$unit" "${SYSTEMD_TARGET}/${unit_name}"
    ln -sfn "$unit_name" "${SYSTEMD_TARGET}/${legacy_name}"
    echo "Updated user unit: ${SYSTEMD_TARGET}/${unit_name}"
    echo "Updated compatibility alias: ${SYSTEMD_TARGET}/${legacy_name}"
  done
  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user daemon-reload || true
    if [[ "$RESTART_RUNNING" == "1" ]]; then
      for unit in "$current_link"/systemd/user/*; do
        [[ -f "$unit" ]] || continue
        unit_name="$(basename "$unit")"
        if systemctl --user is-active --quiet "$unit_name"; then
          systemctl --user restart "$unit_name" || true
          echo "Restarted user unit: ${unit_name}"
        fi
      done
    fi
  fi
fi

echo "Managed release ready: ${release_dir}"
python3 "$current_link/bin/piston-update-agent-instructions"
