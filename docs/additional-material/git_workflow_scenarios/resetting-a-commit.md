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

## Preconditions and Minimal Setup for `git reset`

Before executing `git reset`, several prerequisites must be verified to ensure the operation resets the intended branch without unexpected state loss.

### Precondition Checklist

| Requirement | What to Verify | Verification Command |
|---|---|---|
| **1. Repository State** | Must be inside an initialized Git repository with at least one prior commit to reset to. | `git rev-parse --is-inside-work-tree` |
| **2. Active Branch** | Identify which branch is currently checked out, as `git reset` directly rewrites the tip of the current `HEAD`. | `git branch --show-current` |
| **3. Staging and Working Tree** | Know whether you have uncommitted changes. By default (`--mixed`), `git reset` leaves your working directory files intact while unstaging index changes. | `git status` |
| **4. Valid Target Commit** | Locate the exact 7-character commit SHA or relative reference to reset back to. | `git log --oneline` |
| **5. Configuration** | Ensure local repository identity is configured so Git metadata is unambiguous. | `git config --local user.name` |

---

### Minimal Reproducible Setup and Demonstration

The following walkthrough demonstrates the complete setup and state transitions when executing `git reset <commithash>`.

#### 1. Setup the Repository and History

Create an isolated working repository with branch `main`, local identity `Course Student <student@example.invalid>`, and three initial commits:
- **Commit A**: `notes.txt` with `"alpha\n"`
- **Commit B**: appends `"beta\n"` to `notes.txt`
- **Commit C**: `todo.txt` with `"one\n"`
- Branch `topic` created at Commit B.

```bash
# Initialize repository
git init -b main repo
cd repo

# Set local repository configuration
git config user.name "Course Student"
git config user.email "student@example.invalid"

# Commit A
printf "alpha\n" > notes.txt
git add notes.txt
git commit -m "Commit A: create notes.txt"

# Commit B
printf "beta\n" >> notes.txt
git add notes.txt
git commit -m "Commit B: append beta to notes.txt"
COMMIT_B=$(git rev-parse HEAD)

# Branch topic at Commit B
git branch topic "$COMMIT_B"

# Commit C on main
printf "one\n" > todo.txt
git add todo.txt
git commit -m "Commit C: add todo.txt"
COMMIT_C=$(git rev-parse HEAD)
```

Verify initial prerequisites:

```bash
$ git branch --show-current
main

$ git status
On branch main
nothing to commit, working tree clean

$ git log --oneline
<COMMIT_C> (HEAD -> main) Commit C: add todo.txt
<COMMIT_B> (topic) Commit B: append beta to notes.txt
<COMMIT_A> Commit A: create notes.txt
```

#### 2. Execute `git reset <commithash>`

Reset `main` back to Commit B:

```bash
git reset "$COMMIT_B"
```

Output:
```text
Unstaged changes after reset:
M	notes.txt
```

#### 3. State Verification After Reset

1. **Active Branch Pointer**: `HEAD` and `refs/heads/main` now point directly to Commit B:
   ```bash
   $ git rev-parse HEAD
   <COMMIT_B>
   ```
2. **Commit History**: `git log --oneline` now shows Commit B as the tip of `main`:
   ```bash
   $ git log --oneline
   <COMMIT_B> (HEAD -> main, topic) Commit B: append beta to notes.txt
   <COMMIT_A> Commit A: create notes.txt
   ```
3. **Working Tree and Index**: The changes from Commit C (`todo.txt`) are unstaged and preserved in your working tree:
   ```bash
   $ git status --short
   ?? todo.txt
   ```
4. **Other Branches**: Branch `topic` remains completely unaffected and still points to Commit B.
