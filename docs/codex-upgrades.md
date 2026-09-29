# Codex CLI Upgrades

Piston pins one Codex CLI version in `config/codex-version`. Every automation
account uses a local npm installation at `~/codex`, with `~/.local/bin/codex`
pointing to `~/codex/node_modules/@openai/codex/bin/codex.js`. The runner checks
the live CLI against Piston's pin before starting a session, preventing rollout
formats from drifting between employees.

Install the version selected by the current Piston release with:

```bash
piston-update-codex
```

An explicit exact version remains available for testing or emergency rollback,
but it will not pass the runner check unless Piston's pin matches:

```bash
piston-update-codex 0.159.0
```

The helper:

- reads an exact version from Piston, never `latest` or an npm range
- installs into a sibling staging directory
- checks that the staged CLI reports the requested version
- replaces `~/codex` only after verification
- retains the prior tree as `~/codex.backup-<timestamp>`
- restores the prior tree if post-install verification fails
- selects the managed installation through `~/.local/bin/codex`

Verify an account without changing it:

```bash
piston-update-codex --check
```

After an upgrade, verify both the CLI and automation model selection:

```bash
codex --version
rg -n 'codex_model=' ~/.local/bin/piston-codex-runner
```

An already-running Codex process keeps its existing binary and model. The next automation wakeup uses the new installation. If a model refresh motivated the upgrade, inspect that fresh process or its rollout `turn_context` to confirm the requested model rather than assuming the CLI upgrade changed the runner default.

Once the new version has run successfully, old timestamped backup directories can be removed deliberately. Do not delete the backup as part of the upgrade itself.

For a non-default install root, set `BOT_CODEX_INSTALL_DIR`. This is also the safe way to test the complete upgrade flow without touching the live CLI:

```bash
test_root="$(mktemp -d)"
BOT_CODEX_INSTALL_DIR="$test_root/codex" \
BOT_CODEX_BIN_LINK="$test_root/bin/codex" \
  piston-update-codex 0.159.0
```
