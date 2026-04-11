# Portable Helper Slice

This repo started as the Phase 1 extraction candidate from the earlier reusable-tooling review.

## Why these files first

They are small, already useful, and now parameterized enough to stop depending on hard-coded Axiom HQ values:

- Markdown mail helper
- TeamCity watcher
- simple rolling todo helper
- the matching markdown-email skill

## Why not the rest yet

The following were originally out of scope for the first slice because they were too tied to this host/account:

- monitor renderer/watcher
- nightly summary helper
- most operational notes and wiki content

Since then the shared repo has widened one step and now includes a Linux automation layer too:

- a portable `axiom-codex-runner`
- a workload-sensitive `axiom-autonomy-scheduler`
- a configurable `axiom-mail-filter`
- example `systemd --user` units for timer, nightly, and Maildir-triggered wakeups

The remaining boundary is now mostly around the monitor stack, local profile state, and HQ-specific policy, not around Maildir or `systemd` themselves.

## What a future cleanup would likely do

- rename the helpers away from the `axiom-` prefix
- decide whether the current tiny install/bootstrap script is enough or should become a more polished setup path
- make the skill refer to the final helper name/path
- decide whether `axiom-todo` should stay as a tiny JSON board or give way to a repo-local tracker later
