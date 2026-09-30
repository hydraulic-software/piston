# Piston development

Piston is the reusable employee automation project. Preserve account isolation
and never embed credentials or employee-specific live state in this repository.
Run `scripts/check.sh` before committing. Own Piston changes may be integrated
on master, pushed and deployed with `scripts/update-local.sh --systemd`.

Recurring monthly work is implemented by `piston-todo schedule`, `schedules`,
and `tick`; completion advances its schedule. The autonomy scheduler ticks
before workload counting. Future schedules and occurrences are visible in the
HTML monitor. Scheduling never authorizes automatic external actions.

Both install and managed upgrade refresh the bounded Piston guidance block in
the employee's home AGENTS.md via `piston-update-agent-instructions`. Preserve
all text outside the markers; do not overwrite employee policies.
