#!/usr/bin/env python3
"""R03-T048: Runs and judges the undoing-a-commit guide test.

Run from repository root:  python3 work/R03-T048/check.py

The guide test itself lives in tests/guides/test_undoing_a_commit.py.
This script runs it as a child process:
    1. as it is                     -> must pass (exit 0)
    2. GUIDE_TEST_OMIT=reset        -> must fail (exit 1)
and checks that no temporary directory is left behind.
"""

import glob
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TEST = ROOT / "tests" / "guides" / "test_undoing_a_commit.py"
TMP_PREFIX = "undoing-guide-test-"

COMMANDS = []
RESULTS = []


def expect(label, expected, actual):
    ok = expected == actual
    RESULTS.append({"check": label, "expected": expected, "actual": actual, "ok": ok})
    if not ok:
        raise AssertionError("%s: expected %r, got %r" % (label, expected, actual))


def run_guide_test(omit=""):
    env = {k: v for k, v in os.environ.items() if k != "GUIDE_TEST_OMIT"}
    if omit:
        env["GUIDE_TEST_OMIT"] = omit
    p = subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), env=env,
                       capture_output=True, text=True)
    label = ("GUIDE_TEST_OMIT=%s " % omit if omit else "") + "python3 tests/guides/test_undoing_a_commit.py"
    COMMANDS.append({"cmd": label, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr})
    return p


def outcomes(stderr):
    result = {}
    for line in stderr.splitlines():
        if line.startswith("test_") and " ... " in line:
            result[line.split(" ")[0]] = line.rsplit(" ... ", 1)[1].strip()
    return result


def leftovers():
    return set(glob.glob(os.path.join(tempfile.gettempdir(), TMP_PREFIX + "*")))


def run_checks():
    expect("the guide test file is present", True, TEST.is_file())
    before = leftovers()

    # Run 1: normal test execution
    p = run_guide_test()
    expect("as it is: guide test exits 0", 0, p.returncode)
    test_results = outcomes(p.stderr)
    expect("all four tests are ok", True, all(status == "ok" for status in test_results.values()) and len(test_results) == 4)

    # Run 2: omitting the decisive reset command
    p_omit = run_guide_test(omit="reset")
    expect("reset omitted: guide test fails (exit 1)", 1, p_omit.returncode)
    omit_results = outcomes(p_omit.stderr)
    expect("sequence test FAILs when reset omitted", "FAIL",
           omit_results.get("test_guide_sequence_undoes_commit_and_unstages_file"))

    # Cleanup check: no temporary directories left behind
    expect("no temporary directory is left behind", [], sorted(leftovers() - before))


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T048",
        "guide": "docs/additional-material/git_workflow_scenarios/undoing-a-commit.md",
        "guide_test": "tests/guides/test_undoing_a_commit.py",
        "author": "Course Student <student@example.invalid>",
        "commands": ["git reset <file>", "git reset --hard HEAD~1"],
        "runs": ["unchanged (exit 0)", "GUIDE_TEST_OMIT=reset (exit 1)"]
    }
    (HERE / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")

    rows = ["| check | expected | actual | ok |", "|---|---|---|---|"]
    for r in RESULTS:
        rows.append("| %s | `%s` | `%s` | %s |" % (
            r["check"], json.dumps(r["expected"]), json.dumps(r["actual"]), "yes" if r["ok"] else "NO"))
    (HERE / "expected_vs_actual.md").write_text("\n".join(rows) + "\n")

    log = []
    for c in COMMANDS:
        log.append("$ %s\n[exit %d]\n%s%s" % (c["cmd"], c["returncode"], c["stdout"], c["stderr"]))
    (HERE / "commands.log").write_text("\n".join(log))


def main():
    try:
        run_checks()
    finally:
        write_evidence()

    print(f"OK: All {len(RESULTS)} checks passed.")


if __name__ == "__main__":
    main()
