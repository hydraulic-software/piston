# Linux Automation Slice

This repo now includes a small Linux-scoped automation layer in addition to the lighter helper scripts.

## Included pieces

- `bin/axiom-codex-runner`
  - shared mail / timer / nightly entrypoint for non-interactive Codex wakeups
- `bin/axiom-autonomy-scheduler`
  - workload-sensitive timer gating based on the active todo board
- `bin/axiom-mail-filter`
  - optional Maildir delivery filter with an env-configurable sender-domain allowlist
- `systemd/user/*.service`
- `systemd/user/*.timer`
- `systemd/user/*.path`

## Scope

This is still intentionally not the full HQ stack.

Included:

- Maildir-triggered wakeups
- periodic and nightly wakeups
- workload-sensitive timer gating

Not included yet:

- host-specific profile state
- HQ-specific mail-domain policy defaults

## Important knobs

- `BOT_TODO_FILE`
  - override the todo board path for `axiom-autonomy-scheduler` and `axiom-todo`
- `BOT_AUTONOMY_STATE_FILE`
  - override the scheduler state file
- `BOT_ALLOWED_FROM_DOMAINS`
  - comma-separated allowlist for `axiom-mail-filter`
  - if unset, the filter delivers all messages instead of dropping mail by surprise
- `BOT_MAILDIR`
  - override the Maildir root used by `axiom-mail-filter`
- `BOT_MAIL_FILTER_LOG`
  - override the drop log path used by `axiom-mail-filter`

## Install shape

Use `scripts/install-local.sh --systemd` to install the helpers, the `markdown-email` skill, and the example user units into the current account. That installs the units but does not enable them automatically.

After installation, the intended next steps are:

1. review the unit files under `~/.config/systemd/user`
2. run `systemctl --user daemon-reload`
3. enable the units you want, for example:
   - `systemctl --user enable --now axiom-autonomy.timer`
   - `systemctl --user enable --now axiom-nightly.timer`
   - `systemctl --user enable --now axiom-mail.path`
