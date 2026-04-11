# Bot Tools

Small shared helper/tooling slice for assistants that need lightweight mail, TeamCity, and todo helpers.

This is intentionally a small first slice:

- `bin/axiom-send-markdown-mail`
- `bin/axiom-teamcity-watch`
- `bin/axiom-todo`
- `skills/markdown-email/SKILL.md`

The goal is to prove the extraction boundary before attempting to move more HQ-specific tooling like the Codex runner, monitor renderer, or mail filter.

## Current status

- intentionally small first slice, not a full automation framework
- helpers still keep their Axiom-origin names for now
- the included helpers are parameterized enough to run outside this exact HQ account
- a minimal local bootstrap path exists via `scripts/install-local.sh`

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

## Layout

- `bin/`
  - portable helper scripts
- `skills/`
  - reusable Codex skills that pair with the helpers
- `docs/`
  - shared setup/migration notes
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

See [`docs/install.md`](docs/install.md) for the symlink-vs-copy behavior and current assumptions.

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
