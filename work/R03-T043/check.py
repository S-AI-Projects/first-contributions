#!/usr/bin/env python3
"""R03-T043: Automated verification of branch and remote semantics when amending a commit.

Verifies:
1. Isolated temporary Git repository creation with a bare local remote.
2. Reproduction of commits A, B, and C with branch `topic` at commit B:
   - A creates notes.txt with "alpha\\n"
   - B appends "beta\\n" to notes.txt
   - C adds todo.txt with "one\\n"
   - branch topic created at commit B
   - main and topic pushed to origin
3. Switching to branch topic and amending commit B with additional content "gamma\\n".
4. Meaningful Git state assertions:
   - Fact 1: Intended ref (refs/heads/topic) changed to a new commit B'.
   - Fact 2: Unrelated ref (refs/heads/main) stayed completely fixed at commit C.
   - Fact 3: Remote main tracking ref (refs/remotes/origin/main) stayed fixed at commit C.
   - Fact 4: Remote topic tracking ref (refs/remotes/origin/topic) stayed fixed at commit B before push.
   - Fact 5: Normal git push origin topic fails with non-fast-forward rejection.
   - Fact 6: Force-push (--force-with-lease) updates origin/topic to B'.
   - Fact 7: main and origin/main remain at commit C after the force-push.
   - Fact 8: Working tree files on topic match expected amended content.
5. Verifies reproducibility across two independent temporary directory runs.
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
    """Working repo and local bare origin isolated from user/system git configuration."""

    def __init__(self, root: Path):
        self.root = root
        self.work = self.root / "local"
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
    """Sets up bare origin and working repo with A, B, C, branch topic at B, pushed to origin."""
    sb = Sandbox(root)

    # 1. Bare remote origin
    sb.git("init", "--bare", "-q", "-b", "main", str(sb.remote), cwd=sb.root)

    # 2. Local working repository
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

    # Commit C on main: add todo.txt with "one\n"
    todo = sb.work / "todo.txt"
    todo.write_text("one\n")
    sb.git("add", "todo.txt")
    sb.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit C: add todo.txt")
    sha_c = sb.out("rev-parse", "HEAD")

    # Push main and topic to origin
    sb.git("push", "-q", "-u", "origin", "main")
    sb.git("push", "-q", "-u", "origin", "topic")

    return sb, sha_a, sha_b, sha_c


def verify_run(pass_num: int, tmp_path: Path):
    prefix = f"run{pass_num}"
    sb, sha_a, sha_b, sha_c = build_scenario(tmp_path)

    # 1. Initial ref verification
    local_refs_before = sb.refs()
    expect(f"{prefix}: start refs/heads/main points to commit C", sha_c, local_refs_before.get("refs/heads/main"))
    expect(f"{prefix}: start refs/heads/topic points to commit B", sha_b, local_refs_before.get("refs/heads/topic"))
    expect(f"{prefix}: start refs/remotes/origin/main points to commit C",
           sha_c, local_refs_before.get("refs/remotes/origin/main"))
    expect(f"{prefix}: start refs/remotes/origin/topic points to commit B",
           sha_b, local_refs_before.get("refs/remotes/origin/topic"))

    # 2. Checkout topic branch
    sb.git("checkout", "-q", "topic")
    expect(f"{prefix}: checked out branch is topic", "refs/heads/topic", sb.out("symbolic-ref", "HEAD"))

    # 3. Amend the commit on topic
    notes = sb.work / "notes.txt"
    with open(notes, "a") as f:
        f.write("gamma\n")
    sb.git("add", "notes.txt")
    sb.git("-c", "commit.gpgsign=false", "commit", "--amend", "-q", "-m", "Commit B amended: beta and gamma")
    sha_b_prime = sb.out("rev-parse", "HEAD")

    # Meaningful Fact 1: Intended ref (refs/heads/topic) changed to a new commit
    expect(f"{prefix}: Fact 1a - topic tip is distinct from original B", False, sha_b_prime == sha_b)
    expect(f"{prefix}: Fact 1b - topic tip is distinct from C", False, sha_b_prime == sha_c)
    expect(f"{prefix}: Fact 1c - topic tip is distinct from A", False, sha_b_prime == sha_a)

    # Meaningful Fact 2: Unrelated ref (refs/heads/main) stayed completely fixed
    expect(f"{prefix}: Fact 2 - refs/heads/main unchanged at commit C", sha_c, sb.out("rev-parse", "refs/heads/main"))

    # Meaningful Fact 3: Remote main tracking ref stayed completely fixed
    expect(f"{prefix}: Fact 3 - origin/main unchanged at commit C", sha_c, sb.out("rev-parse", "refs/remotes/origin/main"))

    # Meaningful Fact 4: Remote topic tracking ref stayed fixed at old commit B
    expect(f"{prefix}: Fact 4 - origin/topic still at old commit B before push",
           sha_b, sb.out("rev-parse", "refs/remotes/origin/topic"))

    # Meaningful Fact 5: Normal push is rejected due to history divergence
    push_normal = sb.git("push", "origin", "topic", ok=None)
    expect(f"{prefix}: Fact 5 - normal git push origin topic fails", True, push_normal.returncode != 0)

    # Meaningful Fact 6: Force push with lease succeeds and updates origin/topic
    sb.git("push", "-q", "--force-with-lease", "origin", "topic")
    remote_topic_after = sb.refs(cwd=sb.remote).get("refs/heads/topic")
    expect(f"{prefix}: Fact 6a - origin/topic updated to amended commit B'", sha_b_prime, remote_topic_after)
    expect(f"{prefix}: Fact 6b - local tracking ref origin/topic matches B'",
           sha_b_prime, sb.out("rev-parse", "refs/remotes/origin/topic"))

    # Meaningful Fact 7: main and origin/main remained untouched after force push
    expect(f"{prefix}: Fact 7a - main still at commit C", sha_c, sb.out("rev-parse", "refs/heads/main"))
    expect(f"{prefix}: Fact 7b - origin/main still at commit C", sha_c, sb.out("rev-parse", "refs/remotes/origin/main"))

    # Meaningful Fact 8: Working tree state on topic matches expected content
    expect(f"{prefix}: Fact 8a - notes.txt content", "alpha\nbeta\ngamma\n", notes.read_text())
    expect(f"{prefix}: Fact 8b - todo.txt does not exist on topic", False, (sb.work / "todo.txt").exists())
    expect(f"{prefix}: Fact 8c - working tree is clean", "", sb.out("status", "--porcelain"))


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T043",
        "guide": "docs/additional-material/git_workflow_scenarios/amending-a-commit.md",
        "author": f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>",
        "commits": {
            "A": "create notes.txt with 'alpha\\n'",
            "B": "append 'beta\\n' to notes.txt",
            "C": "add todo.txt with 'one\\n'",
            "B_prime": "Amend commit B on branch topic with 'gamma\\n'"
        },
        "branches": {
            "main": "A-B-C (fixed at C)",
            "topic": "A-B' (amended at B')"
        },
        "remote": "local bare repository via file:// URI",
        "passes": ["run1 (independent repo 1)", "run2 (independent repo 2)"]
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
        with tempfile.TemporaryDirectory(prefix="r03-t043-run1-") as tmp1:
            verify_run(1, Path(tmp1))
        with tempfile.TemporaryDirectory(prefix="r03-t043-run2-") as tmp2:
            verify_run(2, Path(tmp2))
    finally:
        write_evidence()

    print(f"OK: All {len(RESULTS)} checks passed across both runs.")


if __name__ == "__main__":
    main()
