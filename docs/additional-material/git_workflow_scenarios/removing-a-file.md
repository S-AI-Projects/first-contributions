# Removing a file from Git

Sometimes, you may want to remove a file from Git but not delete it from your computer. You can achieve this by using the following command:

``git rm <file> --cached``

## So what happened?

Git will no longer keep track of changes in the removed file. As far as Git knows, it's as if you had deleted the file. If you were to locate the file in your file system, you will notice that it's still there.

Notice that in the example above, the flag `--cached` is used. If we didn't add this flag, Git will remove the file from not just the repo, but from your file system too.

If you commit the change with `git commit -m "Remove file1.js"` and push it to the remote repository using `git push origin main` (or whichever branch you're working on), the remote repository will remove the file.

## Additional features

-   If you want to remove more than one file, you can include them all in the same command:

    `git rm file1.js file2.js file3.js --cached`

-   You can use a wildcard (*) to remove similar files. For example, if you would like to remove all .txt files from your local repository:

    `git rm *.txt --cached`

---

## Reproducible Example: Untracking a File with `git rm --cached`

The following step-by-step example demonstrates how `git rm --cached` removes a file from Git tracking while preserving it in your local filesystem.

### 1. Repository Setup

Create an isolated working repository and a local bare repository serving as `origin`:

```bash
# Set author identity
export GIT_AUTHOR_NAME="Course Student"
export GIT_AUTHOR_EMAIL="student@example.invalid"
export GIT_COMMITTER_NAME="Course Student"
export GIT_COMMITTER_EMAIL="student@example.invalid"

# Create a bare remote repository (origin)
git init --bare remote.git

# Initialize working repository with default branch main
git init -b main work
cd work
git remote add origin file://$(pwd)/../remote.git

# Commit A: create notes.txt
printf "alpha\n" > notes.txt
git add notes.txt
git commit -m "Commit A: create notes.txt"

# Commit B: append beta to notes.txt
printf "beta\n" >> notes.txt
git add notes.txt
git commit -m "Commit B: append beta to notes.txt"
COMMIT_B=$(git rev-parse HEAD)

# Branch topic at Commit B
git branch topic "$COMMIT_B"

# Commit C: add todo.txt
printf "one\n" > todo.txt
git add todo.txt
git commit -m "Commit C: add todo.txt"

# Push main to origin
git push -u origin main
```

At this point, `main` contains three commits (A, B, and C). Both `notes.txt` and `todo.txt` are tracked in Git, and the working tree is clean:

```bash
$ git status
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean

$ git log --oneline
<COMMIT_C> (HEAD -> main, origin/main) Commit C: add todo.txt
<COMMIT_B> (topic) Commit B: append beta to notes.txt
<COMMIT_A> Commit A: create notes.txt
```

### 2. Remove `todo.txt` from Tracking Using `git rm --cached`

Run `git rm --cached` to stop tracking `todo.txt`:

```bash
$ git rm --cached todo.txt
rm 'todo.txt'
```

### 3. Verify Git Status and Working Tree

Check `git status`:

```bash
$ git status
On branch main
Your branch is up to date with 'origin/main'.

Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	deleted:    todo.txt

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	todo.txt
```

Notice two critical facts:
1. **Changes to be committed**: Git stages the file deletion (`deleted: todo.txt`) in the index for the next commit.
2. **Untracked files**: `todo.txt` is listed under untracked files because **it is still present on your hard drive**.

Verify that `todo.txt` still exists in your filesystem with its contents intact:

```bash
$ cat todo.txt
one
```

### 4. Commit the Removal and Push to Remote

Commit the staged deletion:

```bash
$ git commit -m "Remove todo.txt from repository"
[main <COMMIT_D>] Remove todo.txt from repository
 1 file changed, 1 deletion(-)
 delete mode 100644 todo.txt
```

Push the commit to the remote repository:

```bash
$ git push origin main
To file:///.../remote.git
   <COMMIT_C>..<COMMIT_D>  main -> main
```

### 5. Inspect the Resulting Git State

Verify the commit log:

```bash
$ git log -1 --stat
commit <COMMIT_D> (HEAD -> main, origin/main)
Author: Course Student <student@example.invalid>
Date:   ...

    Remove todo.txt from repository

 todo.txt | 1 -
 1 file changed, 1 deletion(-)
 delete mode 100644 todo.txt
```

Verify that the remote tree no longer contains `todo.txt`, while your local file remains untouched:

```bash
# Check tracked files in the latest commit tree (todo.txt is gone)
$ git ls-tree --name-only HEAD
notes.txt

# Check your working directory (todo.txt is still here!)
$ ls
notes.txt  todo.txt

$ git status
On branch main
Your branch is up to date with 'origin/main'.

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	todo.txt

nothing added to commit but untracked files present (use "git add" to track)
```
