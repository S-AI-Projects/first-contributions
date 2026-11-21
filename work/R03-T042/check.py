#!/usr/bin/env python3
"""R03-T042: Automated verification of recovering from an unwanted commit squash.

Verifies:
1. Isolated temporary Git repository creation.
2. Reproduction of commits A, B, and C with branch `topic` at commit B:
   - A creates notes.txt with "alpha\\n"
   - B appends "beta\\n" to notes.txt
   - C adds todo.txt with "one\\n"
   - branch topic created at commit B
3. Execution of an interactive squash combining commits B and C into a squashed commit BC.
4. Recovery of original history and files using `git reset --hard ORIG_HEAD` (and reflog SHA).
5. Meaningful Git state assertions:
   - Fact 1: Recovered HEAD matches original commit C hash.
   - Fact 2: Commit history on main is restored to [C, B, A] in exact order.
   - Fact 3: Tree hash of recovered commit matches original saved pre-squash tree hash.
   - Fact 4: File contents on disk match expected pre-squash contents ("notes.txt" and "todo.txt").
   - Fact 5: Branch topic remains unchanged pointing to commit B.
   - Fact 6: Working tree is clean.
6. Verifies reproducibility across two independent temporary directory runs.
"""

import json
import os
import platform
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

AUTHOR_NAME = "Course Student"
AUTHOR_EMAIL = "student@example.invalid"
SQUASH_MSG = "Combined commits B and C\n"

COMMANDS = []
RESULTS = []

EDITOR_PY = """import sys
mode, path = sys.argv[1], sys.argv[2]
if mode == "todo":
    lines = open(path).read().splitlines(True)
    out, seen_first = [], False
    for line in lines:
        if line.startswith("pick "):
            if seen_first:
                line = "squash " + line[len("pick "):]
            seen_first = True
        out.append(line)
    open(path, "w").write("".join(out))
else:
    open(path, "w").write(%r)
""" % SQUASH_MSG


def expect(label, expected, actual):
    ok = expected == actual
    RESULTS.append({"check": label, "expected": expected, "actual": actual, "ok": ok})
    if not ok:
        raise AssertionError("%s: expected %r, got %r" % (label, expected, actual))


class Sandbox:
    """Working repo isolated from user/system git configuration."""

    def __init__(self, root: Path):
        self.root = root
        self.work = self.root / "repo"
        self.home = self.root / "home"
        self.work.mkdir(parents=True)
        self.home.mkdir(parents=True)

    def env(self, extra=None):
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
        if extra:
            env.update(extra)
        return env

    def git(self, *args, env=None, ok=(0,)):
        p = subprocess.run(["git", *args], cwd=self.work, env=self.env(env),
                           capture_output=True, text=True)
        COMMANDS.append({"cmd": "git " + " ".join(args), "returncode": p.returncode,
                         "stdout": p.stdout, "stderr": p.stderr})
        if ok is not None and p.returncode not in ok:
            raise RuntimeError("git %s failed (%d): %s" % (" ".join(args), p.returncode, p.stderr))
        return p

    def out(self, *args, env=None):
        return self.git(*args, env=env).stdout.strip()

    def lines(self, *args, env=None):
        return self.out(*args, env=env).splitlines()


def build_scenario(root: Path):
    """Sets up local repo with A, B, C, branch topic at B."""
    sb = Sandbox(root)
    sb.git("init", "-q", "-b", "main")

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
    tree_c = sb.out("rev-parse", "HEAD^{tree}")

    return sb, sha_a, sha_b, sha_c, tree_c


def verify_run(pass_num: int, tmp_path: Path):
    prefix = f"run{pass_num}"
    sb, sha_a, sha_b, sha_c, tree_c = build_scenario(tmp_path)

    # 1. Verify initial history
    expect(f"{prefix}: start history is [C, B, A]", [sha_c, sha_b, sha_a], sb.lines("rev-list", "main"))
    expect(f"{prefix}: branch topic points to commit B", sha_b, sb.out("rev-parse", "topic"))
    expect(f"{prefix}: notes.txt initial content", "alpha\nbeta\n", (sb.work / "notes.txt").read_text())
    expect(f"{prefix}: todo.txt initial content", "one\n", (sb.work / "todo.txt").read_text())

    # 2. Perform the mistake: squash commits B and C via git rebase -i HEAD~2
    editor_script = tmp_path / "editor.py"
    editor_script.write_text(EDITOR_PY)
    py_cmd = shlex.quote(sys.executable) + " " + shlex.quote(str(editor_script))
    rebase_env = {
        "GIT_SEQUENCE_EDITOR": py_cmd + " todo",
        "GIT_EDITOR": py_cmd + " msg"
    }
    sb.git("rebase", "-i", "HEAD~2", env=rebase_env)

    sha_squashed = sb.out("rev-parse", "HEAD")
    expect(f"{prefix}: squashed commit is distinct from C", False, sha_squashed == sha_c)
    expect(f"{prefix}: history now contains 2 commits [BC, A]",
           2, int(sb.out("rev-list", "--count", "main")))
    expect(f"{prefix}: commit C is no longer in rev-list", False, sha_c in sb.lines("rev-list", "main"))

    # 3. Recover the original state using git reset --hard
    if pass_num == 1:
        # Pass 1: recover via ORIG_HEAD
        orig_head = sb.out("rev-parse", "ORIG_HEAD")
        expect(f"{prefix}: ORIG_HEAD points to pre-rebase commit C", sha_c, orig_head)
        sb.git("reset", "--hard", "ORIG_HEAD")
    else:
        # Pass 2: recover via commit C SHA discovered via reflog
        reflog_lines = sb.lines("reflog", "-5")
        expect(f"{prefix}: reflog records pre-rebase commit C", True, any(sha_c[:7] in line for line in reflog_lines))
        sb.git("reset", "--hard", sha_c)

    # 4. Assert meaningful Git state facts after recovery
    # Fact 1: HEAD ref equals original commit C
    recovered_head = sb.out("rev-parse", "HEAD")
    expect(f"{prefix}: Fact 1 - HEAD points to original commit C", sha_c, recovered_head)

    # Fact 2: Entire main history is restored to [C, B, A]
    recovered_history = sb.lines("rev-list", "main")
    expect(f"{prefix}: Fact 2 - Main history is fully restored to [C, B, A]",
           [sha_c, sha_b, sha_a], recovered_history)

    # Fact 3: Tree hash of recovered commit matches saved pre-squash tree hash
    recovered_tree = sb.out("rev-parse", "HEAD^{tree}")
    expect(f"{prefix}: Fact 3 - Recovered tree hash matches pre-squash tree hash",
           tree_c, recovered_tree)

    # Fact 4: Working tree file contents match exact pre-squash contents
    expect(f"{prefix}: Fact 4a - notes.txt content matches", "alpha\nbeta\n", (sb.work / "notes.txt").read_text())
    expect(f"{prefix}: Fact 4b - todo.txt content matches", "one\n", (sb.work / "todo.txt").read_text())

    # Fact 5: Branch topic is unchanged and still points to commit B
    expect(f"{prefix}: Fact 5 - Branch topic still points to commit B", sha_b, sb.out("rev-parse", "topic"))

    # Fact 6: Working tree is completely clean
    expect(f"{prefix}: Fact 6 - Working tree status is clean", "", sb.out("status", "--porcelain"))


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T042",
        "guide": "docs/additional-material/git_workflow_scenarios/squashing-commits.md",
        "author": f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>",
        "commits": {
            "A": "create notes.txt with 'alpha\\n'",
            "B": "append 'beta\\n' to notes.txt",
            "C": "add todo.txt with 'one\\n'",
            "BC": "Accidental squash of B and C"
        },
        "recovery_method": "git reset --hard ORIG_HEAD / git reflog",
        "branches": {
            "main": "A-B-C (restored)",
            "topic": "at B (preserved)"
        },
        "passes": ["run1 (recovery via ORIG_HEAD)", "run2 (recovery via reflog commit SHA)"]
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
        with tempfile.TemporaryDirectory(prefix="r03-t042-run1-") as tmp1:
            verify_run(1, Path(tmp1))
        with tempfile.TemporaryDirectory(prefix="r03-t042-run2-") as tmp2:
            verify_run(2, Path(tmp2))
    finally:
        write_evidence()

    print(f"OK: All {len(RESULTS)} checks passed across both runs.")


if __name__ == "__main__":
    main()
