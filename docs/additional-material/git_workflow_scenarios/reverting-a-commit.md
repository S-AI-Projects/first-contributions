# Revert a commit

To revert a commit simply means to create a brand new commit that undoes all
the changes made in a previous one. It is like doing a ```CTRL + Z ``` on git.

Reversion is made easier in git because every commit you push to your remote repository has a unique alphanumeric key known as SHA(Secure Hash Algorithm) tied to it.
So this means you can revert any commit as long as you have the SHA.
But then, you have to be careful to reverse orderly so as not to mess your repository up.


To pick out the SHA of the specific commit we want to undo, a log of all the commits we have made so far would come in handy.
To get this, we would run the command:
```git log --oneline ```
Running the ```git log``` command alone would also give us the SHAs (in long form)
However using the ```--oneline ``` flag tells git that we want it displayed in a concise (one line) manner for easy read.

The first 7 characters displayed when you run this command is called the abbreviated commit hash.

For example, here is what I get when I run ```git log --oneline ``` on this repository:
```
389004d added spacing in title
c1b9fc1 Merge branch 'master' into tutorials
77eaafd added tutorial for reverting a commit
```

So this shows that with ```git log --oneline```, we can fetch a list of all the commits made on the repository together with the first 7 characters of its SHA.

Now, Let's assume I want to undo my commit of "added spacing in title", here are the steps I would take:

*   Copy the SHA of the commit which, in this case is ```389004d```
*   Then, run the command ```git revert 389004d```

This would pop open my text editor and prompt me to edit the commit message.
You can decide to leave the commit message as the default git message which starts with the word `Revert`
or you can also decide to customize the message to your liking.

*   Next, I will save and close the text editor.
*   Return to the command line.
*   Run ```git push origin <branch-name>``` to push the reverted changes to Github.

And that is it, the change would be undone. In this case,  my repository would be reverted to how it looked like in ```c1b9fc1```

---

## Prediction-and-Verification Exercise: Reverting Commit C

To understand how `git revert` works under the hood, work through this prediction exercise using an isolated repository.

### 1. Repository Setup

We create a repository with author `Course Student <student@example.invalid>` on branch `main` with three commits:
- **Commit A**: creates `notes.txt` with `"alpha\n"`
- **Commit B**: appends `"beta\n"` to `notes.txt`
- **Commit C**: creates `todo.txt` with `"one\n"`
- Branch `topic` created at Commit B.

```bash
# Author identity
export GIT_AUTHOR_NAME="Course Student"
export GIT_AUTHOR_EMAIL="student@example.invalid"
export GIT_COMMITTER_NAME="Course Student"
export GIT_COMMITTER_EMAIL="student@example.invalid"

# Initialize repository
git init -b main repo
cd repo

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

Viewing the initial state:

```bash
$ git log --oneline
<COMMIT_C> (HEAD -> main) Commit C: add todo.txt
<COMMIT_B> (topic) Commit B: append beta to notes.txt
<COMMIT_A> Commit A: create notes.txt
```

---

### 2. Predict the Resulting State

Before running `git revert <COMMIT_C>`, pause and predict the outcome across the core areas of Git state:

1. **Ref & Commit Graph**:
   - *Question*: Will Commit C be deleted from history, or will a new commit be created?
   - *Prediction*: Unlike `git reset`, `git revert` is purely forward-moving. Commit C remains in history permanently. A brand new commit (let's call it Commit D) will be added to the tip of `main` with parent Commit C. The history will become `[Commit D, Commit C, Commit B, Commit A]`.
2. **Index & Tree Contents**:
   - *Question*: Which files and tree objects will change?
   - *Prediction*: The change introduced by Commit C was the addition of `todo.txt`. Reverting it applies the exact inverse patch: deleting `todo.txt`. The new commit tree will contain `notes.txt`, but `todo.txt` will be completely removed from the Git tree.
3. **Working Tree Status**:
   - *Question*: What will `git status` show?
   - *Prediction*: `todo.txt` will be deleted from your hard drive, and `git status` will report a completely clean working directory.
4. **Other Branches**:
   - *Question*: Will branch `topic` change?
   - *Prediction*: `refs/heads/topic` will remain completely unaffected and stay pointed at Commit B.

---

### 3. Execution

Execute the revert:

```bash
git revert --no-edit "$COMMIT_C"
```

Output:
```text
[main <COMMIT_D>] Revert "Commit C: add todo.txt"
 1 file changed, 1 deletion(-)
 delete mode 100644 todo.txt
```

---

### 4. Verification and Explanation of Results

Now verify your predictions against the real Git state:

#### Check 1: Commit Graph and Refs
```bash
$ git log --oneline
<COMMIT_D> (HEAD -> main) Revert "Commit C: add todo.txt"
<COMMIT_C> Commit C: add todo.txt
<COMMIT_B> (topic) Commit B: append beta to notes.txt
<COMMIT_A> Commit A: create notes.txt
```
*Result*: Confirms prediction 1. A new commit `<COMMIT_D>` was created, preserving Commit C in the permanent linear history.

#### Check 2: Tree Contents
```bash
$ git ls-tree --name-only HEAD
notes.txt
```
*Result*: Confirms prediction 2. The tree object associated with `<COMMIT_D>` contains only `notes.txt`. The blob for `todo.txt` has been removed from this snapshot.

#### Check 3: Working Tree State
```bash
$ ls
notes.txt

$ git status
On branch main
nothing to commit, working tree clean
```
*Result*: Confirms prediction 3. `todo.txt` was removed from the local filesystem, and the working tree is clean.

#### Check 4: Other Branches
```bash
$ git rev-parse topic
<COMMIT_B>
```
*Result*: Confirms prediction 4. `topic` was not modified and remains at Commit B.
