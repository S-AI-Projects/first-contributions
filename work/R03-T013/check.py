#!/usr/bin/env python3
"""Verify git stash apply across branches and with existing working edits."""

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
            "name": "apply on another branch with a clean worktree",
            "stashed_edit": "append 'stashed line\\n' to notes.txt on main",
            "target_branch": "topic",
            "existing_edit": None,
            "expected": "successful apply, branch remains topic, stash is retained",
        },
        {
            "name": "apply on another branch with a non-conflicting local edit",
            "stashed_edit": "append 'stashed line\\n' to notes.txt on main",
            "target_branch": "topic",
            "existing_edit": "create untracked draft.txt on topic",
            "expected": "successful merge of both edits, stash is retained",
        },
        {
            "name": "apply on another branch with a conflicting local edit",
            "stashed_edit": "change alpha to stashed alpha on main",
            "target_branch": "topic",
            "existing_edit": "change alpha to local alpha on topic",
            "expected": "apply reports conflict, conflict markers exist, stash is retained",
        },
    ],
}

results = {
    "expected": {
        "clean_cross_branch": {
            "branch": "topic",
            "head": "B",
            "notes_txt": "alpha\nbeta\nstashed line\n",
            "todo_exists": False,
            "stash_count": 1,
            "status": " M notes.txt",
        },
        "dirty_non_conflicting": {
            "branch": "topic",
            "head": "B",
            "notes_txt": "alpha\nbeta\nstashed line\n",
            "draft_txt": "local draft\n",
            "stash_count": 1,
            "status": " M notes.txt\n?? draft.txt",
        },
        "dirty_conflicting": {
            "branch": "topic",
            "head": "topic test commit",
            "stash_count": 1,
            "unmerged_paths": ["notes.txt"],
            "conflict_markers": True,
            "draft_txt": "uncommitted local draft\n",
            "status": "UU notes.txt\n?? draft.txt",
        },
    },
    "actual": {"scenarios": [], "commands": [], "commits": {}},
    "failure": None,
}

git_env = os.environ.copy()
git_env["GIT_CONFIG_NOSYSTEM"] = "1"
git_env["GIT_CONFIG_GLOBAL"] = os.devnull


def run_git(repo, *args, expected_returncode=0):
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
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
            "expected_returncode": expected_returncode,
        }
    )
    if completed.returncode != expected_returncode:
        raise AssertionError(
            f"Git command returned {completed.returncode}, expected "
            f"{expected_returncode}: git {' '.join(args)}\n{completed.stderr}"
        )
    return completed


def output(repo, *args):
    return run_git(repo, *args).stdout.strip()


def output_exact(repo, *args):
    return run_git(repo, *args).stdout.rstrip("\n")


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
    commit_a = output(repo, "rev-parse", "HEAD")

    with (repo / "notes.txt").open("a", encoding="utf-8") as notes:
        notes.write("beta\n")
    run_git(repo, "add", "notes.txt")
    run_git(repo, "commit", "-m", "B")
    commit_b = output(repo, "rev-parse", "HEAD")

    (repo / "todo.txt").write_text("one\n", encoding="utf-8")
    run_git(repo, "add", "todo.txt")
    run_git(repo, "commit", "-m", "C")
    commit_c = output(repo, "rev-parse", "HEAD")
    run_git(repo, "branch", "topic", commit_b)

    authors = output(repo, "log", "--reverse", "--format=%an%x00%ae", "main")
    expected_author = [
        INPUTS["repository"]["author_name"],
        INPUTS["repository"]["author_email"],
    ]
    check(
        "all initial commit authors",
        [line.split("\x00") for line in authors.splitlines()],
        [expected_author] * 3,
    )
    check("main contains three commits", output(repo, "rev-list", "--count", "main"), "3")
    check("main points to C", output(repo, "rev-parse", "main"), commit_c)
    check("topic points to B", output(repo, "rev-parse", "topic"), commit_b)
    check("A is a commit", output(repo, "cat-file", "-t", commit_a), "commit")
    results["actual"]["commits"] = {"A": commit_a, "B": commit_b, "C": commit_c}
    return commit_b


def stash_main_edit(repo, edit_type):
    notes_path = repo / "notes.txt"
    notes = notes_path.read_text(encoding="utf-8")
    if edit_type == "append":
        notes += "stashed line\n"
    else:
        notes = notes.replace("alpha\n", "stashed alpha\n", 1)
    notes_path.write_text(notes, encoding="utf-8")
    run_git(repo, "stash", "push", "-m", "stash test edit")
    check("main is clean after stash", output(repo, "status", "--porcelain"), "")
    stash_oid = output(repo, "rev-parse", "stash@{0}")
    output(repo, "switch", "topic")
    check("target branch is topic", output(repo, "branch", "--show-current"), "topic")
    check("topic points to B", output(repo, "rev-parse", "HEAD"), results["actual"]["commits"]["B"])
    return stash_oid


def verify_stash_kept(repo, stash_oid):
    check(
        "apply leaves the stash on the stack",
        output(repo, "rev-parse", "stash@{0}"),
        stash_oid,
    )
    check(
        "one stash remains",
        len(output(repo, "stash", "list", "--format=%H").splitlines()),
        1,
    )


def run_clean_cross_branch(directory):
    repo = Path(directory) / "clean"
    repo.mkdir()
    commit_b = create_repository(repo)
    stash_oid = stash_main_edit(repo, "append")
    applied = run_git(repo, "stash", "apply")
    check("cross-branch apply succeeds", applied.returncode, 0)
    actual = {
        "branch": output(repo, "branch", "--show-current"),
        "head": output(repo, "rev-parse", "HEAD"),
        "notes_txt": (repo / "notes.txt").read_text(encoding="utf-8"),
        "todo_exists": (repo / "todo.txt").exists(),
        "stash_count": len(output(repo, "stash", "list", "--format=%H").splitlines()),
        "status": output_exact(repo, "status", "--porcelain"),
    }
    expected = {**results["expected"]["clean_cross_branch"], "head": commit_b}
    check("clean cross-branch application state", actual, expected)
    verify_stash_kept(repo, stash_oid)
    results["actual"]["scenarios"].append({"name": "clean_cross_branch", "state": actual})


def run_dirty_non_conflicting(directory):
    repo = Path(directory) / "non-conflicting"
    repo.mkdir()
    commit_b = create_repository(repo)
    stash_oid = stash_main_edit(repo, "append")
    (repo / "draft.txt").write_text("local draft\n", encoding="utf-8")
    applied = run_git(repo, "stash", "apply")
    check("non-conflicting dirty apply succeeds", applied.returncode, 0)
    notes = (repo / "notes.txt").read_text(encoding="utf-8")
    actual = {
        "branch": output(repo, "branch", "--show-current"),
        "head": output(repo, "rev-parse", "HEAD"),
        "notes_txt": notes,
        "draft_txt": (repo / "draft.txt").read_text(encoding="utf-8"),
        "stash_count": len(output(repo, "stash", "list", "--format=%H").splitlines()),
        "status": output_exact(repo, "status", "--porcelain"),
    }
    expected = {**results["expected"]["dirty_non_conflicting"], "head": commit_b}
    check("dirty non-conflicting application state", actual, expected)
    verify_stash_kept(repo, stash_oid)
    results["actual"]["scenarios"].append(
        {"name": "dirty_non_conflicting", "state": actual}
    )


def run_dirty_conflicting(directory):
    repo = Path(directory) / "conflicting"
    repo.mkdir()
    create_repository(repo)
    stash_oid = stash_main_edit(repo, "replace")
    (repo / "notes.txt").write_text(
        (repo / "notes.txt").read_text(encoding="utf-8").replace(
            "alpha\n", "local alpha\n", 1
        ),
        encoding="utf-8",
    )
    run_git(repo, "add", "notes.txt")
    run_git(repo, "commit", "-m", "D: change alpha on topic")
    topic_test_commit = output(repo, "rev-parse", "HEAD")
    (repo / "draft.txt").write_text("uncommitted local draft\n", encoding="utf-8")
    applied = run_git(repo, "stash", "apply", expected_returncode=1)
    check("conflicting apply reports failure", applied.returncode, 1)
    notes = (repo / "notes.txt").read_text(encoding="utf-8")
    unmerged = output(repo, "diff", "--name-only", "--diff-filter=U").splitlines()
    actual = {
        "branch": output(repo, "branch", "--show-current"),
        "head": output(repo, "rev-parse", "HEAD"),
        "stash_count": len(output(repo, "stash", "list", "--format=%H").splitlines()),
        "unmerged_paths": unmerged,
        "conflict_markers": all(
            marker in notes for marker in ("<<<<<<<", "=======", ">>>>>>>")
        ),
        "draft_txt": (repo / "draft.txt").read_text(encoding="utf-8"),
        "status": output_exact(repo, "status", "--porcelain"),
    }
    expected = {
        **results["expected"]["dirty_conflicting"],
        "head": topic_test_commit,
    }
    check("dirty conflicting application state", actual, expected)
    verify_stash_kept(repo, stash_oid)
    check("conflict reports notes.txt", "notes.txt" in applied.stdout + applied.stderr, True)
    results["actual"]["scenarios"].append(
        {"name": "dirty_conflicting", "state": actual, "apply_output": applied.stderr.strip()}
    )


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
        with tempfile.TemporaryDirectory(prefix="R03-T013-") as directory:
            run_clean_cross_branch(directory)
            run_dirty_non_conflicting(directory)
            run_dirty_conflicting(directory)
    except Exception as error:
        results["failure"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        (OUTPUT_DIR / "results.json").write_text(
            json.dumps(results, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
