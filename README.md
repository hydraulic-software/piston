# Bot Tools

Local staging repo for a future shared helper/tooling slice that other assistants could plausibly clone.

This is intentionally a small first slice:

- `bin/axiom-send-markdown-mail`
- `bin/axiom-teamcity-watch`
- `bin/axiom-todo`
- `skills/markdown-email/SKILL.md`

The goal is to prove the extraction boundary before attempting to move more HQ-specific tooling like the Codex runner, monitor renderer, or mail filter.

## Current status

- staged locally only
- not pushed anywhere
- helpers are still named after their Axiom origin for now
- the included helpers have already been parameterized enough to run outside this exact HQ account
- a minimal local bootstrap path now exists via `scripts/install-local.sh`

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

For a simple local bootstrap from this repo:

```bash
scripts/install-local.sh
```

See [`docs/install.md`](docs/install.md) for the symlink-vs-copy behavior and current assumptions.
