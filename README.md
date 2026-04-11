# Bot Tools

Small shared helper/tooling slice for assistants that need lightweight mail, TeamCity, todo, and Linux automation helpers.

This is intentionally a small first slice:

- `bin/axiom-autonomy-scheduler`
- `bin/axiom-codex-runner`
- `bin/axiom-mail-filter`
- `bin/axiom-send-markdown-mail`
- `bin/axiom-teamcity-watch`
- `bin/axiom-todo`
- `systemd/user/*.service|*.timer|*.path`
- `skills/markdown-email/SKILL.md`

The goal is to prove the extraction boundary before attempting to move more HQ-specific tooling like the Codex runner, monitor renderer, or mail filter.

## Current status

- intentionally small first slice, not a full automation framework
- helpers still keep their Axiom-origin names for now
- the included helpers are parameterized enough to run outside this exact HQ account
- a minimal local bootstrap path exists via `scripts/install-local.sh`
- an optional Linux user-unit slice now exists under `systemd/user/`

## Portable knobs already added

- `axiom-send-markdown-mail`
  - `BOT_MAIL_FROM`
  - `BOT_ENVELOPE_FROM`
  - `BOT_SENDMAIL`
- `axiom-teamcity-watch`
  - `--base-url`
  - `TEAMCITY_BASE_URL`
- `axiom-todo`
  - `BOT_TODO_FILE`
  - `list --active`
- `axiom-autonomy-scheduler`
  - `BOT_TODO_FILE`
  - `BOT_AUTONOMY_STATE_FILE`
- `axiom-mail-filter`
  - `BOT_ALLOWED_FROM_DOMAINS`
  - `BOT_MAILDIR`
  - `BOT_MAIL_FILTER_LOG`

## Layout

- `bin/`
  - portable helper scripts
- `skills/`
  - reusable Codex skills that pair with the helpers
- `docs/`
  - shared setup/migration notes
- `systemd/user/`
  - example Linux user units for timer, nightly, and Maildir-triggered wakeups
- `profiles/`
  - host/account-specific overlays that should not become the default shared behavior
- `scripts/`
  - small install/bootstrap helpers for local use

## Install

Clone it:

```bash
git clone git@hq.hydraulic.software:axiom/bot-tools.git
cd bot-tools
```

For a simple local bootstrap from this repo:

```bash
scripts/install-local.sh
```

For the Linux automation slice as well:

```bash
scripts/install-local.sh --systemd
```

See [`docs/install.md`](docs/install.md) for the symlink-vs-copy behavior and current assumptions, and [`docs/linux-automation-slice.md`](docs/linux-automation-slice.md) for the Linux user-unit layer.

For the matching removal path:

```bash
scripts/uninstall-local.sh
```

## Validation

For a quick local sanity check of the staged slice:

```bash
scripts/check.sh
```

That runs Python syntax checks and a throwaway install smoke test.
