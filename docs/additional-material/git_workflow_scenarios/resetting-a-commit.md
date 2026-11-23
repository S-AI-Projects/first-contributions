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

## Reproducible Step-by-Step Example

The following self-contained walkthrough demonstrates resetting a branch back to a previous commit using an isolated, temporary Git repository.

### 1. Minimal Setup

Create a temporary repository with branch `main`, configure a local author, and create three sequential commits:

```sh
tmp=$(mktemp -d)
git -C "$tmp" init -b main
git -C "$tmp" config user.name 'Course Student'
git -C "$tmp" config user.email 'student@example.invalid'
cd "$tmp"

# Commit A: create notes.txt
printf 'alpha\n' > notes.txt
git add notes.txt
git commit -m 'A: add notes'

# Commit B: append to notes.txt
printf 'beta\n' >> notes.txt
git add notes.txt
git commit -m 'B: append notes'
B=$(git rev-parse HEAD)

# Create branch topic at commit B
git branch topic "$B"

# Commit C: create todo.txt
printf 'one\n' > todo.txt
git add todo.txt
git commit -m 'C: add todo'
```

At this point, the repository has three commits on `main`. The `topic` branch points to Commit B.

```text
$ git log --oneline --decorate -3
<C> (HEAD -> main) C: add todo
<B> (topic) B: append notes
<A> A: add notes
```

### 2. Inspecting the Log and Executing Reset

Run `git log --oneline` to find the 7-character commit hash of Commit B:

```sh
git log --oneline
```

Then reset the repository back to Commit B:

```sh
git reset "$B"
```

### 3. Expected State After Reset

By default, `git reset` runs in mixed mode:
- **Branch reference:** `main` (and `HEAD`) moves back from Commit C to Commit B.
- **Unrelated references:** The `topic` branch remains unchanged, pointing to Commit B.
- **Index:** The staging area is reset to match Commit B.
- **Working directory:** Changes introduced in Commit C are preserved but unstaged; `todo.txt` appears as an untracked file (`?? todo.txt`).
- **File contents:** `notes.txt` contains `alpha\nbeta\n`.

Expected `git status` output:
```text
$ git status --short --branch
## main
?? todo.txt
```

Expected `git log` output:
```text
$ git log --oneline --decorate -3
<B> (HEAD -> main, topic) B: append notes
<A> A: add notes
```

Commit C is no longer part of the history of `main`. Its changes remain safely in your working directory as untracked files, allowing you to edit or discard them as needed.
