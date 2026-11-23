#!/usr/bin/env python3
"""Verify that `git config credential.helper ...` changes only .git/config.

Builds a temporary repo: main with commits A, B, C; branch topic at B.
Snapshots HEAD, refs, index, and working tree before and after the config
operation, then asserts only the config value changed. Exits non-zero on failure.
"""
import os
import subprocess
import sys
import tempfile

ENV = dict(os.environ,
           GIT_AUTHOR_NAME="Course Student", GIT_AUTHOR_EMAIL="student@example.invalid",
           GIT_COMMITTER_NAME="Course Student", GIT_COMMITTER_EMAIL="student@example.invalid")


def git(repo, *args, check=True):
    res = subprocess.run(["git", *args], cwd=repo, env=ENV,
                         capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {res.stderr}")
    return res.stdout.strip()


def snapshot(repo):
    return {
        "HEAD": git(repo, "rev-parse", "HEAD"),
        "symbolic-ref": git(repo, "symbolic-ref", "HEAD"),
        "refs": git(repo, "for-each-ref", "--format=%(refname) %(objectname)"),
        "index": git(repo, "ls-files", "--stage"),
        "worktree": git(repo, "status", "--porcelain"),
        "files": sorted(os.listdir(repo)),
    }


def build_repo(repo):
    git(repo, "init", "-q", "-b", "main")
    with open(os.path.join(repo, "notes.txt"), "w") as f:
        f.write("alpha\n")
    git(repo, "add", "notes.txt"); git(repo, "commit", "-q", "-m", "A")
    a = git(repo, "rev-parse", "HEAD")
    with open(os.path.join(repo, "notes.txt"), "a") as f:
        f.write("beta\n")
    git(repo, "commit", "-qam", "B")
    b = git(repo, "rev-parse", "HEAD")
    with open(os.path.join(repo, "todo.txt"), "w") as f:
        f.write("one\n")
    git(repo, "add", "todo.txt"); git(repo, "commit", "-q", "-m", "C")
    git(repo, "branch", "topic", b)
    return a, b


def main():
    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {name}" + (f" -- {detail}" if detail and not cond else ""))
        if not cond:
            failures.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, "work")
        os.makedirs(repo)
        a, b = build_repo(repo)
        c = git(repo, "rev-parse", "HEAD")

        # Fact 1: ancestry and branch placement are as described.
        check("topic points at B", git(repo, "rev-parse", "topic") == b)
        check("main is at C", git(repo, "rev-parse", "main") == c)
        ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", b, c], cwd=repo).returncode == 0
        check("B is ancestor of C", ancestor)

        before = snapshot(repo)

        # The operation under study (repo-local, so the host's global config is untouched).
        git(repo, "config", "credential.helper", "cache")
        git(repo, "config", "credential.helper", "cache --timeout=900")  # second anchor form
        helper = git(repo, "config", "--get", "credential.helper")
        after = snapshot(repo)

        # Facts 2-5: refs, ancestry, index and working tree are unchanged.
        check("HEAD unchanged", before["HEAD"] == after["HEAD"])
        check("HEAD still symbolic ref to main", after["symbolic-ref"] == "refs/heads/main")
        check("all refs unchanged", before["refs"] == after["refs"])
        check("index unchanged", before["index"] == after["index"])
        check("working tree clean and unchanged", before["worktree"] == after["worktree"] == "")
        check("no new files in worktree", before["files"] == after["files"])

        # Fact 6: the only change is the stored value in .git/config.
        check("credential.helper stored with timeout", helper == "cache --timeout=900", helper)
        check("config lives in .git/config",
              "helper = cache --timeout=900" in open(os.path.join(repo, ".git", "config")).read())

        # Fact 7: commit A content is recoverable from history (sanity).
        check("notes.txt at B has alpha and beta",
              git(repo, "show", f"{b}:notes.txt") == "alpha\nbeta")

    print(f"\n{len(failures)} failure(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
