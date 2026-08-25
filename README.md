# Bot Tools

Bot Tools is a small, inspectable automation kit for running a Codex-based assistant from a dedicated Linux user account. It connects three useful loops:

- wake Codex when mail arrives in a local Maildir
- run workload-aware autonomous and nightly check-ins with `systemd --user`
- publish a private HTML/JSON activity monitor with a lightweight todo board

The repository also includes Markdown email, TeamCity, review-follow-up, and staged Codex-upgrade helpers. It grew out of a real assistant account, so commands retain the `axiom-` prefix, but the main paths and identities are configurable.

## Start Here

Read [`docs/getting-started.md`](docs/getting-started.md). It covers prerequisites, a throwaway validation run, installation, configuration, mail delivery, enabling timers, safety boundaries, and rollback.

The shortest safe evaluation path is:

```bash
tar -xf bot-tools.tar.gz
cd bot-tools
scripts/check.sh
scripts/install-local.sh --copy
```

Copy mode is recommended for a first evaluation. Once the setup is understood, [`scripts/update-local.sh`](scripts/update-local.sh) provides versioned release snapshots and stable entrypoints.

## Included Components

- `bin/axiom-codex-runner`: non-interactive mail, timer, and nightly Codex entrypoint
- `bin/axiom-autonomy-scheduler`: changes timer cadence based on active/background todos
- `bin/axiom-mail-filter`: optional sender-domain filter that delivers RFC822 messages into Maildir
- `bin/axiom-render-codex-monitor` and `bin/axiom-watch-codex-monitor`: private activity pages with incremental refreshes
- `bin/axiom-todo`: small JSON-backed rolling todo board
- `bin/axiom-send-markdown-mail`: multipart plain-text/HTML mail with reply threading and named attachments
- `bin/axiom-teamcity-watch`: TeamCity build polling and log tails
- `bin/axiom-review-followup`: opinionated review-worktree/TeamCity follow-up helper
- `bin/axiom-update-codex`: staged, exact-version Codex CLI upgrades
- `systemd/user/`: example user services, timers, and Maildir path watcher
- `skills/markdown-email/`: companion Codex skill for reliable email formatting

## Requirements

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
~/.config/bot-tools/environment
```

Start from [`config/environment.example`](config/environment.example). Important knobs include:

- `BOT_CODEX_MODEL`: optional model override; unset uses the Codex default
- `BOT_MAIL_FROM`, `BOT_ENVELOPE_FROM`, `BOT_SENDMAIL`: outbound identity and transport
- `BOT_ALLOWED_FROM_DOMAINS`, `BOT_MAILDIR`: inbound filtering and Maildir location
- `BOT_REQUIRE_ALIGNED_DKIM`, `BOT_AUTH_RESULTS_ID`: require a trusted local
  `Authentication-Results` header with `dkim=pass` aligned exactly to `From`
- `BOT_TODO_FILE`, `BOT_AUTONOMY_STATE_FILE`: scheduler/todo state
- `BOT_MONITOR_OUTPUT_DIR`, `BOT_CODEX_STATE_DB`, `BOT_RUN_LOG_DIR`: monitor inputs/outputs
- `TEAMCITY_BASE_URL`, `TEAMCITY_API_KEY`: optional TeamCity integration

## Safety Model

Bot Tools deliberately uses the Unix account as its security boundary. On every mail, timer, and nightly invocation, `axiom-codex-runner` passes Codex `--dangerously-bypass-approvals-and-sandbox`; there is no supported mode in which the runner relies on Codex's own approvals or filesystem sandbox.

Install Bot Tools only in a dedicated account prepared for that trust model. Before enabling unattended wakeups:

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

The mail/timer/nightly loop, todo board, and monitor are the reusable core. `axiom-review-followup` and `profiles/hq-axiom/` are examples from the original deployment and remain intentionally opinionated around its repository naming and workflow. They are safe to ignore or adapt.

More detail:

- [`docs/linux-automation-slice.md`](docs/linux-automation-slice.md)
- [`docs/monitor-slice.md`](docs/monitor-slice.md)
- [`docs/codex-upgrades.md`](docs/codex-upgrades.md)
- [`docs/portable-helper-slice.md`](docs/portable-helper-slice.md)
