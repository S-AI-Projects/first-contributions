#!/usr/bin/env python3
"""R03-T056: runs and judges the gitflow guide test.

Run from the repository root:  python3 work/R03-T056/check.py

The guide test itself lives in tests/guides/test_gitflow_develop_branch.py (it is part of
the pull request).  This script runs it as a child process, three times:

    1. as it is                           -> must pass (exit 0, all 5 tests ok)
    2. GUIDE_TEST_OMIT=push               -> `git push -u origin develop` is left out of the
                                             guide's sequence; the test must FAIL (exit 1)
    3. GUIDE_TEST_OMIT=branch             -> `git branch develop` is left out; the child git
                                             failure must reach the test as an ERROR (exit 1)

and then checks that the test left no temporary directory behind.  Every assertion goes
through expect(), which records expected-vs-actual and raises AssertionError (non-zero
exit) on mismatch, so a failing child always makes this script fail.  Evidence files are
written next to this script even when a check fails.

Needs: git >= 2.28 and Python 3.8+.
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
ROOT = HERE.parents[1]  # work/R03-T056/check.py -> repository root
TEST = ROOT / "tests" / "guides" / "test_gitflow_develop_branch.py"
TMP_PREFIX = "gitflow-guide-test-"
MAIN_TEST = "test_guide_sequence_publishes_develop_from_main"
ALL_TESTS = [
    "test_develop_starts_from_the_checked_out_branch",
    MAIN_TEST,
    "test_omitting_the_branch_command_propagates_the_git_failure",
    "test_omitting_the_push_makes_the_check_fail",
    "test_temporary_directory_is_removed_even_after_a_failure",
]

COMMANDS = []  # every child process -> commands.log
RESULTS = []   # expected-vs-actual rows -> expected_vs_actual.md


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
    label = ("GUIDE_TEST_OMIT=%s " % omit if omit else "") + "python3 tests/guides/test_gitflow_develop_branch.py"
    COMMANDS.append({"cmd": label, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr})
    return p


def outcomes(stderr):
    """Map test name -> ok / FAIL / ERROR from unittest's verbose output."""
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

    p = run_guide_test()
    expect("as it is: the guide test exits 0", 0, p.returncode)
    expect("as it is: all five tests are ok", {t: "ok" for t in ALL_TESTS}, outcomes(p.stderr))

    p = run_guide_test(omit="push")
    expect("push omitted: the guide test fails (exit 1)", 1, p.returncode)
    expect("push omitted: the sequence test FAILs, the others still pass",
           {**{t: "ok" for t in ALL_TESTS}, MAIN_TEST: "FAIL"}, outcomes(p.stderr))

    p = run_guide_test(omit="branch")
    expect("branch omitted: the guide test fails (exit 1)", 1, p.returncode)
    expect("branch omitted: the sequence test ends in ERROR, the others still pass",
           {**{t: "ok" for t in ALL_TESTS}, MAIN_TEST: "ERROR"}, outcomes(p.stderr))
    expect("branch omitted: the failing git push is reported by the test", True,
           "ChildFailure" in p.stderr and "git push -u origin develop" in p.stderr)

    expect("no temporary directory is left behind by any of the three runs", [],
           sorted(leftovers() - before))


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T056",
        "guide": "docs/additional-material/git_workflow_scenarios/gitflow.md",
        "guide_test": "tests/guides/test_gitflow_develop_branch.py",
        "guide_commands": ["git branch develop", "git push -u origin develop"],
        "not_run": "git flow init (needs the separate git-flow extension)",
        "author": "Course Student <student@example.invalid>",
        "commits": {"A": "create notes.txt 'alpha\\n'", "B": "append 'beta\\n' to notes.txt",
                    "C": "add todo.txt 'one\\n'"},
        "branches": {"main": "A-B-C", "topic": "at B"},
        "remote": "second local bare repository, file:// URL, created by the guide test",
        "runs": ["unchanged", "GUIDE_TEST_OMIT=push", "GUIDE_TEST_OMIT=branch"],
    }
    (HERE / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")

    rows = ["| check | expected | actual | ok |", "|---|---|---|---|"]
    for r in RESULTS:
        rows.append("| %s | `%s` | `%s` | %s |" % (
            r["check"], json.dumps(r["expected"]), json.dumps(r["actual"]), "yes" if r["ok"] else "NO"))
    (HERE / "expected_vs_actual.md").write_text("\n".join(rows) + "\n")

    log = []
    for c in COMMANDS:
        log.append("$ %s\n[exit %d]\n--- stdout ---\n%s--- stderr ---\n%s" % (
            c["cmd"], c["returncode"], c["stdout"], c["stderr"]))
    (HERE / "commands.log").write_text("\n".join(log))


def main():
    try:
        run_checks()
    finally:
        write_evidence()
    print("OK: %d checks passed" % len(RESULTS))


if __name__ == "__main__":
    main()
