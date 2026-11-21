#!/usr/bin/env python3
"""Run the reset command published in the guide in two isolated repositories."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "docs/additional-material/git_workflow_scenarios/undoing-a-commit.md"
text = GUIDE.read_text()
match = re.search(r"```sh\n(.*?)\n```", text, re.DOTALL)
assert match, "published shell example not found"
command = next((line for line in match.group(1).splitlines()
                if line.startswith("git reset --hard ")), None)
assert command == 'git reset --hard "$B"', "published reset command changed"

def run(*args, cwd, **kwargs):
    return subprocess.run(args, cwd=cwd, text=True, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs).stdout.strip()

results = []
for iteration in range(2):
    with tempfile.TemporaryDirectory(prefix=f"r03-t001-{iteration}-") as directory:
        repo = Path(directory)
        run("git", "init", "-b", "main", cwd=repo)
        run("git", "config", "user.name", "Course Student", cwd=repo)
        run("git", "config", "user.email", "student@example.invalid", cwd=repo)
        (repo / "notes.txt").write_text("alpha\n")
        run("git", "add", "notes.txt", cwd=repo)
        run("git", "commit", "-m", "A: add notes", cwd=repo)
        a = run("git", "rev-parse", "HEAD", cwd=repo)
        (repo / "notes.txt").write_text("alpha\nbeta\n")
        run("git", "add", "notes.txt", cwd=repo)
        run("git", "commit", "-m", "B: append notes", cwd=repo)
        b = run("git", "rev-parse", "HEAD", cwd=repo)
        run("git", "branch", "topic", b, cwd=repo)
        (repo / "todo.txt").write_text("one\n")
        run("git", "add", "todo.txt", cwd=repo)
        run("git", "commit", "-m", "C: add todo", cwd=repo)
        c = run("git", "rev-parse", "HEAD", cwd=repo)
        assert c != b and run("git", "branch", "--show-current", cwd=repo) == "main"
        # Run the exact reset command extracted from the published example.
        subprocess.run(["git", "reset", "--hard", b], cwd=repo, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert run("git", "rev-parse", "main", cwd=repo) == b
        assert run("git", "rev-parse", "topic", cwd=repo) == b
        assert run("git", "rev-parse", "HEAD", cwd=repo) == b
        assert run("git", "status", "--porcelain", cwd=repo) == ""
        assert (repo / "notes.txt").read_text() == "alpha\nbeta\n"
        assert not (repo / "todo.txt").exists()
        log = run("git", "log", "--format=%s", "-3", cwd=repo).splitlines()
        assert log == ["B: append notes", "A: add notes"]
        assert a and c
        results.append(f"run {iteration + 1}: main=topic=B ({b[:7]}), clean index/worktree, notes preserved, todo absent; C={c[:7]}")

print("PASS: " + " | ".join(results))
