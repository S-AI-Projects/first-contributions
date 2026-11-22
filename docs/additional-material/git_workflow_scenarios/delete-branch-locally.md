# Deleting a locally created Branch

This will be handy when you accidentally misspelled a branch name.

This can be done in *3* ways

```
git branch -D <branch_name>
```

```
git branch --delete --force <branch_name>  # Same as -D
```

```
git branch --delete  <branch_name>         # Error on unmerge
```

-D stands for --delete --force which will delete the branch even it's not merged (force delete), but you can also use -d which stands for --delete which throws an error respective of the branch merge status...

---

## Handling Paths with Spaces and Ambiguity in Branch Workflows

When working with branches, you frequently handle files or directories that contain spaces—such as `"release notes.txt"` or `"sample data"`. It is important to know where shell quoting and Git's `--` separator are required.

### 1. Shell Word Splitting and Quoting

When a filename or path contains spaces, your command shell splits unquoted arguments by whitespace. 

For example, trying to stage `"release notes.txt"` without quotes fails:

```bash
$ git add release notes.txt
fatal: pathspec 'release' did not match any files
```

Here, the shell treats `release` and `notes.txt` as two separate arguments, and Git cannot find any file named `release`.

To prevent word splitting, enclose the path in quotes:

```bash
git add "release notes.txt" "sample data/data.txt"
```

---

### 2. Disambiguating Revisions from File Paths (`--`)

Many Git commands accept both branch/revision names and file paths (such as `git checkout`, `git diff`, and `git log`). If a file or folder shares a name with a branch, or if Git cannot determine whether an argument is a revision or a file, Git reports an ambiguity error.

The `--` syntax explicitly signals to Git that all subsequent arguments are **file paths**, not revisions.

For example, to safely discard working-tree changes to a file with spaces:

```bash
git checkout -- "release notes.txt"
```

Without quotes, `git checkout -- release notes.txt` would fail because Git would search for two separate pathspecs.

Similarly, when comparing file differences between branches:

```bash
git diff main..topic -- "release notes.txt" "sample data"
```

The `--` guarantees that Git treats `"release notes.txt"` and `"sample data"` strictly as paths to filter, rather than branch references.

---

### 3. Branch Deletion with Unmerged Quoted Paths

Suppose you committed `"release notes.txt"` and `"sample data/data.txt"` on branch `topic`, and now want to delete `topic` after returning to `main`:

```bash
# Switch back to the main branch
git switch main

# Attempting safe deletion
$ git branch --delete topic
error: the branch 'topic' is not fully merged
hint: If you are sure you want to delete it, run 'git branch -D topic'
hint: Disable this message with "git config set advice.forceDeleteBranch false"
```

Because `topic` contains unmerged commits with your release notes and sample data, Git's safety mechanism refuses to delete it with `--delete`.

To forcefully delete the branch and discard its unmerged changes:

```bash
git branch -D topic
```

Or using the equivalent long-form option:

```bash
git branch --delete --force topic
```

Output:
```bash
Deleted branch topic (was <commit-hash>).
```

---

## Related Topics

- [Remove a branch from your repository](removing-branch-from-your-repository.md)
- [Why use branches?](why-using-branches.md)
- [Official Git branch Documentation](https://git-scm.com/docs/git-branch)
