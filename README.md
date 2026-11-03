# Piston

Piston is a small, inspectable automation kit for running a Codex-based assistant from a dedicated Linux user account. It connects three useful loops:

- wake Codex when mail arrives in a local Maildir
- run workload-aware autonomous and nightly check-ins with `systemd --user`
- publish a private HTML/JSON activity monitor with a lightweight todo board

The repository also includes Markdown email, TeamCity, review-follow-up, and staged Codex-upgrade helpers. Commands use the neutral `piston-` prefix, while temporary `axiom-*` compatibility aliases keep existing installations working during migration. The main paths and identities are configurable.

## Start Here

Read [`docs/getting-started.md`](docs/getting-started.md). It covers prerequisites, a throwaway validation run, installation, configuration, mail delivery, enabling timers, safety boundaries, and rollback.

The shortest safe evaluation path is:

```bash
tar -xf piston.tar.gz
cd piston
scripts/check.sh
scripts/install-local.sh --copy
```

Copy mode is recommended for a first evaluation. Once the setup is understood, [`scripts/update-local.sh`](scripts/update-local.sh) provides versioned release snapshots and stable entrypoints.

## Included Components

- `bin/piston-codex-runner`: non-interactive mail, timer, and nightly Codex entrypoint
- `bin/piston-autonomy-scheduler`: changes timer cadence based on active/background todos
- `bin/piston-mail-filter`: optional sender-domain filter that delivers RFC822 messages into Maildir
- `bin/piston-render-codex-monitor` and `bin/piston-watch-codex-monitor`: private activity pages with incremental refreshes
- `bin/piston-todo`: small JSON-backed rolling todo board
- `bin/piston-send-markdown-mail`: multipart plain-text/HTML mail with reply threading and named attachments
- `bin/piston-teamcity-watch`: TeamCity build polling and log tails
- `bin/piston-review-followup`: opinionated review-worktree/TeamCity follow-up helper
- `bin/piston-update-codex`: staged upgrades to Piston's pinned Codex CLI version
- `systemd/user/`: example user services, timers, and Maildir path watcher
- `skills/markdown-email/`: companion Codex skill for reliable email formatting

## Requirements

### Recurring tasks

`piston-todo schedule monthly-triage "Review open issues; done when outcomes are recorded" --next-due 2026-10-30`
creates a monthly schedule in the same JSON board. `piston-todo schedules` lists
schedules. The autonomy timer's `due` check runs `piston-todo tick` before counting
work, so due occurrences become ordinary todos even during routine six-hour
cadence. Completion with `piston-todo done ID` advances to the next future monthly
date. Month-end dates retain their original day where possible. Missed months
produce one task, not a catch-up storm; unfinished tasks are never duplicated.
All helper board updates use a shared lock. Schedules create reminders only,
never perform external actions. Cadence currently supports monthly tasks only;
schedule edits/removal use the JSON board while no helper is writing it.

The monitor includes a live Scheduled tasks section with cadence, next due
date and active occurrence. Install/upgrade refreshes a marked Piston guidance
block in home `AGENTS.md`, preserving all employee-owned text outside it.
Malformed markers or a symlink cause a safe refusal rather than an overwrite.
Set `PISTON_AGENT_INSTRUCTIONS` to select a different instructions path.

Core automation expects:

- Linux with `systemd --user`
- Bash, Python 3.10+, Git, `flock`, and `inotifywait`
- an installed and authenticated `codex` CLI
- a dedicated Unix account whose home directory is the assistant workspace

Email additionally needs:

- a Maildir at `~/Maildir`
- an MTA or delivery rule that places inbound messages in `~/Maildir/new`
- a `sendmail`-compatible command and Pandoc for formatted outbound mail

The repository does not configure DNS, SMTP credentials, DKIM, an MTA, or public web serving. Those are host policy and should be set up separately.

## Installation Modes

```bash
# Symlink helpers to this checkout.
scripts/install-local.sh

# Copy helpers so the install is independent of the checkout.
scripts/install-local.sh --copy

# Include example systemd user units.
scripts/install-local.sh --copy --systemd

# Install an immutable release snapshot and stable symlinks.
scripts/update-local.sh --systemd
```

Remove installed helper names and units with:

```bash
scripts/uninstall-local.sh
```

See [`docs/install.md`](docs/install.md) for details.

## Configuration

The user services optionally read:

```text
~/.config/piston/environment
```

Start from [`config/environment.example`](config/environment.example). Important knobs include:

- `BOT_CODEX_MODEL`: optional model override; unset uses the Codex default
- `BOT_MAIL_FROM`, `BOT_ENVELOPE_FROM`, `BOT_SENDMAIL`: outbound identity and transport
- `BOT_ALLOWED_FROM_DOMAINS`, `BOT_MAILDIR`: inbound filtering and Maildir location
- `BOT_MAIL_SHARED_CONTACTS`: optional administrator-provisioned shared UTF-8
  file of exact sender addresses (one per line, ending in LF). All employee
  filters must use the same file. Reads/writes use advisory locking and updates
  are append-only/deduplicated; its parent must not be writable by outsiders.
- `BOT_MAIL_INTRODUCERS`: comma-separated exact addresses allowed to introduce
  external To/Cc recipients through authenticated mail. Learned contacts can
  introduce further exact addresses in authenticated CC chains, never grant
  whole-domain access, and still require aligned DKIM or the configured
  authenticated-local identity. Outbound contact authority is the operator's
  policy, not a consequence of an unauthenticated header. These settings must reach the delivery filter
  (for HQ, `.forward` environment), not merely the Codex service environment.

Example shared-file provisioning by the administrator (replace employee names):

Preferred rerunnable entry point, after participating accounts deploy this version:

```sh
sudo python3 scripts/setup-shared-mail.py --user axiom --user daneel --introducer mike@hydraulic.software
```

Use `--dry-run` first. `--state-dir` and `--group` parameterize shared storage.
It requires `acl` (`setfacl`) and `util-linux` (`setpriv`). Postfix command
delivery omits supplementary groups, so it grants named-user ACLs on the shared
directory/file and checks read/write access with `--clear-groups` before editing
each delivery configuration. A normal login/`sg` check is not sufficient.
It refuses unmanaged forwarding rules or absent aligned-DKIM configuration,
preserves existing auth variables, backs up the original `.forward`, and leaves
contact contents intact on rerun. It does not update other accounts' Piston
versions; deploy those first. This is separate from temporary DNS failure retry.

Equivalent manual provisioning for unusual installations:

```sh
groupadd --system piston-mail-contacts
install -d -o root -g piston-mail-contacts -m 0750 /var/lib/piston-mail
touch /var/lib/piston-mail/contacts
chown root:piston-mail-contacts /var/lib/piston-mail/contacts
chmod 0660 /var/lib/piston-mail/contacts
usermod -aG piston-mail-contacts axiom
usermod -aG piston-mail-contacts daneel
```

Configure each delivery filter with
`BOT_MAIL_SHARED_CONTACTS=/var/lib/piston-mail/contacts` and the actual trusted
introducer address in `BOT_MAIL_INTRODUCERS`. Refresh delivery-process group
membership and test both accounts. Do not use a world-writable file. Missing or
unwritable configured files fail delivery rather than silently losing shared
updates; monitor mail queues. Existing messages are not automatically replayed.
- `BOT_REQUIRE_ALIGNED_DKIM`, `BOT_AUTH_RESULTS_ID`: require a trusted local
  `Authentication-Results` header with `dkim=pass` aligned exactly to `From`
- `BOT_TRUST_LOCAL_SUBMISSION`, `BOT_LOCAL_MAIL_DOMAIN`: optionally accept a
  same-host Postfix submission when its trusted UID maps exactly to the visible
  sender address; this does not exempt inbound SMTP from aligned DKIM
- `BOT_TODO_FILE`, `BOT_AUTONOMY_STATE_FILE`: scheduler/todo state
- `BOT_MONITOR_OUTPUT_DIR`, `BOT_CODEX_STATE_DB`, `BOT_RUN_LOG_DIR`: monitor inputs/outputs
- `BOT_MONITOR_NAME`, `BOT_MONITOR_AVATAR`: visible monitor identity and optional favicon source
- `TEAMCITY_BASE_URL`, `TEAMCITY_API_KEY`: optional TeamCity integration

## Safety Model

Piston deliberately uses the Unix account as its security boundary. On every mail, timer, and nightly invocation, `piston-codex-runner` passes Codex `--dangerously-bypass-approvals-and-sandbox`; there is no supported mode in which the runner relies on Codex's own approvals or filesystem sandbox.

Install Piston only in a dedicated account prepared for that trust model. Before enabling unattended wakeups:

- limit the account's filesystem permissions to data the assistant is allowed to read and change
- expose only the credentials, network services, and command-line tools the assistant is allowed to use without per-command approval
- do not grant root access or membership in privileged groups unless that is an intentional part of the deployment
- treat the whole account as potentially controlled by any prompt that the automation accepts

Mail is untrusted input, and mail wakeups run with every permission available to the assistant account. A sender allowlist reduces accidental wakeups but is not a complete security boundary: authenticate inbound mail, restrict account permissions, constrain who can trigger automation, and keep external communication behind an appropriate policy or review step.

The monitor may expose prompts, paths, command output, and mail-derived text. Publish it only to a private/authenticated location.

## Validation

Run:

```bash
scripts/check.sh
```

This performs Python syntax checks, unit tests, shell syntax checks, a throwaway install/uninstall test, and a managed-release smoke test without changing the real account.

## Scope And Known Opinions

The mail/timer/nightly loop, todo board, and monitor are the reusable core. `piston-review-followup` and `profiles/hq-axiom/` are examples from the original deployment and remain intentionally opinionated around its repository naming and workflow. They are safe to ignore or adapt.

More detail:

- [`docs/linux-automation-slice.md`](docs/linux-automation-slice.md)
- [`docs/monitor-slice.md`](docs/monitor-slice.md)
- [`docs/codex-upgrades.md`](docs/codex-upgrades.md)
- [`docs/portable-helper-slice.md`](docs/portable-helper-slice.md)
