#!/usr/bin/env python3
"""Verify moving the latest commit's changes to an existing branch."""

import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "work" / "R03-T017"
TEMP_ROOT = None
GIT_ENV = os.environ.copy()
GIT_ENV["GIT_CONFIG_NOSYSTEM"] = "1"
GIT_ENV["GIT_CONFIG_GLOBAL"] = os.devnull

results = {
    "expected": {
        "after_soft_reset": {
            "main": "B",
            "current_branch": "main",
            "staged_paths": ["todo.txt"],
            "todo_txt": "one\n",
        },
        "after_stash": {
            "main": "B",
            "status": "",
            "stash_count": 1,
        },
        "after_stash_pop_and_commit": {
            "main": "B",
            "topic_parent": "B",
            "current_branch": "topic",
            "topic_commit_count": "3",
            "status": "",
            "notes_txt": "alpha\nbeta\n",
            "todo_txt": "one\n",
            "stash_count": 0,
        },
    },
    "actual": {"commands": [], "checks": [], "commits": {}},
    "failure": None,
}


def sanitize(value):
    if TEMP_ROOT is not None:
        return value.replace(str(TEMP_ROOT.resolve()), "$TMP").replace(
            str(TEMP_ROOT), "$TMP"
        )
    return value


def run(repo, *args):
    command = ["git", *args]
    completed = subprocess.run(
        command,
        cwd=repo,
        env=GIT_ENV,
        check=False,
        capture_output=True,
        text=True,
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
    results["actual"]["checks"].append(
        {"name": name, "expected": expected, "actual": actual, "passed": passed}
    )
    assert passed, f"{name}: expected {expected!r}, got {actual!r}"


def create_history(repo):
    repo.mkdir()
    run(None, "init", "--initial-branch=main", str(repo))
    run(repo, "config", "user.name", "Course Student")
    run(repo, "config", "user.email", "student@example.invalid")

    (repo / "notes.txt").write_text("alpha\n", encoding="utf-8")
    run(repo, "add", "notes.txt")
    run(repo, "commit", "-m", "A")
    commit_a = run(repo, "rev-parse", "HEAD")

    with (repo / "notes.txt").open("a", encoding="utf-8") as notes:
        notes.write("beta\n")
    run(repo, "add", "notes.txt")
    run(repo, "commit", "-m", "B")
    commit_b = run(repo, "rev-parse", "HEAD")

    (repo / "todo.txt").write_text("one\n", encoding="utf-8")
    run(repo, "add", "todo.txt")
    run(repo, "commit", "-m", "C")
    commit_c = run(repo, "rev-parse", "HEAD")
    run(repo, "branch", "topic", commit_b)

    author_output = run(repo, "log", "--reverse", "--format=%an%x00%ae", "main")
    check(
        "initial commit authors",
        [line.split("\x00") for line in author_output.splitlines()],
        [["Course Student", "student@example.invalid"]] * 3,
    )
    check("main initially points to C", run(repo, "rev-parse", "main"), commit_c)
    check("topic initially points to B", run(repo, "rev-parse", "topic"), commit_b)
    results["actual"]["commits"] = {
        "A": commit_a,
        "B": commit_b,
        "C": commit_c,
    }
    return commit_b, commit_c


def main():
    global TEMP_ROOT
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="R03-T017-") as directory:
            TEMP_ROOT = Path(directory)
            repo = TEMP_ROOT / "repo"
            commit_b, commit_c = create_history(repo)

            run(repo, "reset", "HEAD~", "--soft")
            after_soft_reset = {
                "main": run(repo, "rev-parse", "main"),
                "current_branch": run(repo, "branch", "--show-current"),
                "staged_paths": run(repo, "diff", "--cached", "--name-only").splitlines(),
                "todo_txt": (repo / "todo.txt").read_text(encoding="utf-8"),
            }
            check(
                "soft reset removes C from main but preserves its staged changes",
                after_soft_reset,
                {
                    **results["expected"]["after_soft_reset"],
                    "main": commit_b,
                },
            )

            run(repo, "stash")
            after_stash = {
                "main": run(repo, "rev-parse", "main"),
                "status": run(repo, "status", "--porcelain"),
                "stash_count": len(run(repo, "stash", "list", "--format=%H").splitlines()),
            }
            check(
                "stash records the change and cleans the worktree",
                after_stash,
                {**results["expected"]["after_stash"], "main": commit_b},
            )

            run(repo, "checkout", "topic")
            check("checkout switched to topic", run(repo, "branch", "--show-current"), "topic")
            run(repo, "stash", "pop")
            check("pop restored todo.txt", (repo / "todo.txt").read_text(encoding="utf-8"), "one\n")

            run(repo, "add", "todo.txt")
            run(repo, "commit", "-m", "C moved to topic")
            moved_commit = run(repo, "rev-parse", "HEAD")
            topic_parent = run(repo, "rev-parse", "HEAD^")
            check("new topic commit is distinct from original C", moved_commit != commit_c, True)

            after_move = {
                "main": run(repo, "rev-parse", "main"),
                "topic_parent": topic_parent,
                "current_branch": run(repo, "branch", "--show-current"),
                "topic_commit_count": run(repo, "rev-list", "--count", "topic"),
                "status": run(repo, "status", "--porcelain"),
                "notes_txt": (repo / "notes.txt").read_text(encoding="utf-8"),
                "todo_txt": (repo / "todo.txt").read_text(encoding="utf-8"),
                "stash_count": len(run(repo, "stash", "list", "--format=%H").splitlines()),
            }
            check(
                "commit change now belongs to topic",
                after_move,
                {
                    **results["expected"]["after_stash_pop_and_commit"],
                    "main": commit_b,
                    "topic_parent": commit_b,
                },
            )
            results["actual"]["states"] = {
                "after_soft_reset": after_soft_reset,
                "after_stash": after_stash,
                "after_stash_pop_and_commit": after_move,
            }
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
                    "operation_sequence": [
                        ["git", "reset", "HEAD~", "--soft"],
                        ["git", "stash"],
                        ["git", "checkout", "topic"],
                        ["git", "stash", "pop"],
                        ["git", "add", "todo.txt"],
                        ["git", "commit", "-m", "C moved to topic"],
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
