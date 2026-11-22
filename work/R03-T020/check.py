#!/usr/bin/env python3
"""Verify credential-cache helper values at global and repository scopes."""

import json
import os
import platform
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "work" / "R03-T020"
TEMP_ROOT = None

results = {
    "expected": {
        "global_only": ["cache"],
        "repository_only": ["cache"],
        "global_and_repository": ["cache", "cache"],
        "global_and_repository_timeout": ["cache", "cache --timeout=3600"],
        "global_after_repository_timeout": ["cache"],
        "repository": {
            "branch": "main",
            "commit_count": "3",
            "topic_at": "B",
            "notes_txt": "alpha\nbeta\n",
            "todo_txt": "one\n",
        },
    },
    "actual": {"commands": [], "checks": [], "commits": {}},
    "failure": None,
}


def sanitize(value):
    if TEMP_ROOT is not None:
        value = value.replace(str(TEMP_ROOT.resolve()), "$TMP").replace(
            str(TEMP_ROOT), "$TMP"
        )
    return re.sub(
        r"(?:/private)?/var/folders/[^ \t\n]*/T/R03-T020-[^/\t\n ]+",
        "$TMP",
        value,
    )


def run(command, *, env, cwd=None):
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
    if completed.returncode != 0:
        raise AssertionError(
            f"Command failed ({completed.returncode}): {command!r}\n"
            f"{completed.stderr}"
        )
    return completed.stdout.strip()


def git(repo, env, *args):
    return run(["git", *args], cwd=repo, env=env)


def check(name, actual, expected):
    passed = actual == expected
    results["actual"]["checks"].append(
        {"name": name, "expected": expected, "actual": actual, "passed": passed}
    )
    assert passed, f"{name}: expected {expected!r}, got {actual!r}"


def create_history(repo, env):
    repo.mkdir()
    run(["git", "init", "--initial-branch=main", str(repo)], env=env)
    git(repo, env, "config", "user.name", "Course Student")
    git(repo, env, "config", "user.email", "student@example.invalid")

    (repo / "notes.txt").write_text("alpha\n", encoding="utf-8")
    git(repo, env, "add", "notes.txt")
    git(repo, env, "commit", "-m", "A")
    commit_a = git(repo, env, "rev-parse", "HEAD")

    with (repo / "notes.txt").open("a", encoding="utf-8") as notes:
        notes.write("beta\n")
    git(repo, env, "add", "notes.txt")
    git(repo, env, "commit", "-m", "B")
    commit_b = git(repo, env, "rev-parse", "HEAD")

    (repo / "todo.txt").write_text("one\n", encoding="utf-8")
    git(repo, env, "add", "todo.txt")
    git(repo, env, "commit", "-m", "C")
    commit_c = git(repo, env, "rev-parse", "HEAD")
    git(repo, env, "branch", "topic", commit_b)

    authors = git(repo, env, "log", "--reverse", "--format=%an%x00%ae", "main")
    check(
        "all initial commit authors",
        [line.split("\x00") for line in authors.splitlines()],
        [["Course Student", "student@example.invalid"]] * 3,
    )
    check("main branch", git(repo, env, "branch", "--show-current"), "main")
    check("three commits", git(repo, env, "rev-list", "--count", "main"), "3")
    check("main points to C", git(repo, env, "rev-parse", "main"), commit_c)
    check("topic points to B", git(repo, env, "rev-parse", "topic"), commit_b)
    results["actual"]["commits"] = {
        "A": commit_a,
        "B": commit_b,
        "C": commit_c,
    }


def config_values(repo, env, *scope_args):
    output = git(
        repo, env, "config", *scope_args, "--get-all", "credential.helper"
    )
    return output.splitlines() if output else []


def main():
    global TEMP_ROOT
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="R03-T020-") as directory:
            TEMP_ROOT = Path(directory)
            home = TEMP_ROOT / "home"
            home.mkdir()
            global_config = home / ".gitconfig"
            env = os.environ.copy()
            env["GIT_CONFIG_NOSYSTEM"] = "1"
            env["GIT_CONFIG_GLOBAL"] = str(global_config)
            env["HOME"] = str(home)
            repo = TEMP_ROOT / "repo"
            create_history(repo, env)

            run(
                ["git", "config", "--global", "credential.helper", "cache"],
                env=env,
            )
            global_only = config_values(repo, env)
            check("global cache helper", global_only, ["cache"])

            git(repo, env, "config", "credential.helper", "cache")
            repository_only = config_values(repo, env, "--local")
            global_and_repository = config_values(repo, env)
            check("repository cache helper", repository_only, ["cache"])
            check(
                "global and repository helpers",
                global_and_repository,
                ["cache", "cache"],
            )

            git(
                repo,
                env,
                "config",
                "credential.helper",
                "cache --timeout=3600",
            )
            local_with_timeout = config_values(repo, env, "--local")
            global_and_repository_timeout = config_values(repo, env)
            global_after_timeout = config_values(repo, env, "--global")
            check(
                "repository timeout setting",
                local_with_timeout,
                ["cache --timeout=3600"],
            )
            check(
                "timeout helper is added to global effective config",
                global_and_repository_timeout,
                ["cache", "cache --timeout=3600"],
            )
            check(
                "repository timeout does not change global helper",
                global_after_timeout,
                ["cache"],
            )

            origin_lines = git(
                repo,
                env,
                "config",
                "--show-origin",
                "--get-all",
                "credential.helper",
            ).splitlines()
            check("both config scopes are shown", len(origin_lines), 2)
            results["actual"]["config"] = {
                "global_only": global_only,
                "repository_only": repository_only,
                "global_and_repository": global_and_repository,
                "global_and_repository_timeout": global_and_repository_timeout,
                "global_after_repository_timeout": global_after_timeout,
                "origins": [
                    "global: cache",
                    "local: cache --timeout=3600",
                ],
            }
            repository = {
                "branch": git(repo, env, "branch", "--show-current"),
                "commit_count": git(repo, env, "rev-list", "--count", "main"),
                "main_head": git(repo, env, "rev-parse", "main"),
                "topic_head": git(repo, env, "rev-parse", "topic"),
                "notes_txt": (repo / "notes.txt").read_text(encoding="utf-8"),
                "todo_txt": (repo / "todo.txt").read_text(encoding="utf-8"),
            }
            check(
                "repository state",
                repository,
                {
                    "branch": "main",
                    "commit_count": "3",
                    "main_head": results["actual"]["commits"]["C"],
                    "topic_head": results["actual"]["commits"]["B"],
                    "notes_txt": "alpha\nbeta\n",
                    "todo_txt": "one\n",
                },
            )
            results["actual"]["repository"] = repository
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
                    "config_commands": [
                        ["git", "config", "--global", "credential.helper", "cache"],
                        ["git", "config", "credential.helper", "cache"],
                        [
                            "git",
                            "config",
                            "credential.helper",
                            "cache --timeout=3600",
                        ],
                    ],
                    "credentials_used": False,
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
