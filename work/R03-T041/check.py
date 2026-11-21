#!/usr/bin/env python3
"""R03-T041: Automated verification of reproducible `git rm --cached` example.

Verifies:
1. Isolated temporary Git repository creation with bare origin remote.
2. Reproduction of commits A, B, and C with branch `topic` at commit B:
   - A creates notes.txt with "alpha\\n"
   - B appends "beta\\n" to notes.txt
   - C adds todo.txt with "one\\n"
   - branch topic created at commit B
3. Execution of `git rm --cached todo.txt`.
4. Meaningful Git state assertions:
   - Fact 1: File is removed from the Git index (staging area).
   - Fact 2: File remains present in the local filesystem with identical content.
   - Fact 3: Staged status shows deletion (`D  todo.txt`), untracked status shows `?? todo.txt`.
   - Fact 4: Commit creates a new commit object whose tree omits the untracked file.
   - Fact 5: Pushing to remote origin updates remote tracking branch, removing the file on remote.
   - Fact 6: Branch `topic` and other repository refs remain completely untouched.
5. Verifies reproducibility by running two independent passes in separate temporary directories.
"""

import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

AUTHOR_NAME = "Course Student"
AUTHOR_EMAIL = "student@example.invalid"

COMMANDS = []
RESULTS = []


def expect(label, expected, actual):
    ok = expected == actual
    RESULTS.append({"check": label, "expected": expected, "actual": actual, "ok": ok})
    if not ok:
        raise AssertionError("%s: expected %r, got %r" % (label, expected, actual))


class Sandbox:
    """A working repo + bare origin, isolated from user/system git configuration."""

    def __init__(self, root: Path):
        self.root = root
        self.work = self.root / "work"
        self.remote = self.root / "remote.git"
        self.home = self.root / "home"
        self.work.mkdir(parents=True)
        self.home.mkdir(parents=True)

    def env(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "EMAIL"}
        env.update({
            "HOME": str(self.home),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": AUTHOR_NAME,
            "GIT_AUTHOR_EMAIL": AUTHOR_EMAIL,
            "GIT_COMMITTER_NAME": AUTHOR_NAME,
            "GIT_COMMITTER_EMAIL": AUTHOR_EMAIL,
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        })
        return env

    def git(self, *args, cwd=None, ok=(0,)):
        p = subprocess.run(["git", *args], cwd=cwd or self.work, env=self.env(),
                           capture_output=True, text=True)
        COMMANDS.append({"cmd": "git " + " ".join(args), "returncode": p.returncode,
                         "stdout": p.stdout, "stderr": p.stderr})
        if ok is not None and p.returncode not in ok:
            raise RuntimeError("git %s failed (%d): %s" % (" ".join(args), p.returncode, p.stderr))
        return p

    def out(self, *args, cwd=None):
        return self.git(*args, cwd=cwd).stdout.strip()

    def lines(self, *args, cwd=None):
        return self.out(*args, cwd=cwd).splitlines()

    def refs(self, cwd=None):
        rows = self.lines("for-each-ref", "--format=%(refname) %(objectname)", cwd=cwd)
        return dict(r.split(" ", 1) for r in rows)


def build_scenario(root: Path):
    """Sets up bare remote and local repo with A, B, C, branch topic at B, pushed to origin."""
    sb = Sandbox(root)

    # 1. Initialize bare remote repository
    sb.git("init", "--bare", "-q", "-b", "main", str(sb.remote), cwd=sb.root)

    # 2. Initialize working repository with default branch main
    sb.git("init", "-q", "-b", "main")
    sb.git("remote", "add", "origin", sb.remote.resolve().as_uri())

    # Commit A: create notes.txt with "alpha\n"
    notes = sb.work / "notes.txt"
    notes.write_text("alpha\n")
    sb.git("add", "notes.txt")
    sb.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit A: create notes.txt")
    sha_a = sb.out("rev-parse", "HEAD")

    # Commit B: append "beta\n" to notes.txt
    with open(notes, "a") as f:
        f.write("beta\n")
    sb.git("add", "notes.txt")
    sb.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit B: append beta to notes.txt")
    sha_b = sb.out("rev-parse", "HEAD")

    # Branch topic at Commit B
    sb.git("branch", "topic", sha_b)

    # Commit C: create todo.txt with "one\n"
    todo = sb.work / "todo.txt"
    todo.write_text("one\n")
    sb.git("add", "todo.txt")
    sb.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit C: add todo.txt")
    sha_c = sb.out("rev-parse", "HEAD")

    # Push main to origin
    sb.git("push", "-q", "-u", "origin", "main")

    return sb, sha_a, sha_b, sha_c


def verify_run(pass_num: int, tmp_path: Path):
    prefix = f"run{pass_num}"
    sb, sha_a, sha_b, sha_c = build_scenario(tmp_path)

    # 1. Verify initial repository state
    expect(f"{prefix}: commit A is ancestor of B", 0,
           sb.git("merge-base", "--is-ancestor", sha_a, sha_b, ok=None).returncode)
    expect(f"{prefix}: commit B is ancestor of C", 0,
           sb.git("merge-base", "--is-ancestor", sha_b, sha_c, ok=None).returncode)
    expect(f"{prefix}: branch topic points to commit B", sha_b, sb.out("rev-parse", "topic"))
    expect(f"{prefix}: branch main points to commit C", sha_c, sb.out("rev-parse", "main"))
    expect(f"{prefix}: origin/main points to commit C", sha_c, sb.out("rev-parse", "origin/main"))
    expect(f"{prefix}: notes.txt content before removal", "alpha\nbeta\n", (sb.work / "notes.txt").read_text())
    expect(f"{prefix}: todo.txt content before removal", "one\n", (sb.work / "todo.txt").read_text())
    expect(f"{prefix}: working tree is clean before removal", "", sb.out("status", "--porcelain"))

    # 2. Execute git rm --cached todo.txt
    rm_proc = sb.git("rm", "--cached", "todo.txt")
    expect(f"{prefix}: git rm --cached todo.txt exits 0", 0, rm_proc.returncode)

    # Meaningful Fact 1: File is removed from the Git index (staging area)
    ls_files = sb.git("ls-files", "--error-unmatch", "todo.txt", ok=None)
    expect(f"{prefix}: Fact 1 - todo.txt is removed from index", 1, ls_files.returncode)
    diff_cached = sb.lines("diff", "--cached", "--name-only")
    expect(f"{prefix}: Fact 1b - staged diff contains todo.txt deletion", ["todo.txt"], diff_cached)

    # Meaningful Fact 2: File remains present on disk with untouched content
    expect(f"{prefix}: Fact 2 - todo.txt exists on disk", True, (sb.work / "todo.txt").is_file())
    expect(f"{prefix}: Fact 2b - todo.txt content is preserved", "one\n", (sb.work / "todo.txt").read_text())

    # Meaningful Fact 3: Porcelain status shows staged deletion (D ) and untracked (??)
    status_lines = sorted(sb.lines("status", "--porcelain"))
    expect(f"{prefix}: Fact 3 - status shows staged deletion and untracked file",
           ["?? todo.txt", "D  todo.txt"], status_lines)

    # 3. Commit the removal
    sb.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Remove todo.txt from repository")
    sha_d = sb.out("rev-parse", "HEAD")

    # Meaningful Fact 4: New commit created; tree contains notes.txt but NOT todo.txt
    expect(f"{prefix}: Fact 4a - commit D is distinct from C", False, sha_d == sha_c)
    tree_files = sb.lines("ls-tree", "--name-only", "HEAD")
    expect(f"{prefix}: Fact 4b - HEAD commit tree contains only notes.txt", ["notes.txt"], tree_files)
    expect(f"{prefix}: Fact 4c - todo.txt still exists on disk after commit", True, (sb.work / "todo.txt").is_file())

    # Meaningful Fact 5: Push to remote origin
    sb.git("push", "-q", "origin", "main")
    remote_main_ref = sb.refs(cwd=sb.remote).get("refs/heads/main")
    expect(f"{prefix}: Fact 5a - remote main ref matches commit D", sha_d, remote_main_ref)
    remote_tree_files = sb.lines("ls-tree", "--name-only", "main", cwd=sb.remote)
    expect(f"{prefix}: Fact 5b - remote main tree does not contain todo.txt", ["notes.txt"], remote_tree_files)

    # Meaningful Fact 6: Branch topic remained completely unchanged
    expect(f"{prefix}: Fact 6 - topic branch still points to commit B", sha_b, sb.out("rev-parse", "topic"))


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T041",
        "guide": "docs/additional-material/git_workflow_scenarios/removing-a-file.md",
        "author": f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>",
        "commits": {
            "A": "create notes.txt with 'alpha\\n'",
            "B": "append 'beta\\n' to notes.txt",
            "C": "add todo.txt with 'one\\n'",
            "D": "Remove todo.txt from repository (via git rm --cached todo.txt)"
        },
        "branches": {
            "main": "A-B-C-D",
            "topic": "at B (preserved)"
        },
        "remote": "local bare repository via file:// URI",
        "passes": ["run1 (temporary directory 1)", "run2 (temporary directory 2)"]
    }
    (HERE / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")

    rows = ["| check | expected | actual | ok |", "|---|---|---|---|"]
    for r in RESULTS:
        rows.append("| %s | `%s` | `%s` | %s |" % (
            r["check"], json.dumps(r["expected"]), json.dumps(r["actual"]), "yes" if r["ok"] else "NO"))
    (HERE / "expected_vs_actual.md").write_text("\n".join(rows) + "\n")

    log = []
    for c in COMMANDS:
        log.append("$ %s\n[exit %d]\n%s%s" % (c["cmd"], c["returncode"], c["stdout"], c["stderr"]))
    (HERE / "commands.log").write_text("\n".join(log))


def main():
    try:
        with tempfile.TemporaryDirectory(prefix="r03-t041-run1-") as tmp1:
            verify_run(1, Path(tmp1))
        with tempfile.TemporaryDirectory(prefix="r03-t041-run2-") as tmp2:
            verify_run(2, Path(tmp2))
    finally:
        write_evidence()

    print(f"OK: All {len(RESULTS)} checks passed across both runs.")


if __name__ == "__main__":
    main()
