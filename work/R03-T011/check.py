#!/usr/bin/env python3
"""Verify local branch deletion variants against a small, reproducible repo."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent
INPUTS = {
    "repository": {
        "initial_branch": "main",
        "author_name": "Course Student",
        "author_email": "student@example.invalid",
        "commits": [
            {"label": "A", "message": "A", "files": {"notes.txt": "alpha\n"}},
            {"label": "B", "message": "B", "append": {"notes.txt": "beta\n"}},
            {"label": "C", "message": "C", "files": {"todo.txt": "one\n"}},
        ],
        "topic_start": "B",
    },
    "deletion_commands": [
        ["branch", "-d", "topic"],
        ["branch", "--delete", "topic"],
        ["branch", "-D", "topic"],
        ["branch", "--delete", "--force", "topic"],
    ],
}

results = {
    "expected": {
        "author": ["Course Student", "student@example.invalid"],
        "commit_count": 3,
        "branch_head": "main at C",
        "topic_initially_points_to": "B",
        "deletion_variants": "Each command succeeds because topic is merged into main.",
        "after_each_deletion": {
            "topic_exists": False,
            "current_branch": "main",
            "main_head": "C",
            "notes_txt": "alpha\nbeta\n",
            "todo_txt": "one\n",
        },
    },
    "actual": {"commands": [], "checks": [], "commits": {}},
    "failure": None,
}

git_env = os.environ.copy()
git_env["GIT_CONFIG_NOSYSTEM"] = "1"
git_env["GIT_CONFIG_GLOBAL"] = os.devnull


def run_git(cwd, *args):
    """Run Git and record/check its return code, including expected operations."""
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=git_env,
        check=False,
        capture_output=True,
        text=True,
    )
    results["actual"]["commands"].append(
        {
            "command": ["git", *args],
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"Git command failed ({completed.returncode}): git {' '.join(args)}\n"
            f"{completed.stderr}"
        )
    return completed.stdout.strip()


def check(name, actual, expected):
    passed = actual == expected
    results["actual"]["checks"].append(
        {"name": name, "expected": expected, "actual": actual, "passed": passed}
    )
    assert passed, f"{name}: expected {expected!r}, got {actual!r}"


def branch_names(repo, branch):
    return run_git(repo, "branch", "--list", "--format=%(refname:short)", branch)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "inputs.json").write_text(
        json.dumps(INPUTS, indent=2) + "\n", encoding="utf-8"
    )
    git_version = subprocess.run(
        ["git", "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    (OUTPUT_DIR / "tool-versions.txt").write_text(
        f"Python: {sys.version.split()[0]}\n{git_version}\n", encoding="utf-8"
    )

    try:
        with tempfile.TemporaryDirectory(prefix="R03-T011-") as directory:
            repo = Path(directory) / "repo"
            run_git(None, "init", "--initial-branch=main", str(repo))
            run_git(repo, "config", "user.name", "Course Student")
            run_git(repo, "config", "user.email", "student@example.invalid")

            (repo / "notes.txt").write_text("alpha\n", encoding="utf-8")
            run_git(repo, "add", "notes.txt")
            run_git(repo, "commit", "-m", "A")
            commit_a = run_git(repo, "rev-parse", "HEAD")

            with (repo / "notes.txt").open("a", encoding="utf-8") as notes:
                notes.write("beta\n")
            run_git(repo, "add", "notes.txt")
            run_git(repo, "commit", "-m", "B")
            commit_b = run_git(repo, "rev-parse", "HEAD")

            (repo / "todo.txt").write_text("one\n", encoding="utf-8")
            run_git(repo, "add", "todo.txt")
            run_git(repo, "commit", "-m", "C")
            commit_c = run_git(repo, "rev-parse", "HEAD")
            results["actual"]["commits"] = {
                "A": commit_a,
                "B": commit_b,
                "C": commit_c,
            }

            run_git(repo, "branch", "topic", commit_b)
            authors = run_git(
                repo, "log", "--reverse", "--format=%an%x00%ae", "main"
            )
            expected_author = [
                INPUTS["repository"]["author_name"],
                INPUTS["repository"]["author_email"],
            ]
            check(
                "all commit authors",
                [line.split("\x00") for line in authors.splitlines()],
                [expected_author] * 3,
            )
            check(
                "three commits on main",
                run_git(repo, "rev-list", "--count", "main"),
                "3",
            )
            check("main points to C", run_git(repo, "rev-parse", "main"), commit_c)
            check(
                "topic initially points to B",
                run_git(repo, "rev-parse", "topic"),
                commit_b,
            )
            check(
                "A remains in main history",
                run_git(repo, "merge-base", "--is-ancestor", commit_a, "main"),
                "",
            )
            expected_after_deletion = {
                **results["expected"]["after_each_deletion"],
                "main_head": commit_c,
                "commit_count": "3",
            }
            results["expected"]["after_each_deletion"] = expected_after_deletion

            for index, command in enumerate(INPUTS["deletion_commands"], start=1):
                if index > 1:
                    run_git(repo, "branch", "topic", commit_b)
                output = run_git(repo, *command)
                actual_after = {
                    "topic_exists": bool(branch_names(repo, "topic")),
                    "current_branch": run_git(repo, "branch", "--show-current"),
                    "main_head": run_git(repo, "rev-parse", "main"),
                    "notes_txt": (repo / "notes.txt").read_text(encoding="utf-8"),
                    "todo_txt": (repo / "todo.txt").read_text(encoding="utf-8"),
                    "commit_count": run_git(repo, "rev-list", "--count", "main"),
                }
                check(
                    f"deletion variant {index}: {' '.join(command)}",
                    actual_after,
                    expected_after_deletion,
                )
                results["actual"].setdefault("deletions", []).append(
                    {
                        "command": ["git", *command],
                        "output": output,
                        "after": actual_after,
                    }
                )
    except Exception as error:
        results["failure"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        (OUTPUT_DIR / "results.json").write_text(
            json.dumps(results, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
