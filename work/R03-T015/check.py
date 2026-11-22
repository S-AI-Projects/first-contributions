#!/usr/bin/env python3
"""Verify the Ubuntu guide's Git version and global user.name commands."""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "work" / "R03-T015"
VERSION_PATTERN = re.compile(r"^git version \d+(?:\.\d+)+(?:[-+.]?\w.*)?$")
TEMP_ROOT: Path | None = None

results = {
    "expected": {
        "git_version": "git --version succeeds and reports a version, not a pinned value",
        "global_name": "git config --global user.name stores Your Name in the isolated config",
        "repo": {
            "initial_branch": "main",
            "author": ["Course Student", "student@example.invalid"],
            "main_commit_count": "3",
            "topic_points_to": "B",
            "notes_txt": "alpha\nbeta\n",
            "todo_txt": "one\n",
        },
    },
    "actual": {"commands": [], "checks": [], "commits": {}},
    "failure": None,
}


def run(command, *, cwd=None, env=None):
    completed = subprocess.run(
        command, cwd=cwd, env=env, check=False, capture_output=True, text=True
    )
    results["actual"]["commands"].append(
        {
            "command": [sanitize(item) for item in command],
            "cwd": sanitize(str(cwd)) if cwd else None,
            "returncode": completed.returncode,
            "stdout": sanitize(completed.stdout.strip()),
            "stderr": sanitize(completed.stderr.strip()),
        }
    )
    if completed.returncode:
        raise AssertionError(
            f"Command failed ({completed.returncode}): {command!r}\n"
            f"{completed.stderr}"
        )
    return completed.stdout.strip()


def sanitize(value):
    if TEMP_ROOT is not None:
        return value.replace(str(TEMP_ROOT.resolve()), "$TMP").replace(
            str(TEMP_ROOT), "$TMP"
        )
    return value


def check(name, actual, expected):
    passed = actual == expected
    results["actual"]["checks"].append(
        {"name": name, "expected": expected, "actual": actual, "passed": passed}
    )
    assert passed, f"{name}: expected {expected!r}, got {actual!r}"


def test_version_and_global_name(home):
    home.mkdir(parents=True)
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["GIT_CONFIG_GLOBAL"] = str(home / ".gitconfig")
    env["GIT_CONFIG_NOSYSTEM"] = "1"

    version = run(["git", "--version"], env=env)
    check("Git version output format", bool(VERSION_PATTERN.fullmatch(version)), True)
    results["actual"]["git_version"] = version

    run(["git", "config", "--global", "user.name", "Your Name"], env=env)
    configured_name = run(
        ["git", "config", "--global", "--get", "user.name"], env=env
    )
    check("global Git user.name", configured_name, "Your Name")


def test_repository(repo):
    base_env = os.environ.copy()
    base_env["GIT_CONFIG_NOSYSTEM"] = "1"
    base_env["GIT_CONFIG_GLOBAL"] = os.devnull

    run(["git", "init", "--initial-branch=main", str(repo)], env=base_env)

    def git(*args):
        return run(["git", *args], cwd=repo, env=base_env)

    git("config", "user.name", "Course Student")
    git("config", "user.email", "student@example.invalid")

    (repo / "notes.txt").write_text("alpha\n", encoding="utf-8")
    git("add", "notes.txt")
    git("commit", "-m", "A")
    commit_a = git("rev-parse", "HEAD")

    with (repo / "notes.txt").open("a", encoding="utf-8") as notes:
        notes.write("beta\n")
    git("add", "notes.txt")
    git("commit", "-m", "B")
    commit_b = git("rev-parse", "HEAD")

    (repo / "todo.txt").write_text("one\n", encoding="utf-8")
    git("add", "todo.txt")
    git("commit", "-m", "C")
    commit_c = git("rev-parse", "HEAD")
    git("branch", "topic", commit_b)

    author_output = git("show", "-s", "--format=%an%x00%ae", "main")
    check(
        "commit C author identity",
        author_output.split("\x00"),
        ["Course Student", "student@example.invalid"],
    )
    actual_state = {
        "initial_branch": git("branch", "--show-current"),
        "main_commit_count": git("rev-list", "--count", "main"),
        "main_head": git("rev-parse", "main"),
        "topic_head": git("rev-parse", "topic"),
        "notes_txt": (repo / "notes.txt").read_text(encoding="utf-8"),
        "todo_txt": (repo / "todo.txt").read_text(encoding="utf-8"),
    }
    check(
        "temporary repository state",
        actual_state,
        {
            "initial_branch": "main",
            "main_commit_count": "3",
            "main_head": commit_c,
            "topic_head": commit_b,
            "notes_txt": "alpha\nbeta\n",
            "todo_txt": "one\n",
        },
    )
    results["actual"]["commits"] = {
        "A": commit_a,
        "B": commit_b,
        "C": commit_c,
    }
    results["actual"]["repo_state"] = actual_state


def main():
    global TEMP_ROOT
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="R03-T015-") as directory:
            temporary_root = Path(directory)
            TEMP_ROOT = temporary_root
            test_version_and_global_name(temporary_root / "home")
            repo = temporary_root / "repo"
            repo.mkdir()
            test_repository(repo)
    except Exception as error:
        results["failure"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        (OUTPUT_DIR / "inputs.json").write_text(
            json.dumps(
                {
                    "commands_under_test": [
                        ["git", "--version"],
                        ["git", "config", "--global", "user.name", "Your Name"],
                    ],
                    "temporary_repository": {
                        "branch": "main",
                        "author_name": "Course Student",
                        "author_email": "student@example.invalid",
                        "commits": [
                            {"label": "A", "file": "notes.txt", "content": "alpha\n"},
                            {"label": "B", "append": "notes.txt", "content": "beta\n"},
                            {"label": "C", "file": "todo.txt", "content": "one\n"},
                        ],
                        "topic_at": "B",
                    },
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
            f"Python: {os.sys.version.split()[0]}\n{git_version}\n",
            encoding="utf-8",
        )
        (OUTPUT_DIR / "results.json").write_text(
            json.dumps(results, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
