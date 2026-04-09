# Portable Helper Slice

This staging repo is the Phase 1 extraction candidate from the earlier reusable-tooling review.

## Why these files first

They are small, already useful, and now parameterized enough to stop depending on hard-coded Axiom HQ values:

- Markdown mail helper
- TeamCity watcher
- simple rolling todo helper
- the matching markdown-email skill

## Why not the rest yet

The following remain out of scope for this first slice because they are still too tied to this host/account:

- Codex runner
- monitor renderer/watcher
- mail filter
- nightly summary helper
- most operational notes and wiki content

## What a future cleanup would likely do

- rename the helpers away from the `axiom-` prefix
- add a tiny install/bootstrap script
- make the skill refer to the final helper name/path
- decide whether `axiom-todo` should stay as a tiny JSON board or give way to a repo-local tracker later
