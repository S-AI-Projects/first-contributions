# Reset a commit

```reset``` is the command which can be used when we want to move the repository back to a previous commit, discarding any changes made after that commit.<br/>
The main difference between resetting and reverting a commit is that git reset ```unstages a file and bring our changes back to the working directory``` 
and git revert ```removes the commits from the remote repository```. <br/>

```git reset``` can be achieved using following commands:
- The following command will give summary of all the commits using following two parameters:
   
     - The first seven characters of the commit hash - this is what we need to refer to in our **reset** command.
     - the commit message
  
   ```
   git log --oneline
   ```
 
   
- One can reset repository back to the specific commit using following command: <br />
  ```git reset commithash```
  where commithash being the first 7 characters of the commit hash we found in the log

---

## Troubleshooting: `git reset` fails with an invalid or unknown commit hash

**Triggering state.** You tried to reset your repository using `git reset <commithash>`, but the specified commit hash or revision does not exist in the repository history (for example, due to a mistyped hash like `badc0de` or an out-of-bounds relative reference like `HEAD~5` when only three commits exist).

**Error category.** Invalid revision / unknown object reference. Git cannot resolve the argument to a valid commit object in the repository database. Because Git cannot tell whether an unrecognized argument was intended as a commit revision or a file path, it aborts with a nonzero exit status (exit code `128`):

```text
$ git reset badc0de
fatal: ambiguous argument 'badc0de': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
```

When this occurs, Git leaves your repository state completely untouched: `HEAD`, the staging area (index), and your working directory remain exactly where they were before the command was run.

**Smallest correction.** Use `git log --oneline` to find the authentic 7-character commit hash of your target commit, and run `git reset` with that valid identifier:

```bash
# 1. View recent commits to obtain valid commit hashes
$ git log --oneline
<COMMIT_C> (HEAD -> main) Commit C: add todo.txt
<COMMIT_B> Commit B: append beta to notes.txt
<COMMIT_A> Commit A: create notes.txt

# 2. Reset to the desired valid commit hash (e.g., Commit B)
$ git reset <COMMIT_B>
Unstaged changes after reset:
M	notes.txt
```

Once executed with a valid commit hash, `git reset` succeeds (exit code `0`), moving `HEAD` to Commit B while preserving uncommitted file modifications in your working directory.
