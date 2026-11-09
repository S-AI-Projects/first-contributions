#!/usr/bin/env python3
"""R03-T051: verify what `git log` does (and does not) change.

Builds a throwaway repository (branch main: A -> B -> C, branch topic at B),
runs several `git log` invocations, and asserts the resulting refs, commit
ancestry, index and working-tree state. Exits non-zero if any check fails.

Evidence (inputs, expected vs actual, tool versions) is written to
evidence.json next to this script.

Set R03_T051_FORCE_FAIL=1 to see a deliberate failure (proves the exit code).
"""
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTHOR = "Course Student <student@example.invalid>"
RESULTS = []
INPUTS = []


def expect(name, expected, actual):
    ok = expected == actual
    RESULTS.append({"check": name, "expected": expected, "actual": actual, "ok": ok})
    print(("PASS  " if ok else "FAIL  ") + name)
    if not ok:
        print(f"      expected: {expected!r}\n      actual:   {actual!r}")
    return ok


def make_git(repo, env):
    def git(*args, record=True):
        if record:
            cmd = "git " + " ".join(args)
            if cmd not in INPUTS:
                INPUTS.append(cmd)
        proc = subprocess.run(
            ["git", *args], cwd=repo, env=env,
            capture_output=True, text=True, check=True,
        )
        return proc.stdout
    return git


def snapshot(git, repo):
    """Everything `git log` must leave alone: refs, HEAD, reflog, index, worktree, objects."""
    return {
        "head_symref": git("symbolic-ref", "HEAD", record=False).strip(),
        "head_sha": git("rev-parse", "HEAD", record=False).strip(),
        "refs": git("for-each-ref", "--format=%(refname) %(objectname)", record=False),
        "head_reflog": git("reflog", "show", "HEAD", record=False),
        "status": git("status", "--porcelain=v1", "--branch", record=False),
        "index": git("ls-files", "--stage", record=False),
        "worktree": {p.name: p.read_text() for p in sorted(repo.iterdir()) if p.is_file()},
        "objects": git("count-objects", "-v", record=False),
    }


LOG_VARIANTS = [
    ["log"],
    ["log", "--oneline"],
    ["log", "--graph", "--oneline", "--all", "--decorate"],
    ["log", "--stat"],
    ["log", "-p"],
    ["log", "topic"],
    ["log", "topic..main"],
    ["log", "--author=student@example.invalid"],
]


def run_all_log_variants(git, label):
    """Run every log variant; each must succeed (check=True) and print something."""
    printed = {" ".join(args): bool(git(*args).strip()) for args in LOG_VARIANTS}
    expect(f"{label}: all {len(LOG_VARIANTS)} `git log` variants run and print output",
           {k: True for k in printed}, printed)


def main():
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        repo = tmp / "repo"
        repo.mkdir()
        env = {
            **os.environ,
            "HOME": str(tmp),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Course Student",
            "GIT_AUTHOR_EMAIL": "student@example.invalid",
            "GIT_COMMITTER_NAME": "Course Student",
            "GIT_COMMITTER_EMAIL": "student@example.invalid",
        }
        git = make_git(repo, env)

        # ---- build the fixture: A, B, C on main; topic at B -----------------
        git("init", "-b", "main")
        git("config", "commit.gpgsign", "false")

        def commit(msg, minute):
            stamp = f"2026-01-01T00:0{minute}:00+00:00"
            e = {**env, "GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}
            subprocess.run(["git", "commit", "-q", "-m", msg], cwd=repo, env=e,
                           capture_output=True, text=True, check=True)
            INPUTS.append(f'git commit -m "{msg}"')
            return git("rev-parse", "HEAD", record=False).strip()

        (repo / "notes.txt").write_text("alpha\n")
        git("add", "notes.txt")
        A = commit("A: create notes.txt", 1)

        with open(repo / "notes.txt", "a") as fh:
            fh.write("beta\n")
        git("add", "notes.txt")
        B = commit("B: append beta", 2)

        (repo / "todo.txt").write_text("one\n")
        git("add", "todo.txt")
        C = commit("C: add todo.txt", 3)

        git("branch", "topic", B)

        # ---- state BEFORE running git log (clean tree) -----------------------
        expect("HEAD is a symbolic ref to refs/heads/main",
               "refs/heads/main", git("symbolic-ref", "HEAD").strip())
        expect("branch main points at C", C, git("rev-parse", "main").strip())
        expect("branch topic points at B", B, git("rev-parse", "topic").strip())
        expect("C's parent is B", B, git("rev-parse", C + "^").strip())
        expect("B's parent is A", A, git("rev-parse", B + "^").strip())
        expect("A is a root commit (no parents)", [A],
               git("rev-list", "--parents", "-n1", A).split())
        expect("working tree is clean before the first log",
               "## main\n", git("status", "--porcelain=v1", "--branch"))

        # ---- the operation under test: git log (clean tree) ------------------
        before_clean = snapshot(git, repo)

        order = [C, B, A]
        if os.environ.get("R03_T051_FORCE_FAIL"):
            order = order[::-1]  # deliberate failure to prove a non-zero exit
        expect("`git log` on main lists C, B, A (newest first)",
               order, git("log", "--format=%H").split())
        expect("`git log topic` lists only B, A",
               [B, A], git("log", "--format=%H", "topic").split())
        expect("`git log main..topic` is empty (topic has nothing main lacks)",
               [], git("log", "--format=%H", "main..topic").split())
        expect("`git log topic..main` is exactly C",
               [C], git("log", "--format=%H", "topic..main").split())
        expect("all three commits carry the course author",
               [AUTHOR] * 3, git("log", "--format=%an <%ae>").splitlines())
        expect("--author filter keeps all three commits",
               [C, B, A], git("log", "--author=student@example.invalid", "--format=%H").split())
        expect("--oneline shows abbreviated ids newest first",
               [git("rev-parse", "--short", s).strip() for s in (C, B, A)],
               [line.split()[0] for line in git("log", "--oneline").splitlines()])

        # the guide's "variations and options" claims, run against the fixture
        expect("`git log main topic ^A` (two refs, one excluded) lists C, B",
               [C, B], git("log", "--format=%H", "main", "topic", "^" + A).split())
        expect("`git log -n 2` limits the output to the newest two commits",
               [C, B], git("log", "-n", "2", "--format=%H").split())
        expect("`git log -- notes.txt` lists only commits that touched notes.txt",
               [B, A], git("log", "--format=%H", "--", "notes.txt").split())
        expect("`git log --all -- todo.txt` lists only C (--all = all refs, path after --)",
               [C], git("log", "--all", "--format=%H", "--", "todo.txt").split())

        decorations = {}
        for line in git("log", "--format=%H|%D").splitlines():
            sha, _, deco = line.partition("|")
            decorations[sha] = deco
        expect("decorations: HEAD -> main on C, topic on B, nothing on A",
               {C: "HEAD -> main", B: "topic", A: ""}, decorations)

        def changes(sha):
            out = git("log", "-n1", "--name-status", "--format=%H", sha).splitlines()
            return [ln for ln in out if ln and ln != sha]

        expect("A's diff: adds notes.txt", ["A\tnotes.txt"], changes(A))
        expect("B's diff: modifies notes.txt", ["M\tnotes.txt"], changes(B))
        expect("C's diff: adds todo.txt", ["A\ttodo.txt"], changes(C))
        patch_b = git("log", "-n1", "-p", "--format=", B).splitlines()
        expect("B's patch adds the line 'beta' and removes nothing",
               (True, False), ("+beta" in patch_b, any(l.startswith("-") and not l.startswith("---") for l in patch_b)))

        run_all_log_variants(git, "clean tree")

        after_clean = snapshot(git, repo)
        expect("clean tree: refs, HEAD, reflog, index, worktree and object store unchanged by git log",
               before_clean, after_clean)

        # ---- dirty tree: staged change in one file, unstaged in another ------
        (repo / "todo.txt").write_text("one\ntwo\n")
        git("add", "todo.txt")
        (repo / "notes.txt").write_text("alpha\nbeta\nunstaged\n")

        expect("status separates staged (todo.txt) from unstaged (notes.txt)",
               ["## main", " M notes.txt", "M  todo.txt"],
               git("status", "--porcelain=v1", "--branch").splitlines())
        expect("index blob of todo.txt differs from HEAD (staged)", True,
               git("rev-parse", ":todo.txt").strip() != git("rev-parse", "HEAD:todo.txt").strip())
        expect("index blob of notes.txt equals HEAD (not staged)", True,
               git("rev-parse", ":notes.txt").strip() == git("rev-parse", "HEAD:notes.txt").strip())
        expect("working-tree notes.txt differs from the index", True,
               git("hash-object", "notes.txt").strip() != git("rev-parse", ":notes.txt").strip())

        before_dirty = snapshot(git, repo)
        run_all_log_variants(git, "dirty tree")
        expect("`git log` still lists exactly three commits with a dirty tree",
               [C, B, A], git("log", "--format=%H").split())
        after_dirty = snapshot(git, repo)
        expect("dirty tree: staged and unstaged edits and every ref survive git log untouched",
               before_dirty, after_dirty)

        # ---- negative control: prove the snapshot would notice a real change ----
        before_control = snapshot(git, repo)
        git("branch", "probe")  # creating a ref is a change; git log never does this
        expect("control: creating a branch IS detected by the snapshot comparison",
               False, before_control == snapshot(git, repo))

    # ---- evidence ------------------------------------------------------------
    git_version = subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip()
    evidence = {
        "task": "R03-T051",
        "tool_versions": {"git": git_version, "python": platform.python_version(), "platform": platform.platform()},
        "inputs": INPUTS,
        "results": RESULTS,
    }
    (HERE / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")

    failed = [r["check"] for r in RESULTS if not r["ok"]]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
