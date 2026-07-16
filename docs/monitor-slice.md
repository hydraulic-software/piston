# Monitor Slice

This repo now includes the reusable monitor layer that was originally developed on HQ:

- `bin/axiom-render-codex-monitor`
- `bin/axiom-watch-codex-monitor`
- `systemd/user/axiom-codex-monitor.service`

## What it does

- reads Codex rollout/thread data from the local Codex SQLite/session state
- reads run logs and structured summary sidecars from the local `runs` directory
- reads the rolling todo board
- publishes day-by-day HTML and JSON monitor pages into an output directory
- watches the relevant state paths and re-renders on changes

## Important knobs

- `BOT_CODEX_STATE_DB`
  - override the Codex SQLite state path
- `BOT_MONITOR_OUTPUT_DIR`
  - override the published HTML/JSON output directory
- `BOT_MONITOR_AVATAR`
  - override the optional favicon/avatar source image
- `BOT_MONITOR_FAVICON_NAME`
  - override the favicon filename written into the output directory
- `BOT_TODO_FILE`
  - override the todo board path
- `BOT_RUN_LOG_DIR`
  - override the run-log directory used for summary sidecars
- `BOT_MONITOR_MIN_INTERVAL_SECONDS`
  - minimum seconds between renders while files are changing; defaults to `30`

The shared runner now writes those sidecars as:

- `~/.local/state/axiom/runs/<timestamp>-<mode>.summary.json`

That gives the monitor a structured `headline` source instead of relying only on rollout heuristics.

The watcher relies on those same defaults and watches the matching paths under `$HOME` unless you override them.

## Included, but still opinionated

The shared slice keeps the existing Axiom-oriented UI structure for now:

- day index plus per-day pages
- timeline view
- rolling todo list
- grouped tool output

That is useful enough to share as-is, even though it is not yet a polished generic theming/configuration layer.

The watcher drains filesystem events until this interval expires. This bounds
CPU use during active Codex sessions while still publishing a final render
after activity stops.

## Not included yet

- a more formal packaging/bootstrap story for the published HTML directory itself
- a configurable theme system
- a repo-agnostic abstraction over Codex thread semantics
