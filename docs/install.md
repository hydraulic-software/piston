# Local Install

This staging repo is still intentionally small, so the install story is small too.

## Quick start

From the repo root:

```bash
scripts/install-local.sh
```

That will:

- symlink all helpers from `bin/` into `~/.local/bin`
- symlink `skills/markdown-email` into `${CODEX_HOME:-~/.codex}/skills/markdown-email`

## Copy mode

If you want a standalone copy instead of live symlinks:

```bash
scripts/install-local.sh --copy
```

That copies the helper scripts and the skill directory into the same targets.

## What it does not install

This repo only stages the portable helper slice. It does not install any of the HQ-specific overlay pieces from `profiles/hq-axiom/`, such as:

- user `systemd` units
- the Codex runner
- the monitor renderer/publisher
- mail filtering policy

## Expectations

- `~/.local/bin` should already be on your `PATH`
- the Markdown mail helper expects `pandoc` and a working `sendmail`-compatible binary
- the TeamCity helper expects a valid TeamCity API token in the environment used by that host
