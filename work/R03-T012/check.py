#!/usr/bin/env python3
"""Verify the index and worktree effects of documented git reset forms."""

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
    "scenarios": [
        {
            "name": "default reset unstages all staged edits",
            "command": ["reset"],
            "expected_effect": "main stays at C; both edits remain in the worktree and are unstaged",
        },
        {
            "name": "path reset unstages only the selected path",
            "command": ["reset", "--", "notes.txt"],
            "expected_effect": "main stays at C; notes.txt is unstaged and todo.txt remains staged",
        },
        {
            "name": "hard reset moves main to B and restores its tree",
            "command": ["reset", "--hard", "HEAD~1"],
            "expected_effect": "main moves from C to B; todo.txt is removed and notes.txt is restored",
        },
    ],
}

results = {
    "expected": {
        "default_reset": {
            "head": "C",
            "topic": "B",
            "staged_paths": [],
            "unstaged_paths": ["notes.txt", "todo.txt"],
            "notes_txt": "alpha\nbeta changed\n",
            "todo_txt": "one changed\n",
        },
        "path_reset": {
            "head": "C",
            "topic": "B",
            "staged_paths": ["todo.txt"],
            "unstaged_paths": ["notes.txt"],
            "notes_txt": "alpha changed\nbeta\n",
            "todo_txt": "one changed\n",
        },
        "hard_reset": {
            "head": "B",
            "topic": "B",
            "commit_count": "2",
            "status": "",
            "notes_txt": "alpha\nbeta\n",
            "todo_exists": False,
        },
    },
    "actual": {"scenarios": []},
    "failure": None,
}

git_env = os.environ.copy()
git_env["GIT_CONFIG_NOSYSTEM"] = "1"
git_env["GIT_CONFIG_GLOBAL"] = os.devnull


def run_git(repo, *args):
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=git_env,
        check=False,
        capture_output=True,
        text=True,
    )
    command_record = {
        "command": ["git", *args],
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }
    results["actual"].setdefault("commands", []).append(command_record)
    if completed.returncode != 0:
        raise AssertionError(
            f"Git command failed ({completed.returncode}): git {' '.join(args)}\n"
            f"{completed.stderr}"
        )
    return completed.stdout.strip()


def check(name, actual, expected):
    passed = actual == expected
    results["actual"].setdefault("checks", []).append(
        {"name": name, "expected": expected, "actual": actual, "passed": passed}
    )
    assert passed, f"{name}: expected {expected!r}, got {actual!r}"


def create_repository(repo):
    run_git(None, "init", "--initial-branch=main", str(repo))
    run_git(repo, "config", "user.name", INPUTS["repository"]["author_name"])
    run_git(repo, "config", "user.email", INPUTS["repository"]["author_email"])

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

    actual_authors = run_git(
        repo, "log", "--reverse", "--format=%an%x00%ae", "main"
    )
    expected_author = [
        INPUTS["repository"]["author_name"],
        INPUTS["repository"]["author_email"],
    ]
    check(
        "all initial commit authors",
        [line.split("\x00") for line in actual_authors.splitlines()],
        [expected_author] * 3,
    )
    check("A is an object", run_git(repo, "cat-file", "-t", commit_a), "commit")
    check("main initially points to C", run_git(repo, "rev-parse", "main"), commit_c)
    check("topic initially points to B", run_git(repo, "rev-parse", "topic"), commit_b)
    check(
        "three initial commits",
        run_git(repo, "rev-list", "--count", "main"),
        "3",
    )
    return commit_b, commit_c


def changed_paths(repo, *args):
    output = run_git(repo, *args)
    return sorted(output.splitlines()) if output else []


def run_default_reset(directory):
    repo = Path(directory) / "default"
    repo.mkdir()
    commit_b, commit_c = create_repository(repo)
    (repo / "notes.txt").write_text("alpha\nbeta changed\n", encoding="utf-8")
    (repo / "todo.txt").write_text("one changed\n", encoding="utf-8")
    run_git(repo, "add", "notes.txt", "todo.txt")
    run_git(repo, "reset")

    actual = {
        "head": run_git(repo, "rev-parse", "HEAD"),
        "topic": run_git(repo, "rev-parse", "topic"),
        "staged_paths": changed_paths(repo, "diff", "--cached", "--name-only"),
        "unstaged_paths": changed_paths(repo, "diff", "--name-only"),
        "notes_txt": (repo / "notes.txt").read_text(encoding="utf-8"),
        "todo_txt": (repo / "todo.txt").read_text(encoding="utf-8"),
    }
    expected = {
        **results["expected"]["default_reset"],
        "head": commit_c,
        "topic": commit_b,
    }
    check("default git reset preserves edits but unstages them", actual, expected)
    results["actual"]["scenarios"].append({"name": "default_reset", "state": actual})


def run_path_reset(directory):
    repo = Path(directory) / "path"
    repo.mkdir()
    commit_b, commit_c = create_repository(repo)
    (repo / "notes.txt").write_text("alpha changed\nbeta\n", encoding="utf-8")
    (repo / "todo.txt").write_text("one changed\n", encoding="utf-8")
    run_git(repo, "add", "notes.txt", "todo.txt")
    run_git(repo, "reset", "--", "notes.txt")

    actual = {
        "head": run_git(repo, "rev-parse", "HEAD"),
        "topic": run_git(repo, "rev-parse", "topic"),
        "staged_paths": changed_paths(repo, "diff", "--cached", "--name-only"),
        "unstaged_paths": changed_paths(repo, "diff", "--name-only"),
        "notes_txt": (repo / "notes.txt").read_text(encoding="utf-8"),
        "todo_txt": (repo / "todo.txt").read_text(encoding="utf-8"),
    }
    expected = {
        **results["expected"]["path_reset"],
        "head": commit_c,
        "topic": commit_b,
    }
    check("path git reset unstages only the selected path", actual, expected)
    results["actual"]["scenarios"].append({"name": "path_reset", "state": actual})


def run_hard_reset(directory):
    repo = Path(directory) / "hard"
    repo.mkdir()
    commit_b, _ = create_repository(repo)
    (repo / "notes.txt").write_text("discard this edit\n", encoding="utf-8")
    run_git(repo, "add", "notes.txt")
    (repo / "todo.txt").write_text("discard this edit too\n", encoding="utf-8")
    run_git(repo, "reset", "--hard", "HEAD~1")

    actual = {
        "head": run_git(repo, "rev-parse", "HEAD"),
        "topic": run_git(repo, "rev-parse", "topic"),
        "commit_count": run_git(repo, "rev-list", "--count", "main"),
        "status": run_git(repo, "status", "--porcelain"),
        "notes_txt": (repo / "notes.txt").read_text(encoding="utf-8"),
        "todo_exists": (repo / "todo.txt").exists(),
    }
    expected = {**results["expected"]["hard_reset"], "head": commit_b, "topic": commit_b}
    check("hard git reset moves branch and discards local state", actual, expected)
    results["actual"]["scenarios"].append({"name": "hard_reset", "state": actual})


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
        with tempfile.TemporaryDirectory(prefix="R03-T012-") as directory:
            run_default_reset(directory)
            run_path_reset(directory)
            run_hard_reset(directory)
    except Exception as error:
        results["failure"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        (OUTPUT_DIR / "results.json").write_text(
            json.dumps(results, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
