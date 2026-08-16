# jenkins-log-analyzer

A CLI tool that triages a directory of Jenkins console logs: it extracts each
build's status, failing stage, and a concise failure reason, clusters
failures by likely root cause, and prints a Markdown (or JSON) report.

No third-party dependencies -- Python 3.9+ standard library only.

## Usage

```bash
# Default: reads ./logs, prints a Markdown report to stdout
python triage.py

# Explicit directory (positional or --dir)
python triage.py --dir ./logs
python triage.py ./logs

# Write JSON instead of Markdown
python triage.py --dir ./logs --format json -o report.json

# Show per-file parse warnings on stderr
python triage.py --dir ./logs -v
```

Run `python triage.py --help` for all options.
