#!/usr/bin/env python3
"""Check three named API catalogue entries in README.md, with offline fixtures."""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
OUTPUT_DIR = ROOT / "work" / "R02-T014"
FIXTURE_DIR = ROOT / "tools" / "course_checks" / "fixtures" / "r02-t014"
TARGETS = {
    "Agent Verifier": "https://packet.guru/agents/reference",
    "Application Environment Verification": "https://github.com/fingerprintjs/aev",
    "BinaryEdge": "https://docs.binaryedge.io/api-v2.html",
}
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CATALOGUE_HEADING = re.compile(r"^(#{1,6})\s+.*(?:api|catalog(?:ue)?).*", re.IGNORECASE)


def section_lines(text: str) -> tuple[list[tuple[int, str]], str]:
    """Return the matching API/catalogue heading section, or the whole file."""
    lines = text.splitlines()
    heading_index = None
    heading_level = None
    for index, line in enumerate(lines):
        match = CATALOGUE_HEADING.match(line)
        if match:
            heading_index = index
            heading_level = len(match.group(1))
            break
    if heading_index is None:
        return (
            list(enumerate(lines, start=1)),
            "README.md (whole file; no API catalogue heading)",
        )

    end_index = len(lines)
    for index in range(heading_index + 1, len(lines)):
        match = re.match(r"^(#{1,6})\s+", lines[index])
        if match and len(match.group(1)) <= heading_level:
            end_index = index
            break
    return (
        [(index + 1, lines[index]) for index in range(heading_index, end_index)],
        f"README.md lines {heading_index + 1}-{end_index}",
    )


def inspect_entries(lines: list[tuple[int, str]]) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for name in TARGETS:
        entry_prefix = re.compile(rf"^\s*(?:[-*]\s*)?{re.escape(name)}\s*:")
        occurrences = []
        for line_number, line in lines:
            if not entry_prefix.match(line):
                continue
            link = LINK_PATTERN.search(line)
            occurrences.append(
                {
                    "line_number": line_number,
                    "source": line.strip(),
                    "link_text": link.group(1) if link else None,
                    "url": link.group(2) if link else None,
                }
            )
        entries[name] = {"expected_url": TARGETS[name], "occurrences": occurrences}
    return entries


def validate_entries(entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks = []
    for name, expected_url in TARGETS.items():
        occurrences = entries[name]["occurrences"]
        if not occurrences:
            checks.append(
                {
                    "name": name,
                    "line_number": None,
                    "expected_url": expected_url,
                    "actual_url": None,
                    "status": "missing",
                }
            )
            continue
        if len(occurrences) > 1:
            checks.append(
                {
                    "name": name,
                    "line_number": [entry["line_number"] for entry in occurrences],
                    "expected_url": expected_url,
                    "actual_url": [entry["url"] for entry in occurrences],
                    "status": "duplicate",
                }
            )
            continue
        entry = occurrences[0]
        if entry["url"] is None:
            status = "malformed_link"
        elif entry["url"] != expected_url:
            status = "incorrect_url"
        else:
            status = "ok"
        checks.append(
            {
                "name": name,
                "line_number": entry["line_number"],
                "expected_url": expected_url,
                "actual_url": entry["url"],
                "status": status,
            }
        )
    return {
        "passed": all(check["status"] == "ok" for check in checks),
        "checks": checks,
    }


def run_self_tests() -> list[dict[str, Any]]:
    cases = [
        {
            "name": "valid fixture",
            "file": "valid.md",
            "expected_passed": True,
            "expected_statuses": ["ok", "ok", "ok"],
            "expected_lines": [3, 4, 5],
        },
        {
            "name": "invalid fixture",
            "file": "invalid.md",
            "expected_passed": False,
            "expected_statuses": ["incorrect_url", "missing", "ok"],
            "expected_lines": [3, None, 4],
        },
    ]
    results = []
    for case in cases:
        text = (FIXTURE_DIR / case["file"]).read_text(encoding="utf-8")
        lines, scope = section_lines(text)
        entries = inspect_entries(lines)
        actual = validate_entries(entries)
        actual_statuses = [item["status"] for item in actual["checks"]]
        actual_lines = [item["line_number"] for item in actual["checks"]]
        assert actual["passed"] is case["expected_passed"], case["name"]
        assert actual_statuses == case["expected_statuses"], (
            case["name"],
            actual_statuses,
        )
        assert actual_lines == case["expected_lines"], (case["name"], actual_lines)
        results.append(
            {
                "name": case["name"],
                "fixture": case["file"],
                "expected": {
                    "passed": case["expected_passed"],
                    "statuses": case["expected_statuses"],
                    "line_numbers": case["expected_lines"],
                },
                "actual": {
                    "passed": actual["passed"],
                    "statuses": actual_statuses,
                    "line_numbers": actual_lines,
                    "scope": scope,
                },
                "passed": True,
            }
        )
    return results


def write_evidence(self_tests: list[dict[str, Any]]) -> dict[str, Any]:
    source_text = README.read_text(encoding="utf-8")
    source_lines, scope = section_lines(source_text)
    source_entries = inspect_entries(source_lines)
    catalogue_result = validate_entries(source_entries)
    scoped_target_lines = [
        {"line_number": number, "text": line}
        for number, line in source_lines
        if any(name in line for name in TARGETS)
    ]
    inputs = {
        "source_file": "README.md",
        "scope": scope,
        "target_entries": TARGETS,
        "source_target_lines": scoped_target_lines,
        "fixtures": [
            "tools/course_checks/fixtures/r02-t014/valid.md",
            "tools/course_checks/fixtures/r02-t014/invalid.md",
        ],
    }
    results = {
        "expected": {
            "self_test": "valid fixture passes; invalid fixture is identified with exact line numbers",
            "catalogue": {
                "entries": [
                    {"name": name, "url": url, "status": "ok"}
                    for name, url in TARGETS.items()
                ],
                "normal_mode_exit_code": 0,
            },
        },
        "actual": {
            "self_test": self_tests,
            "catalogue": {
                "passed": catalogue_result["passed"],
                "scope": scope,
                "entries": source_entries,
                "checks": catalogue_result["checks"],
                "normal_mode_exit_code": 0 if catalogue_result["passed"] else 1,
            },
        },
        "failure": None,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "inputs.json").write_text(
        json.dumps(inputs, indent=2) + "\n", encoding="utf-8"
    )
    (OUTPUT_DIR / "results.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    git_version = subprocess.run(
        ["git", "--version"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    (OUTPUT_DIR / "tool-versions.txt").write_text(
        f"Python: {platform.python_version()}\n{git_version}\n", encoding="utf-8"
    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run offline parser fixtures and save the README audit report",
    )
    args = parser.parse_args()
    try:
        self_tests = run_self_tests() if args.self_test else []
        write_evidence(self_tests)
    except Exception as error:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        failure_results = {
            "expected": "offline fixtures satisfy their asserted parser results",
            "actual": None,
            "failure": f"{type(error).__name__}: {error}",
        }
        (OUTPUT_DIR / "results.json").write_text(
            json.dumps(failure_results, indent=2) + "\n", encoding="utf-8"
        )
        raise
    report = json.loads((OUTPUT_DIR / "results.json").read_text(encoding="utf-8"))
    catalogue = report["actual"]["catalogue"]
    missing = sum(item["status"] == "missing" for item in catalogue["checks"])
    if args.self_test:
        print(f"Self-test passed ({len(self_tests)} offline fixtures).")
    print(
        "README catalogue audit: "
        f"{'passed' if catalogue['passed'] else 'needs review'} "
        f"({missing} missing target entries; scope: {catalogue['scope']})."
    )
    return 0 if args.self_test or catalogue["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
