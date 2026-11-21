"""
R03-T050 Verification Script
Task: Show the Git state transition in installing-git-ubuntu.md

Checks:
  A. Guide content — section heading, table, stages, reproducible walkthrough
  B. Live git state transitions using a temporary repository
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

GUIDE = os.path.join(
    os.path.dirname(__file__),
    "../../docs/additional-material/git_workflow_scenarios/installing-git-ubuntu.md",
)

passes = 0
fails = 0


def ok(msg):
    global passes
    passes += 1
    print(f"  PASS  {msg}")


def fail(msg):
    global fails
    fails += 1
    print(f"  FAIL  {msg}")


def check(condition, msg):
    if condition:
        ok(msg)
    else:
        fail(msg)


# ── A. Guide content checks ────────────────────────────────────────────────

print("\n── A. Guide content ──")

with open(GUIDE, encoding="utf-8") as fh:
    content = fh.read()

check("Git State Transition" in content,
      "Guide contains 'Git State Transition' section heading")

check("Stage 1" in content and "Stage 6" in content,
      "Guide covers Stage 1 through Stage 6")

check("before Git is installed" in content.lower() or
      "before git is installed" in content.lower(),
      "Stage 1 describes state before Git is installed")

check("command not found" in content,
      "Stage 1 shows 'command not found' error")

check("git init" in content,
      "Guide mentions 'git init'")

check("No commits yet" in content,
      "Guide shows 'No commits yet' status after git init")

check("Changes to be committed" in content,
      "Guide shows 'Changes to be committed' status after git add")

check("nothing to commit, working tree clean" in content,
      "Guide shows clean state after first commit")

check("HEAD" in content,
      "Guide references HEAD")

check(re.search(r"unborn", content),
      "Guide mentions unborn branch concept")

check(re.search(r"\| *Stage *\|", content),
      "Guide contains a state transition summary table")

check(re.search(r"Reproducible", content),
      "Guide contains reproducible walkthrough section")

check("notes.txt" in content,
      "Guide uses notes.txt in example")

check(re.search(r"commit A", content),
      "Guide labels first commit as 'commit A'")

check(re.search(r"git log --oneline", content),
      "Guide shows git log --oneline")

check(re.search(r"git status", content),
      "Guide shows git status at multiple stages")

# ── B. Live git state transition verification ──────────────────────────────

print("\n── B. Live git state transitions ──")

tmpdir = tempfile.mkdtemp(prefix="r03t050_")

try:
    # Git must be available
    result = subprocess.run(["git", "--version"], capture_output=True, text=True)
    check(result.returncode == 0 and "git version" in result.stdout,
          "git binary is available (installation confirmed)")

    # --- init ---
    repo = os.path.join(tmpdir, "repo")
    os.makedirs(repo)
    env = os.environ.copy()
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["HOME"] = tmpdir

    # Write a minimal global config so commits work
    global_cfg = os.path.join(tmpdir, ".gitconfig")
    with open(global_cfg, "w") as f:
        f.write("[user]\n\tname = Course Student\n\temail = student@example.invalid\n")

    r = subprocess.run(["git", "init", repo], capture_output=True, text=True, env=env)
    check(r.returncode == 0, "git init succeeds in a new directory")
    check(os.path.isdir(os.path.join(repo, ".git")),
          ".git directory created by git init")

    # --- status after init (no commits yet) ---
    r = subprocess.run(
        ["git", "status"], capture_output=True, text=True, cwd=repo, env=env
    )
    check("No commits yet" in r.stdout,
          "git status shows 'No commits yet' on unborn branch (Stage 4)")

    default_branch = None
    for line in r.stdout.splitlines():
        m = re.match(r"On branch (\S+)", line)
        if m:
            default_branch = m.group(1)
            break
    check(default_branch is not None,
          f"Default branch name detected: '{default_branch}'")

    # --- add file (Stage 5) ---
    notes = os.path.join(repo, "notes.txt")
    with open(notes, "w") as f:
        f.write("alpha\n")
    subprocess.run(["git", "add", "notes.txt"], cwd=repo, env=env, check=True)

    r = subprocess.run(
        ["git", "status"], capture_output=True, text=True, cwd=repo, env=env
    )
    check("Changes to be committed" in r.stdout,
          "git status shows 'Changes to be committed' after git add (Stage 5)")
    check("new file:   notes.txt" in r.stdout,
          "notes.txt listed as new file in staged changes")

    # --- first commit (Stage 6) ---
    r = subprocess.run(
        ["git", "commit", "-m", "commit A: add notes.txt"],
        capture_output=True, text=True, cwd=repo, env=env,
    )
    check(r.returncode == 0, "First commit succeeds with author identity configured")
    check("commit A: add notes.txt" in r.stdout or "commit A" in r.stdout,
          "Commit message appears in commit output")

    r = subprocess.run(
        ["git", "log", "--oneline"], capture_output=True, text=True, cwd=repo, env=env
    )
    check(r.returncode == 0 and len(r.stdout.strip()) > 0,
          "git log --oneline shows at least one commit after first commit (Stage 6)")
    check("commit A" in r.stdout,
          "git log --oneline shows 'commit A' message")

    r = subprocess.run(
        ["git", "status"], capture_output=True, text=True, cwd=repo, env=env
    )
    check("nothing to commit, working tree clean" in r.stdout,
          "git status shows clean working tree after first commit (Stage 6)")

    # --- HEAD resolves to a commit ---
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, cwd=repo, env=env,
    )
    check(r.returncode == 0 and len(r.stdout.strip()) == 40,
          "HEAD resolves to a 40-char commit hash after first commit")

    # --- author identity in commit ---
    r = subprocess.run(
        ["git", "log", "--format=%an <%ae>", "-1"],
        capture_output=True, text=True, cwd=repo, env=env,
    )
    check("Course Student" in r.stdout and "student@example.invalid" in r.stdout,
          "Commit records correct author: Course Student <student@example.invalid>")

finally:
    shutil.rmtree(tmpdir, ignore_errors=True)

# ── Summary ────────────────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"Results: {passes} passed, {fails} failed")
if fails:
    print("SOME CHECKS FAILED — please review the output above.")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED ✓")
