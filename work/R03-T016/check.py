#!/usr/bin/env python3
"""Compare the documented branch creation and checkout command sequences."""

import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "work" / "R03-T016"
TEMP_ROOT = None
results = {
    "expected": {
        "branch_then_checkout": {
            "after_branch_command": {"current_branch": "main", "new_branch_head": "C"},
            "after_checkout": {"current_branch": "my-new-branch", "new_branch_head": "C"},
        },
        "checkout_b": {
            "current_branch": "my-new-branch",
            "new_branch_head": "C",
            "main_head": "C",
        },
        "both_methods_create_branch_at_same_commit": True,
    },
    "actual": {"commands": [], "scenarios": [], "commits": {}},
    "failure": None,
}

GIT_ENV = os.environ.copy()
GIT_ENV["GIT_CONFIG_NOSYSTEM"] = "1"
GIT_ENV["GIT_CONFIG_GLOBAL"] = os.devnull


def sanitize(value):
    if TEMP_ROOT is not None:
        return value.replace(str(TEMP_ROOT.resolve()), "$TMP").replace(
            str(TEMP_ROOT), "$TMP"
        )
    return value


def git(repo, *args):
    command = ["git", *args]
    completed = subprocess.run(
        command, cwd=repo, env=GIT_ENV, check=False, capture_output=True, text=True
    )
    results["actual"]["commands"].append(
        {
            "command": command,
            "cwd": sanitize(str(repo)) if repo else None,
            "returncode": completed.returncode,
            "stdout": sanitize(completed.stdout.strip()),
            "stderr": sanitize(completed.stderr.strip()),
        }
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"Git command failed ({completed.returncode}): "
            f"git {' '.join(args)}\n{completed.stderr}"
        )
    return completed.stdout.strip()


def check(name, actual, expected):
    passed = actual == expected
    results["actual"].setdefault("checks", []).append(
        {"name": name, "expected": expected, "actual": actual, "passed": passed}
    )
    assert passed, f"{name}: expected {expected!r}, got {actual!r}"


def create_history(repo):
    repo.mkdir()
    git(None, "init", "--initial-branch=main", str(repo))
    git(repo, "config", "user.name", "Course Student")
    git(repo, "config", "user.email", "student@example.invalid")

    (repo / "notes.txt").write_text("alpha\n", encoding="utf-8")
    git(repo, "add", "notes.txt")
    git(repo, "commit", "-m", "A")
    commit_a = git(repo, "rev-parse", "HEAD")

    with (repo / "notes.txt").open("a", encoding="utf-8") as notes:
        notes.write("beta\n")
    git(repo, "add", "notes.txt")
    git(repo, "commit", "-m", "B")
    commit_b = git(repo, "rev-parse", "HEAD")

    (repo / "todo.txt").write_text("one\n", encoding="utf-8")
    git(repo, "add", "todo.txt")
    git(repo, "commit", "-m", "C")
    commit_c = git(repo, "rev-parse", "HEAD")
    git(repo, "branch", "topic", commit_b)

    check("commit A exists", git(repo, "cat-file", "-t", commit_a), "commit")
    check("main starts at C", git(repo, "rev-parse", "main"), commit_c)
    check("topic starts at B", git(repo, "rev-parse", "topic"), commit_b)
    results["actual"]["commits"] = {"A": commit_a, "B": commit_b, "C": commit_c}
    return commit_c


def test_branch_then_checkout(parent):
    repo = parent / "branch-then-checkout"
    commit_c = create_history(repo)

    git(repo, "branch", "my-new-branch")
    after_create = {
        "current_branch": git(repo, "branch", "--show-current"),
        "new_branch_head": git(repo, "rev-parse", "my-new-branch"),
    }
    check(
        "git branch creates without switching",
        after_create,
        {
            "current_branch": "main",
            "new_branch_head": commit_c,
        },
    )

    git(repo, "checkout", "my-new-branch")
    after_checkout = {
        "current_branch": git(repo, "branch", "--show-current"),
        "new_branch_head": git(repo, "rev-parse", "HEAD"),
    }
    check(
        "git checkout switches to the created branch",
        after_checkout,
        {
            "current_branch": "my-new-branch",
            "new_branch_head": commit_c,
        },
    )
    results["actual"]["scenarios"].append(
        {
            "name": "branch_then_checkout",
            "after_branch_command": after_create,
            "after_checkout": after_checkout,
        }
    )
    return commit_c, after_create, after_checkout


def test_checkout_b(parent):
    repo = parent / "checkout-b"
    commit_c = create_history(repo)

    git(repo, "checkout", "-b", "my-new-branch")
    actual = {
        "current_branch": git(repo, "branch", "--show-current"),
        "new_branch_head": git(repo, "rev-parse", "HEAD"),
        "main_head": git(repo, "rev-parse", "main"),
    }
    check(
        "git checkout -b creates and switches at current commit",
        actual,
        {
            "current_branch": "my-new-branch",
            "new_branch_head": commit_c,
            "main_head": commit_c,
        },
    )
    results["actual"]["scenarios"].append(
        {"name": "checkout_b", "state": actual}
    )
    return actual


def main():
    global TEMP_ROOT
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="R03-T016-") as directory:
            TEMP_ROOT = Path(directory)
            parent = TEMP_ROOT / "repos"
            parent.mkdir()
            commit_c, after_create, after_checkout = test_branch_then_checkout(parent)
            shortcut = test_checkout_b(parent)
            check(
                "both methods create the new branch at the same commit",
                after_checkout["new_branch_head"] == shortcut["new_branch_head"]
                == commit_c,
                True,
            )
    except Exception as error:
        results["failure"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "inputs.json").write_text(
            json.dumps(
                {
                    "repository": {
                        "initial_branch": "main",
                        "author_name": "Course Student",
                        "author_email": "student@example.invalid",
                        "commits": [
                            {"label": "A", "file": "notes.txt", "content": "alpha\n"},
                            {"label": "B", "append": "notes.txt", "content": "beta\n"},
                            {"label": "C", "file": "todo.txt", "content": "one\n"},
                        ],
                        "topic_branch_at": "B",
                    },
                    "operations_under_test": [
                        ["git", "branch", "my-new-branch"],
                        ["git", "checkout", "my-new-branch"],
                        ["git", "checkout", "-b", "my-new-branch"],
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        git_version = subprocess.run(
            ["git", "--version"], check=True, capture_output=True, text=True
        ).stdout.strip()
        (OUTPUT_DIR / "tool-versions.txt").write_text(
            f"Python: {platform.python_version()}\n{git_version}\n",
            encoding="utf-8",
        )
        (OUTPUT_DIR / "results.json").write_text(
            json.dumps(results, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
