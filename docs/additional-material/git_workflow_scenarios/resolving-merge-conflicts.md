# What is a merge conflict?

A merge conflict occurs when changes from different branches clash and Git cannot merge them automatically. Common scenarios include:

- Two contributors editing the same line in a file.
- One contributor deletes a file that another has modified.
- Simultaneous renaming of a file to different names in separate branches.

In such cases, Git will pause the merge process and mark the conflicting files for manual resolution. There are tools that helps users resolve these conflicts but in this guide, we will be focusing on the git command line tool.

## How to resolve a merge conflict?

1. **Identify Conflicted Files**
   After attempting a merge, Git will notify you of conflicts. Use the following command to list them:

```bash
git status
```

Look for files listed under "Unmerged paths."

2. **Open and Examine Conflicted Files**
   Open each conflicted file in your preferred text editor. Git sets boundaries for conflicts using the following markers:

```plaintext
<<<<<<< HEAD
Your changes
=======
Incoming changes
>>>>>>> branch-name
```

- `<<<<<<< HEAD` represents your current branch's changes.

- `=======` separates the conflicting changes.

- `>>>>>>> branch-name` shows the incoming changes from the other branch.

3. **Resolve the Conflicts**

Decide how to integrate the changes:

- Keep your changes.
- Accept the incoming changes.
- Combine both changes in a coherent manner.

After making the necessary edits, remove the conflict markers (<<<<<<<, =======, >>>>>>>)

4. **Mark Conflicts as Resolved**
   Once you've resolved the conflicts in a file:

```bash
git add <filename>
```

**Repeat this for each conflicted file.**

5. **Commit the Merge**
   After staging all resolved files:

```bash
git commit -m "Resolved merge conflicts"
```

🎉This finalizes the merge process.🎉

---

# Additional information

## Tools to Assist in Conflict Resolution

- Git Merge Tool: Launches a visual merge tool to help resolve conflicts.

```bash
git mergetool
```

> Note: Ensure you have a merge tool installed (e.g., Meld, KDiff3, Beyond Compare).

- Abort a Merge: If you wish to cancel the merge process:

```bash
  git merge --abort
```

## Best Practices to Avoid Conflicts

Pull Regularly: Frequently pull changes from the main branch to stay updated.

```bash
git pull origin main
```

Work on Feature Branches: Create separate branches for each feature or fix.

```bash
git checkout -b feature-branch
```

## Additional Resources

- [GitHub: Resolving Merge Conflicts via Command Line](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts/resolving-a-merge-conflict-using-the-command-line)

- [Atlassian: Git Merge Conflicts Tutorial](https://www.atlassian.com/git/tutorials/using-branches/merge-conflicts)

- [FreeCodeCamp: Practical Guide to Merge Conflicts](https://www.freecodecamp.org/news/resolve-merge-conflicts-in-git-a-practical-guide/)

By following this guide, you'll be well-equipped to handle merge conflicts confidently, ensuring a smoother contribution process to any open source project!

## Before you start: preconditions

The steps in this guide (`git status`, `git add`, `git commit -m "Resolved merge conflicts"`) only work in a particular state. Check each item below. The last column shows what you should see.

| # | Prerequisite | Check with | You should see |
|---|---|---|---|
| 1 | You started the merge from a clean working tree | `git status`, before `git merge` | `nothing to commit, working tree clean` |
| 2 | You are on the branch you merged into | `git status` | `On branch main` (or your own branch name) |
| 3 | The merge stopped on a conflict | `git status` and `git status --short` | `You have unmerged paths.`, `both modified:   notes.txt`, and `UU notes.txt` |
| 4 | The conflicted file has conflict markers while you edit it, and none when you are done | `git diff --check` | `leftover conflict marker` lines at first, no output when done |
| 5 | The resolved file is staged | `git add notes.txt`, then `git status` | `All conflicts fixed but you are still merging.` |
| 6 | Your name and email are configured | `git config user.name` and `git config user.email` | your name and your email |

**Minimal setup example.** Start in an empty folder. Use your own name and email in the two `git config` lines (see [configuring git](configuring-git.md)).

```
git init -b main
git config user.name "Your Name"
git config user.email "you@example.com"
printf 'alpha\n' > notes.txt
git add notes.txt
git commit -m "A: create notes.txt"
printf 'beta\n' >> notes.txt
git commit -am "B: append beta"
printf 'one\n' > todo.txt
git add todo.txt
git commit -m "C: add todo.txt"
git branch topic HEAD~1
git switch topic
printf 'alpha\nbeta from topic\n' > notes.txt
git commit -am "D: change line 2 on topic"
git switch main
printf 'alpha\nbeta from main\n' > notes.txt
git commit -am "E: change line 2 on main"
git merge topic
```

The last command stops with a conflict:

```
Auto-merging notes.txt
CONFLICT (content): Merge conflict in notes.txt
Automatic merge failed; fix conflicts and then commit the result.
```

`notes.txt` now contains the conflict markers:

```
alpha
<<<<<<< HEAD
beta from main
=======
beta from topic
>>>>>>> topic
```

Edit the file to the text you want to keep, for example `beta from main and topic`, and then finish the merge:

```
git add notes.txt
git commit -m "Resolved merge conflicts"
```

The merge commit has two parents, the old tip of `main` and the tip of `topic`. Only `main` moves; `topic` stays where it was.

**What happens when a prerequisite is missing**

- Committing before `git add` (prerequisite 5) fails with `error: Committing is not possible because you have unmerged files.` Nothing changes, and the merge is still in progress.
- Committing without a name and email (prerequisite 6) fails with `Author identity unknown`. The merge is still in progress and your resolved file is still staged, so set the name and email and run the same `git commit` again.
