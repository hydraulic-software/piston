# Codex CLI Upgrades

The automation account uses a local npm installation at `~/codex`, with `~/.local/bin/codex` pointing to `~/codex/node_modules/@openai/codex/bin/codex.js`.

Upgrade to an explicitly requested version with:

```bash
axiom-update-codex 0.144.4
```

The helper:

- accepts only an exact version, not `latest` or an npm range
- installs into a sibling staging directory
- checks that the staged CLI reports the requested version
- replaces `~/codex` only after verification
- retains the prior tree as `~/codex.backup-<timestamp>`
- restores the prior tree if post-install verification fails

After an upgrade, verify both the CLI and automation model selection:

```bash
codex --version
rg -n 'codex_model=' ~/.local/bin/axiom-codex-runner
```

An already-running Codex process keeps its existing binary and model. The next automation wakeup uses the new installation. If a model refresh motivated the upgrade, inspect that fresh process or its rollout `turn_context` to confirm the requested model rather than assuming the CLI upgrade changed the runner default.

Once the new version has run successfully, old timestamped backup directories can be removed deliberately. Do not delete the backup as part of the upgrade itself.

For a non-default install root, set `BOT_CODEX_INSTALL_DIR`. This is also the safe way to test the complete upgrade flow without touching the live CLI:

```bash
BOT_CODEX_INSTALL_DIR="$(mktemp -d)/codex" axiom-update-codex 0.144.4
```
