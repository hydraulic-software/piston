# Local Install

This repo is still intentionally small, so the install story is still lightweight too.

## Quick start

From the repo root:

```bash
scripts/install-local.sh
```

That will:

- symlink all helpers from `bin/` into `~/.local/bin`
- symlink `skills/markdown-email` into `${CODEX_HOME:-~/.codex}/skills/markdown-email`

If you also want the example Linux user units:

```bash
scripts/install-local.sh --systemd
```

That additionally installs the example files from `systemd/user/` into `~/.config/systemd/user`.

## Copy mode

If you want a standalone copy instead of live symlinks:

```bash
scripts/install-local.sh --copy
```

That copies the helper scripts and the skill directory into the same targets. You can combine it with `--systemd` if you want copied user units too.

## Uninstall

To remove the staged helper slice from the current account:

```bash
scripts/uninstall-local.sh
```

That removes the installed helper entry names from `~/.local/bin`, the staged `markdown-email` skill from `${CODEX_HOME:-~/.codex}/skills`, and any matching example user-unit files from `~/.config/systemd/user`.

## Managed updates

If you want repo changes to behave more like software updates, use:

```bash
scripts/update-local.sh --systemd
```

That does **not** point your live entrypoints at the repo working tree. Instead it:

- copies the current repo slice into `~/.local/share/bot-tools/releases/<id>`
- atomically repoints `~/.local/share/bot-tools/current`
- refreshes the stable links in `~/.local/bin`, `${CODEX_HOME:-~/.codex}/skills`, and optionally `~/.config/systemd/user`

This is the safer path for shell-heavy tooling because the running system sees a stable installed snapshot rather than a repo checkout that might change mid-interpretation.

If you explicitly want running user units restarted after the update:

```bash
scripts/update-local.sh --systemd --restart-running
```

## What it does not install

This repo now includes a Linux automation slice and a reusable monitor slice too, but it still does not install the more HQ-specific overlay pieces from `profiles/hq-axiom/`, such as:

- HQ-specific mail filtering policy defaults

## Expectations

- `~/.local/bin` should already be on your `PATH`
- the Markdown mail helper expects `pandoc` and a working `sendmail`-compatible binary
- the TeamCity helper expects a valid TeamCity API token in the environment used by that host

## Validation

To verify the staged slice without touching your real account state:

```bash
scripts/check.sh
```

That script syntax-checks the Python helpers, syntax-checks the installer, and runs a throwaway install into a temporary `HOME` / `CODEX_HOME`, including the example user-unit files.
