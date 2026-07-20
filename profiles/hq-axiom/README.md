# HQ Axiom Profile Notes

This directory is reserved for host/account-specific overlays that should not be the default shared behavior.

Examples that still belong on the HQ side instead of in the shared core:

- mail filter policy
- account-specific sender defaults
- credentials and service environment values
- web server and MTA configuration

The current shared repo now includes one concrete example profile file here:

- `mail-filter-domains.txt`

That keeps the default shared mail filter permissive unless configured, while still making the HQ allowlist explicit and reusable as profile state rather than script-local code.
