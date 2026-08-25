---
name: markdown-email
description: Use when sending or replying to email from the current bot account and you want reliable formatting. Converts Markdown into multipart plain-text + HTML mail with the companion `axiom-send-markdown-mail` helper, and can auto-thread replies from a Maildir message file.
---

# Markdown Email

Use this skill when composing email from the current bot account and the message should preserve formatting cleanly in Gmail or similar clients.

## Helper

- Command: `bin/axiom-send-markdown-mail` (or the installed equivalent in your environment)
- It sends `multipart/alternative` mail:
  - plain text generated from the Markdown
  - HTML generated from the Markdown
- It expects `sendmail` and `pandoc` to be available in the local environment.

## Common usage

Send a new message from a Markdown file:

```bash
bin/axiom-send-markdown-mail \
  --to person@example.com \
  --subject "Subject here" \
  --markdown-file /tmp/body.md
```

Reply to an existing Maildir message and preserve threading automatically:

```bash
bin/axiom-send-markdown-mail \
  --reply-mail "$HOME/Maildir/new/<message-file>" \
  --expect-reply-message-id '<message-id-copied-when-reading>' \
  --markdown-file /tmp/body.md
```

Attach one or more files without losing either body alternative:

```bash
bin/axiom-send-markdown-mail \
  --reply-mail "$HOME/Maildir/new/<message-file>" \
  --expect-reply-message-id '<message-id-copied-when-reading>' \
  --markdown-file /tmp/body.md \
  --attach /tmp/form.pdf
```

In reply mode the helper derives:

- `To` from `Reply-To` or `From`
- `Subject` as `Re: ...` if needed
- `In-Reply-To` from the source `Message-ID`
- `References` from the source `References` plus `Message-ID`

## Workflow

1. Write the body in normal Markdown.
2. Prefer short paragraphs and simple bullet lists.
3. Use `--reply-mail` when responding to a message file you already have locally.
4. Retain that exact path from the read step; do not rediscover "the newest mail" immediately before sending.
5. Pass `--expect-reply-message-id` for an end-to-end guard against a new message becoming the reply parent.
6. Confirm the current process has the instance's `BOT_MAIL_FROM` and `BOT_ENVELOPE_FROM` values. If it does not, source the instance environment file or pass the identity explicitly; never use generic development defaults for a real send.
7. Use repeatable `--attach` arguments for attachments. Do not fall back to GNU `mail`; its MIME option ordering is easy to misuse and can silently drop the body or filename.
8. If you want to inspect the exact MIME before sending, add `--dry-run`.

## Notes

- The helper's sender defaults should come from its local configuration or environment.
- Override those defaults only when there is a concrete reason.
