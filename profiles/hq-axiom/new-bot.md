# Provisioning Another HQ Bot

This runbook covers the Hydraulic-specific layer on top of the portable setup in
[`docs/getting-started.md`](../../docs/getting-started.md). Use a dedicated Unix
account for every bot; the account is the security and ownership boundary.

## 1. Decide Identity And Scope

Before creating anything, record:

- the bot's human-facing name, with the `R.` prefix that identifies it as a robot
- its Unix account and `@hq.hydraulic.software` mailbox
- the repositories, services, credentials, and people it may interact with
- which actions require human review

Start with fewer privileges than Axiom. Expand them only when a concrete task
requires it.

## 2. Create The Host Account

As an administrator, create the Unix user and enable lingering so user services
run without an interactive login:

```bash
sudo adduser BOT_ACCOUNT
sudo loginctl enable-linger BOT_ACCOUNT
```

Configure disk quotas, groups, SSH keys, and repository access explicitly. Do
not copy Axiom's home directory or credential files.

## 3. Configure Mail Identity

Create the `@hq.hydraulic.software` address and deliver it to the new account's
Maildir. Configure the visible sender name with its robot prefix. Ensure outbound
mail is covered by Hydraulic's SPF/DKIM setup, then verify that a real received
message passes aligned DKIM before enabling mail-triggered automation.

The account-local bot-tools environment should contain values like:

```ini
BOT_MAIL_FROM="R. Example <example@hq.hydraulic.software>"
BOT_ENVELOPE_FROM=example@hq.hydraulic.software
BOT_MAIL_SIGNATURE="R. Example, AI employee."
BOT_REQUIRE_ALIGNED_DKIM=1
BOT_AUTH_RESULTS_ID=hq.hydraulic.software
```

Keep that file mode `0600`. Never commit credentials or tokens.

## 4. Install And Configure Bot Tools

Log in as the bot, clone the reviewed bot-tools branch, and follow the portable
getting-started guide. Use the managed release installer after checks pass:

```bash
scripts/check.sh
scripts/update-local.sh --systemd
```

Create the Maildir, account-specific allowlist, service environment, Codex
authentication, and an `AGENTS.md` that states the bot's mandate and boundaries.
Do not reuse Axiom's live state database, notes, Maildir, Codex session, or
automation lock.

## 5. Create Bot-Owned Repositories

HQ Gitolite allows each account to create repositories below its own username.
The first push to a nonexistent `BOT_ACCOUNT/NAME` repository creates it:

```bash
git init -b master NAME
cd NAME
printf '# NAME\n' > README.md
git add README.md
git commit -m 'Initial commit'
git remote add origin git@hq.hydraulic.software:BOT_ACCOUNT/NAME.git
git push -u origin master
```

Bot-owned repositories are readable by other HQ users. Publish review work as
`rr/BOT_ACCOUNT/CHANGE` in the bot-owned repository and send the branch name and
commit to the reviewer. Do not assume a same-named repository exists below the
reviewer's username.

## 6. Validate Before Enabling Wakeups

Validate each boundary independently:

1. send a dry-run Markdown message and inspect both MIME alternatives
2. send one real outbound message and confirm the `R.` identity, subtle AI
   signature, SPF, and DKIM at the recipient
3. deliver authenticated and deliberately unauthenticated inbound test messages
   and confirm only the authenticated message reaches `Maildir/new`
4. run timer, nightly, and mail modes manually and inspect their transcripts
5. confirm the monitor is private and requires HQ authentication
6. confirm the bot cannot access repositories or credentials outside its scope

Only then enable the user timers and mail path described in the portable guide.

## 7. First-Week Operation

Keep the initial mandate narrow, review outbound communication, and inspect the
monitor daily. Back up durable notes and configuration, but not transient locks
or resumable Codex session state. Document every new permission and why it was
granted so the account remains reproducible and auditable.
