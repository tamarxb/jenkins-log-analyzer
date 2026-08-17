import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional
import re

# --- Regex patterns -------------------------------------------------------

# Jenkins optionally prefixes lines with an "HH:MM:SS  " timestamp.
TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\s+")

# Declarative pipeline stage markers look like: [Pipeline] { (Stage Name)
STAGE_RE = re.compile(r"\[Pipeline\]\s*\{\s*\(([^)]+)\)")

# The final result line Jenkins writes, e.g. "Finished: FAILURE"
STATUS_RE = re.compile(r"Finished:\s*(SUCCESS|FAILURE|ABORTED|UNSTABLE)", re.IGNORECASE)

# A line that looks like a genuine error/exception.
ERROR_RE = re.compile(r"ERROR[: ]|FAILED\b|Exception\b|fatal:|AssertionError|Traceback", re.IGNORECASE)

# Lines that match ERROR_RE but are just Jenkins boilerplate or transient
# retry warnings, not the actual root cause -- skip these as candidates.
NOISE_RE = re.compile(r"^(ERROR: script returned exit code|Finished:|\[Pipeline\]|WARNING:)", re.IGNORECASE)

# Root-cause keyword rules, checked in order -- most specific first.
CATEGORY_RULES = [
    ("Out of Memory (OOM)", r"OOMKilled|OutOfMemoryError|out of memory"),
    ("Dependency/Package Error", r"ResolutionImpossible|conflicting dependencies|ModuleNotFoundError|npm ERR!"),
    ("Git/SCM Checkout Failure", r"GitException|fatal:.*git|repository not found"),
    ("Network/Connection Issue", r"Connection refused|Connection reset|SSL_ERROR_SYSCALL|Could not resolve host"),
    ("Timeout", r"timed out|TimeoutException"),
    ("Test Failure", r"FAILED\b.*::|AssertionError|\d+ failed,"),
    ("Compilation Error", r"compilation error|SyntaxError|cannot find symbol"),
]
CATEGORY_RULES = [(name, re.compile(pattern, re.IGNORECASE)) for name, pattern in CATEGORY_RULES]


@dataclass
class BuildResult:
    name: str
    status: str = "UNKNOWN"
    stage: Optional[str] = None
    reason: Optional[str] = None
    category: Optional[str] = None


def categorize(reason: str) -> str:
    """Map a failure reason to a root-cause category via keyword rules."""
    for category, pattern in CATEGORY_RULES:
        if pattern.search(reason):
            return category
    return "Uncategorized"


def parse_log(path: Path) -> BuildResult:
    """Parse a single Jenkins console log. Never raises -- logs are messy."""
    result = BuildResult(name=path.stem)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        result.reason = f"Could not read file: {exc}"
        return result

    current_stage = None
    for raw_line in text.splitlines():
        line = TIMESTAMP_RE.sub("", raw_line).strip() # remove timestamp & unnecessary tabs

        status_match = STATUS_RE.search(line)
        if status_match:
            result.status = status_match.group(1).upper()

        stage_match = STAGE_RE.search(line)
        if stage_match:
            current_stage = stage_match.group(1).strip()

        if result.reason is None and not NOISE_RE.match(line) and ERROR_RE.search(line):
            result.reason = line[:200]
            result.stage = current_stage

    if result.status == "SUCCESS":
        return result

    if result.reason is None:
        result.reason = "No specific error found (build did not report SUCCESS)."
        result.stage = current_stage

    # Categorize using the whole log, not just the one-line reason: the
    # clearest keyword (e.g. "GitException") may sit a few lines away from
    # the line we picked as the headline reason.
    result.category = categorize(text)
    return result


def cluster_failures(results: list[BuildResult]) -> dict[str, list[BuildResult]]:
    """Group non-SUCCESS builds by root-cause category."""
    clusters: dict[str, list[BuildResult]] = defaultdict(list)
    for result in results:
        if result.status != "SUCCESS":
            clusters[result.category].append(result)
    return clusters


def render_markdown(results: list[BuildResult], logs_dir: Path) -> str:
    lines = [
        "# Jenkins Build Triage Report",
        "",
        f"- Logs directory: `{logs_dir}`",
        f"- Builds analyzed: {len(results)}",
        "",
        "## Status Summary",
        "",
    ]
    for status, count in Counter(result.status for result in results).most_common():
        lines.append(f"- **{status}**: {count}")

    lines += ["", "## Root Cause Clusters", ""]
    clusters = cluster_failures(results)
    if not clusters:
        lines.append("No failures found.")
    for category, group in sorted(clusters.items(), key=lambda item: -len(item[1])):
        lines.append(f"### {category} ({len(group)} build{'s' if len(group) != 1 else ''})")
        for result in group:
            lines.append(f"- **{result.name}** [{result.stage or 'unknown stage'}]: {result.reason}")
        lines.append("")

    lines += [
        "## Per-Build Details",
        "",
        "| Build | Status | Stage | Reason |",
        "|---|---|---|---|",
    ]
    for result in results:
        reason = (result.reason or "").replace("|", "/")
        lines.append(f"| {result.name} | {result.status} | {result.stage or ''} | {reason} |")

    return "\n".join(lines)


def render_text(results: list[BuildResult], logs_dir: Path) -> str:
    lines = [
        "JENKINS BUILD TRIAGE REPORT",
        f"Logs directory: {logs_dir}",
        f"Builds analyzed: {len(results)}",
        "",
        "STATUS SUMMARY",
    ]
    for status, count in Counter(result.status for result in results).most_common():
        lines.append(f"  {status}: {count}")

    lines += ["", "ROOT CAUSE CLUSTERS"]
    clusters = cluster_failures(results)
    if not clusters:
        lines.append("  No failures found.")
    for category, group in sorted(clusters.items(), key=lambda item: -len(item[1])):
        lines.append(f"  {category} ({len(group)} build{'s' if len(group) != 1 else ''})")
        for result in group:
            lines.append(f"    - {result.name} [{result.stage or 'unknown stage'}]: {result.reason}")

    lines += ["", "PER-BUILD DETAILS"]
    for result in results:
        lines.append(f"  {result.name} | {result.status} | {result.stage or ''} | {result.reason or ''}")

    return "\n".join(lines)


def render_json(results: list[BuildResult], logs_dir: Path) -> str:
    clusters = cluster_failures(results)
    payload = {
        "logs_directory": str(logs_dir),
        "builds_analyzed": len(results),
        "status_summary": dict(Counter(result.status for result in results)),
        "root_cause_clusters": {
            category: [asdict(result) for result in group]
            for category, group in sorted(clusters.items(), key=lambda item: -len(item[1]))
        },
        "builds": [asdict(result) for result in results],
    }
    return json.dumps(payload, indent=2)


RENDERERS = {"md": render_markdown, "text": render_text, "json": render_json}


def render_report(results: list[BuildResult], logs_dir: Path, fmt: str = "md") -> str:
    return RENDERERS[fmt](results, logs_dir)


def main() -> None:
    # Make stdout tolerant of odd Unicode in log content
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Triage Jenkins console logs.")
    parser.add_argument("dir", nargs="?", default=None, help="Path to logs directory (positional)")
    parser.add_argument("--dir", dest="dir_opt", default=None, help="Path to logs directory (flag form)")
    parser.add_argument("-o", "--output", default=None,
        help="Write the report to this file instead of stdout")
    parser.add_argument("-f", "--format", choices=["md", "text", "json"], default="md",
        help="Report output format: md (default), text, or json")
    args = parser.parse_args()

    logs_dir = Path(args.dir_opt or args.dir or "./logs")
    if not logs_dir.is_dir():
        raise SystemExit(f"error: directory not found: {logs_dir}")

    results = [parse_log(path) for path in sorted(logs_dir.glob("*.log"))]
    report = render_report(results, logs_dir, args.format)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
