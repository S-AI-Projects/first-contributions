#!/usr/bin/env python3
"""Verify git rm --cached affects the index, commit, and remote as described."""

import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "work" / "R03-T018"
TEMP_ROOT = None
GIT_ENV = os.environ.copy()
GIT_ENV["GIT_CONFIG_NOSYSTEM"] = "1"
GIT_ENV["GIT_CONFIG_GLOBAL"] = os.devnull

results = {
    "expected": {
        "after_cached_remove": {
            "working_file_exists": True,
            "working_file_content": "alpha\nbeta\n",
            "staged_paths": ["notes.txt"],
            "unstaged_paths": [],
        },
        "after_commit_and_push": {
            "local_head_equals_remote": True,
            "local_file_exists": True,
            "remote_file_exists": False,
            "remote_todo_content": "one\n",
        },
        "multiple_file_removal": {
            "file1_exists": True,
            "file2_exists": True,
            "staged_paths": ["file1.txt", "file2.txt"],
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


def run_git(repo, *args):
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
    results["actual"]["checks"].append(
        {"name": name, "expected": expected, "actual": actual, "passed": passed}
    )
    assert passed, f"{name}: expected {expected!r}, got {actual!r}"


def make_repository(repo):
    repo.mkdir()
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
    run_git(repo, "branch", "topic", commit_b)
    check("main history length", run_git(repo, "rev-list", "--count", "main"), "3")
    check("main points to C", run_git(repo, "rev-parse", "main"), commit_c)
    check("topic points to B", run_git(repo, "rev-parse", "topic"), commit_b)
    authors = run_git(repo, "log", "--reverse", "--format=%an%x00%ae", "main")
    check(
        "all initial commit authors",
        [line.split("\x00") for line in authors.splitlines()],
        [["Course Student", "student@example.invalid"]] * 3,
    )
    results["actual"]["commits"] = {
        "A": commit_a,
        "B": commit_b,
        "C": commit_c,
    }


def tracked_paths(repo, *args):
    output = run_git(repo, *args)
    return sorted(output.splitlines()) if output else []


def test_cached_remove_and_remote(parent):
    repo = parent / "working"
    make_repository(repo)
    bare = parent / "remote.git"
    run_git(None, "init", "--bare", "--initial-branch=main", str(bare))
    remote_url = bare.as_uri()
    run_git(repo, "remote", "add", "origin", remote_url)
    run_git(repo, "push", "-u", "origin", "main")

    run_git(repo, "rm", "--cached", "notes.txt")
    after_remove = {
        "working_file_exists": (repo / "notes.txt").exists(),
        "working_file_content": (repo / "notes.txt").read_text(encoding="utf-8"),
        "staged_paths": tracked_paths(repo, "diff", "--cached", "--name-only"),
        "unstaged_paths": tracked_paths(repo, "diff", "--name-only"),
    }
    check(
        "cached remove stages deletion but keeps working file",
        after_remove,
        results["expected"]["after_cached_remove"],
    )

    run_git(repo, "commit", "-m", "Stop tracking notes.txt")
    removal_commit = run_git(repo, "rev-parse", "HEAD")
    run_git(repo, "push", "origin", "main")
    remote_head = run_git(repo, "ls-remote", "origin", "refs/heads/main").split()[0]
    remote_notes = subprocess.run(
        ["git", "--git-dir", str(bare), "cat-file", "-e", f"{remote_head}:notes.txt"],
        env=GIT_ENV,
        check=False,
        capture_output=True,
        text=True,
    )
    results["actual"]["commands"].append(
        {
            "command": [
                "git",
                "--git-dir",
                sanitize(str(bare)),
                "cat-file",
                "-e",
                f"{remote_head}:notes.txt",
            ],
            "cwd": None,
            "returncode": remote_notes.returncode,
            "stdout": remote_notes.stdout.strip(),
            "stderr": remote_notes.stderr.strip(),
        }
    )
    if remote_notes.returncode not in (0, 1, 128):
        raise AssertionError(f"Unexpected remote cat-file code: {remote_notes.returncode}")

    remote_todo = subprocess.run(
        ["git", "--git-dir", str(bare), "show", f"{remote_head}:todo.txt"],
        env=GIT_ENV,
        check=False,
        capture_output=True,
        text=True,
    )
    results["actual"]["commands"].append(
        {
            "command": [
                "git",
                "--git-dir",
                sanitize(str(bare)),
                "show",
                f"{remote_head}:todo.txt",
            ],
            "cwd": None,
            "returncode": remote_todo.returncode,
            "stdout": remote_todo.stdout.strip(),
            "stderr": remote_todo.stderr.strip(),
        }
    )
    if remote_todo.returncode != 0:
        raise AssertionError(f"Remote todo.txt read failed: {remote_todo.stderr}")

    after_push = {
        "local_head_equals_remote": run_git(repo, "rev-parse", "HEAD") == remote_head,
        "local_file_exists": (repo / "notes.txt").exists(),
        "remote_file_exists": remote_notes.returncode == 0,
        "remote_todo_content": remote_todo.stdout,
    }
    check(
        "commit and push removes file from remote but not local disk",
        after_push,
        results["expected"]["after_commit_and_push"],
    )
    results["actual"]["states"] = {
        "after_cached_remove": after_remove,
        "after_commit_and_push": after_push,
        "removal_commit": removal_commit,
        "remote_url": sanitize(remote_url),
    }


def test_multiple_files(parent):
    repo = parent / "multiple"
    repo.mkdir()
    run_git(None, "init", "--initial-branch=main", str(repo))
    run_git(repo, "config", "user.name", "Course Student")
    run_git(repo, "config", "user.email", "student@example.invalid")
    for name in ("file1.txt", "file2.txt"):
        (repo / name).write_text(f"{name}\n", encoding="utf-8")
    run_git(repo, "add", "file1.txt", "file2.txt")
    run_git(repo, "commit", "-m", "Add multiple files")
    run_git(repo, "rm", "--cached", "file1.txt", "file2.txt")
    actual = {
        "file1_exists": (repo / "file1.txt").exists(),
        "file2_exists": (repo / "file2.txt").exists(),
        "staged_paths": tracked_paths(repo, "diff", "--cached", "--name-only"),
    }
    check(
        "cached remove accepts multiple paths and keeps both files",
        actual,
        results["expected"]["multiple_file_removal"],
    )
    results["actual"]["multiple_file_removal"] = actual


def main():
    global TEMP_ROOT
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="R03-T018-") as directory:
            TEMP_ROOT = Path(directory)
            parent = TEMP_ROOT / "repos"
            parent.mkdir()
            test_cached_remove_and_remote(parent)
            test_multiple_files(parent)
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
                        ["git", "rm", "--cached", "notes.txt"],
                        ["git", "commit", "-m", "Stop tracking notes.txt"],
                        ["git", "push", "origin", "main"],
                        ["git", "rm", "--cached", "file1.txt", "file2.txt"],
                    ],
                    "remote": "temporary local bare repository via file:// URL",
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
