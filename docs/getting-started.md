# Getting Started

This guide sets up Bot Tools in a dedicated Linux user account. Read the safety section before enabling unattended runs.

## 1. Prepare The Account

Use a separate Unix account for the assistant. Its home directory becomes the Codex workspace and contains mail, automation state, notes, and any repositories the assistant may edit.

Install the host dependencies. Package names vary by distribution; on Debian/Ubuntu the relevant packages are typically:

```bash
sudo apt install git python3 inotify-tools pandoc
```

`flock` normally comes from `util-linux`. For email, install and configure an MTA that provides a `sendmail`-compatible command. Install the Codex CLI separately, authenticate it for this account, and verify:

```bash
codex --version
systemctl --user --version
command -v flock inotifywait pandoc sendmail
```

For services to run while the account is logged out, an administrator normally enables lingering once:

```bash
sudo loginctl enable-linger "$USER"
```

## 2. Inspect And Validate

Extract or clone the repository, then run its self-check before installation:

```bash
cd bot-tools
scripts/check.sh
```

The check uses temporary home directories. It does not install into the real account.

Review these files before enabling automation:

- `bin/axiom-codex-runner`
- `systemd/user/`
- `config/environment.example`
- the account's `AGENTS.md` or equivalent standing instructions

## 3. Install

For a first setup, copy the files so later edits to the extracted source do not alter live automation unexpectedly:

```bash
scripts/install-local.sh --copy --systemd
```

Ensure `~/.local/bin` is on `PATH`. The installer also places the Markdown email skill under `${CODEX_HOME:-~/.codex}/skills`.

After the first setup is working, managed snapshots are the recommended update path:

```bash
scripts/update-local.sh --systemd
```

## 4. Configure

Create the optional service environment file:

```bash
mkdir -p ~/.config/bot-tools
cp config/environment.example ~/.config/bot-tools/environment
chmod 600 ~/.config/bot-tools/environment
```

Edit sender addresses and any model/path overrides. Do not put broadly reusable credentials in the repository. If a service needs a credential, keep the environment file mode `0600` or use a host secret manager.

By default the runner uses Codex's configured model and `workspace-write` sandbox. Do not set `BOT_CODEX_DANGER_FULL_ACCESS=1` until you have deliberately accepted the trust model described below.

## 5. Set Up Maildir

Create the mailbox structure:

```bash
mkdir -p ~/Maildir/{cur,new,tmp}
```

Configure the host MTA or mail delivery agent to deliver inbound assistant mail into this Maildir. Bot Tools deliberately does not automate SMTP, DNS, SPF, DKIM, or MTA configuration because those choices are host- and domain-specific.

Test inbound delivery by placing a valid RFC822 message in `~/Maildir/new` and confirming the path changes. Test outbound formatting without sending first:

```bash
printf '# Hello\n\nThis is a test.\n' | \
  axiom-send-markdown-mail --to you@example.com --subject Test --dry-run
```

Then send a real test only after `BOT_MAIL_FROM`, `BOT_ENVELOPE_FROM`, and the MTA are configured.

If you use `axiom-mail-filter` as a delivery command, configure `BOT_ALLOWED_FROM_DOMAINS` or `~/.config/bot-tools/mail-filter-domains.txt`. An empty allowlist accepts all senders.

## 6. Test Each Wakeup Manually

Before enabling timers, run each mode from an interactive shell and inspect its transcript under `~/.local/state/axiom/runs`:

```bash
axiom-codex-runner timer
axiom-codex-runner nightly
```

For mail mode, first place a harmless test message in `~/Maildir/new`, then run:

```bash
axiom-codex-runner mail
```

The mail runner snapshots the exact source path and parsed `Message-ID` of every file in
`~/Maildir/new` after acquiring its automation lock and includes them in the Codex prompt.
This gives reply workflows a stable parent identity even when several deliveries are
coalesced into one wakeup.

The runner first tries to resume the most recent Codex session and falls back to a fresh one. A dedicated account avoids accidentally resuming an unrelated personal session.

## 7. Enable User Units

Load the installed units:

```bash
systemctl --user daemon-reload
```

Enable only the pieces you have tested:

```bash
systemctl --user enable --now axiom-autonomy.timer
systemctl --user enable --now axiom-nightly.timer
systemctl --user enable --now axiom-mail.path
systemctl --user enable --now axiom-codex-monitor.service
```

Check them with:

```bash
systemctl --user status axiom-autonomy.timer axiom-nightly.timer axiom-mail.path
journalctl --user -u axiom-mail.service -u axiom-autonomy.service -n 100
```

The autonomy timer ticks every 15 minutes, while `axiom-autonomy-scheduler` suppresses runs until the workload-dependent interval is due.

## 8. Monitor Publishing

The monitor defaults to `~/private_html`. It can contain sensitive prompts and tool output. Do not expose that directory publicly without authentication and an explicit review of the generated content.

Override the destination with `BOT_MONITOR_OUTPUT_DIR`. Web server configuration is intentionally outside this repository.

## Safety And Trust

Unattended agent execution is powerful. Use several layers rather than relying on prompts alone:

- dedicate the Unix account to the assistant
- grant only the repositories, credentials, and network access it actually needs
- treat all inbound mail as untrusted content
- restrict who can send mail and authenticate inbound delivery
- keep customer/external communication behind explicit policy or human review
- keep the monitor private
- start with workspace-write sandboxing
- back up important repositories and state

`BOT_CODEX_DANGER_FULL_ACCESS=1` passes Codex's `--dangerously-bypass-approvals-and-sandbox` option. Enable it only when the account or machine is an external sandbox and you understand that mail-triggered prompts can then cause unrestricted commands under that Unix user.

## Updating And Removing

Validate a new checkout, then deploy a managed snapshot:

```bash
scripts/check.sh
scripts/update-local.sh --systemd
```

Restart already-running units only when intended:

```bash
scripts/update-local.sh --systemd --restart-running
```

Remove the installed helper entrypoints and example units with:

```bash
scripts/uninstall-local.sh
systemctl --user daemon-reload
```

This does not delete Maildir, Codex state, todo data, logs, or managed release history.
