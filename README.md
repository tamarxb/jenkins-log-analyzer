# Jenkins Log Triage

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![Stdlib Only](https://img.shields.io/badge/stdlib-only-informational)

A CLI tool that triages a directory of Jenkins console logs. It parses each
build's outcome, failing stage, and one-line failure reason, clusters
failures by likely root cause, and emits a report in Markdown, plain text,
or JSON — with optional Slack alerting.

## Overview

Jenkins log directories accumulate fast, and eyeballing every console log
after a batch of failures doesn't scale. This tool scans a directory of
`*.log` files, extracts a structured `BuildResult` per build (status, stage,
reason, category), and groups failures by root cause so you can see at a
glance whether five failures are five different problems or one flaky
dependency taking down the whole pipeline.

**Architectural approach:** a single file, zero external dependencies —
pure Python 3.11+ standard library (`argparse`, `re`, `json`,
`urllib.request`, `dataclasses`, `pathlib`). No `pip install` step, no
virtualenv required to run it; copy `triage.py` anywhere Python 3.11 exists.

## Features

- **Automated error detection & classification** — an ordered set of regex
  rules pattern-matches each log against known root-cause signatures.
- **Multiple output formats** — Markdown, plain text, or JSON via
  `-f`/`--format`.
- **File export** — write the report straight to disk with `-o`/`--output`
  instead of stdout.
- **Slack alerts** — a compact Block Kit summary posted to an incoming
  webhook via `--slack-webhook`, capped in size so it never spams a channel.
- **Developer tooling** — `Makefile`
- **Crash-proof parsing** — malformed, empty, or binary log files degrade to
  an `UNKNOWN` result instead of raising.

## How to Run

### CLI

```bash
# Default: reads ./logs, prints a Markdown report to stdout
python triage.py ./logs

# Directory via flag instead of positional argument
python triage.py --dir ./logs

# Plain-text or JSON output
python triage.py ./logs -f text
python triage.py ./logs -f json

# Export the report to a file instead of stdout
python triage.py ./logs -f json -o report.json

# Send a compact failure summary to Slack
python triage.py ./logs --slack-webhook "$SLACK_WEBHOOK_URL"
```

Run `python triage.py --help` for the full flag reference.

### Makefile

```bash
make help          # list all available targets
make run           # python triage.py ./logs (Markdown)
make json          # python triage.py ./logs -f json
make slack         # post the summary to Slack (needs SLACK_WEBHOOK_URL)
```

The image is built from `python:3.11-alpine` and copies in only
`triage.py` — no dependency layer needed.
`./logs` directory into the container at runtime.

## Classification Taxonomy & Assumptions

**Assumptions about log structure:**

- Lines may be prefixed with a Jenkins timestamp (`HH:MM:SS  `), which is
  stripped before pattern matching.
- Declarative pipeline stages are marked with the standard
  `[Pipeline] { (Stage Name)` / `[Pipeline] }` notation; the tool tracks
  which stage was active when the failing line was emitted.
- A terminal `Finished: SUCCESS|FAILURE|ABORTED|UNSTABLE` line reports the
  build's final status. Its absence (e.g. a truncated log) is treated as
  `UNKNOWN` rather than a hard failure.
- The failure reason is the **first** non-boilerplate line matching an
  error signature (`ERROR:`, `FAILED`, `Exception`, `fatal:`,
  `AssertionError`, `Traceback`), since the first genuine error is
  typically the root cause — later lines tend to be generic
  wrapper/exit-code noise.

**Root-cause categories**, checked in order (most specific first):

| Category | Example signal |
|---|---|
| Out of Memory (OOM) | `OOMKilled`, `OutOfMemoryError` |
| Dependency/Package Error | `ResolutionImpossible`, `ModuleNotFoundError`, `npm ERR!` |
| Git/SCM Checkout Failure | `GitException`, `fatal: ... git`, repository not found |
| Network/Connection Issue | `Connection refused/reset`, `SSL_ERROR_SYSCALL` |
| Timeout | `timed out`, `TimeoutException` |
| Test Failure | `FAILED <test>::...`, `AssertionError`, `N failed,` |
| Compilation Error | `SyntaxError`, `cannot find symbol` |
| Uncategorized | No rule matched — the reason is still surfaced, just unclustered |

## Known Limitations

- **Memory footprint** — each log file is read fully into memory
  (`Path.read_text`) rather than streamed. Fine for typical console logs;
  could matter on a directory of very large (multi-GB) build logs.
- **Uncategorized fallback** — novel or unusual error formats that don't
  match any regex rule land in an `Uncategorized` bucket rather than a
  specific root cause. The keyword rules are meant to be extended as new
  failure signatures are observed.
- **Heuristic reason selection** — picking the *first* non-boilerplate
  error line is a heuristic, not a guarantee. It works well for the
  Jenkins pipeline logs this tool was built against, but an unusual log
  layout could surface a less relevant line as the headline reason.
