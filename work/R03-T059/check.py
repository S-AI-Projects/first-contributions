#!/usr/bin/env python3
"""R03-T059: worked exercise "reset a branch" -- predict, execute, explain.

Fixture (temporary repository, no remote needed):

    main : A --- B --- C          A creates notes.txt ("alpha\\n")
                \\                 B appends "beta\\n"
    topic:       B                C adds todo.txt ("one\\n")

Exercise: HEAD is on `topic`; notes.txt has an uncommitted edit and
scratch.txt is untracked.  Reset `topic` to `main`:

    git reset --hard main

The expected state is PREDICTED from the fixture before the command runs and
then compared with the real state afterwards.  The guide's literal syntax
(`git reset <base_branch> <origin_branch> --hard`) is also run to show that it
is rejected and changes nothing.

Run:  python3 work/R03-T059/check.py      (exit code != 0 on any failure)
Evidence is written next to this file.
"""
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "Course Student"
EMAIL = "student@example.invalid"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def make_env(home: Path) -> dict:
    """Isolated environment: no user/system git config, fixed identity."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        HOME=str(home),
        XDG_CONFIG_HOME=str(home / ".config"),
        GIT_CONFIG_NOSYSTEM="1",
        GIT_PAGER="cat",
        GIT_AUTHOR_NAME=NAME,
        GIT_AUTHOR_EMAIL=EMAIL,
        GIT_COMMITTER_NAME=NAME,
        GIT_COMMITTER_EMAIL=EMAIL,
        LC_ALL="C",
    )
    return env


def git(repo: Path, env: dict, *args: str) -> str:
    """Run git, raising CalledProcessError on a non-zero exit code."""
    result = subprocess.run(
        ["git", *args], cwd=repo, env=env, check=True,
        capture_output=True, text=True,
    )
    return result.stdout


def dated(env: dict, n: int) -> dict:
    """Fixed, increasing timestamps => deterministic order and commit IDs."""
    stamp = f"2026-01-01T00:00:0{n} +0000"
    return dict(env, GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp)


def build_fixture(repo: Path, env: dict) -> dict:
    """A, B, C on main; topic at B; HEAD on topic; dirty worktree."""
    repo.mkdir()
    git(repo, env, "init", "-q", "-b", "main")
    ids = {}

    (repo / "notes.txt").write_text("alpha\n")
    git(repo, env, "add", "notes.txt")
    git(repo, dated(env, 1), "commit", "-q", "-m", "A: create notes.txt")
    ids["A"] = git(repo, env, "rev-parse", "HEAD").strip()

    with open(repo / "notes.txt", "a") as fh:
        fh.write("beta\n")
    git(repo, env, "add", "notes.txt")
    git(repo, dated(env, 2), "commit", "-q", "-m", "B: append beta")
    ids["B"] = git(repo, env, "rev-parse", "HEAD").strip()

    git(repo, env, "branch", "topic")  # topic points at B

    (repo / "todo.txt").write_text("one\n")
    git(repo, env, "add", "todo.txt")
    git(repo, dated(env, 3), "commit", "-q", "-m", "C: add todo.txt")
    ids["C"] = git(repo, env, "rev-parse", "HEAD").strip()

    git(repo, env, "checkout", "-q", "topic")

    # exercise set-up: one tracked-but-uncommitted edit, one untracked file
    with open(repo / "notes.txt", "a") as fh:
        fh.write("gamma (uncommitted)\n")
    (repo / "scratch.txt").write_text("scratch\n")
    return ids


def refs(repo: Path, env: dict) -> dict:
    out = git(repo, env, "for-each-ref", "--format=%(refname) %(objectname)")
    return dict(line.split(" ", 1) for line in out.splitlines())


def worktree(repo: Path) -> dict:
    return {p.name: p.read_text() for p in sorted(repo.iterdir())
            if p.name != ".git" and p.is_file()}


def state(repo: Path, env: dict) -> dict:
    return {
        "head": git(repo, env, "symbolic-ref", "HEAD").strip(),
        "refs": refs(repo, env),
        "index_tree": git(repo, env, "write-tree").strip(),
        "worktree": worktree(repo),
        "status": git(repo, env, "status", "--porcelain").splitlines(),
    }


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------
def run_checks(expect, evidence: dict) -> None:
    with tempfile.TemporaryDirectory(prefix="r03-t059-") as tmp_name:
        tmp = Path(tmp_name)
        home = tmp / "home"
        home.mkdir()
        env = make_env(home)

        repo = tmp / "repo"
        ids = build_fixture(repo, env)
        A, B, C = ids["A"], ids["B"], ids["C"]
        tree_c = git(repo, env, "rev-parse", f"{C}^{{tree}}").strip()
        evidence["commit_ids_this_run"] = ids

        # -- 1. starting point ---------------------------------------------
        before = state(repo, env)
        expect("start: HEAD is on topic", "refs/heads/topic", before["head"])
        expect("start: topic is at B, main is at C",
               {"refs/heads/main": C, "refs/heads/topic": B}, before["refs"])
        expect("start: notes.txt has the uncommitted edit",
               "alpha\nbeta\ngamma (uncommitted)\n",
               before["worktree"]["notes.txt"])
        expect("start: status shows the edit and the untracked file",
               [" M notes.txt", "?? scratch.txt"], before["status"])
        expect("start: author of every commit",
               [f"{NAME} <{EMAIL}>"] * 3,
               git(repo, env, "log", "main", "--format=%an <%ae>").splitlines())

        # -- 2. PREDICT (computed before running the command) ---------------
        predicted = {
            "head": "refs/heads/topic",                       # still on topic
            "refs": {"refs/heads/main": C, "refs/heads/topic": C},
            "changed_refs": {"refs/heads/topic": [B, C]},     # only topic moves
            "index_tree": tree_c,                             # index == C
            "worktree": {"notes.txt": "alpha\nbeta\n",        # edit discarded
                         "todo.txt": "one\n",                 # C's file appears
                         "scratch.txt": "scratch\n"},         # untracked survives
            "status": ["?? scratch.txt"],
            "orig_head": B,                                   # old tip is kept
        }
        evidence["prediction"] = predicted

        # -- 3. the guide's literal syntax is rejected and changes nothing --
        literal = subprocess.run(
            ["git", "reset", "topic", "main", "--hard"], cwd=repo, env=env,
            capture_output=True, text=True)
        expect("guide syntax `git reset topic main --hard` exits 128",
               128, literal.returncode)
        expect("...with 'Cannot do hard reset with paths'", True,
               "Cannot do hard reset with paths" in literal.stderr)
        expect("...and refs, index, worktree are unchanged",
               before, state(repo, env))

        # -- 4. EXECUTE ------------------------------------------------------
        git(repo, env, "reset", "--hard", "main")

        # -- 5. compare with the prediction ----------------------------------
        after = state(repo, env)
        changed = {name: [before["refs"][name], after["refs"][name]]
                   for name in after["refs"]
                   if before["refs"][name] != after["refs"][name]}
        expect("ref moved: only refs/heads/topic changed, B -> C",
               predicted["changed_refs"], changed)
        expect("refs: topic and main both point at C",
               predicted["refs"], after["refs"])
        expect("HEAD still on topic", predicted["head"], after["head"])
        expect("index tree equals the tree of C",
               predicted["index_tree"], after["index_tree"])
        expect("worktree: edit discarded, todo.txt added, scratch.txt kept",
               predicted["worktree"], after["worktree"])
        expect("status shows only the untracked file",
               predicted["status"], after["status"])
        expect("ORIG_HEAD keeps the old tip (B)",
               predicted["orig_head"],
               git(repo, env, "rev-parse", "ORIG_HEAD").strip())
        expect("topic's reflog records the reset",
               "reset: moving to main",
               git(repo, env, "reflog", "show", "topic",
                   "--format=%gs").splitlines()[0])
        evidence["explanation"] = (
            f"git reset --hard main, run while topic was checked out, moved "
            f"refs/heads/topic from {B} (B) to {C} (C) and made the index and "
            f"worktree match C's tree {tree_c}. refs/heads/main did not move.")


def tool_versions() -> str:
    git_v = subprocess.run(["git", "--version"], check=True,
                           capture_output=True, text=True).stdout.strip()
    return "\n".join([git_v,
                      f"Python {platform.python_version()}",
                      f"OS {platform.platform()}"]) + "\n"


def main() -> int:
    rows = []
    evidence = {}
    inputs = {
        "author": f"{NAME} <{EMAIL}>",
        "branch": "main",
        "commits": {
            "A": "create notes.txt with 'alpha\\n'",
            "B": "append 'beta\\n' to notes.txt",
            "C": "add todo.txt with 'one\\n'",
        },
        "extra_branch": "topic at B",
        "exercise_setup": ["git checkout topic",
                           "append 'gamma (uncommitted)' to notes.txt (not staged)",
                           "create untracked scratch.txt"],
        "operation": "git reset --hard main  (run on topic)",
        "also_run": "git reset topic main --hard  (the guide's literal form)",
        "remote": "not needed (reset works on local refs)",
    }

    def expect(name, expected, actual):
        ok = expected == actual
        rows.append({"check": name, "expected": expected, "actual": actual,
                     "ok": ok})
        assert ok, f"{name}\n  expected: {expected!r}\n  actual:   {actual!r}"

    try:
        run_checks(expect, evidence)
    finally:  # evidence is saved even when an assertion fails
        (HERE / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
        (HERE / "expected_vs_actual.json").write_text(
            json.dumps({"checks": rows, **evidence}, indent=2) + "\n")
        (HERE / "tool_versions.txt").write_text(tool_versions())

    print(f"OK: {len(rows)} checks passed (evidence in {HERE})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
