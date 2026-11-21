# Amending a Commit

What if you commit a change to your remote repository and later realize that your commit message contains a typo?
Or that you forgot to add a line to your most recent commit?
How do you edit that? This is what this tutorial covers.

## Changing a recent commit message after pushing to GitHub.
To do this without opening a file:
*   Type in the ```git commit --amend -m "followed by your new commit message"```
*   Run ```git push origin <branch-name>``` to push the changes to the repository.

Note: If you type in just ```git commit --amend```, your text editor would open up prompting you to edit the commit message.
Adding the ``-m`` flags prevents it.

## Modifying a single commit

So, what if we forgot to make a minor change to a file like changing a single word and we have already pushed the commit to our remote repository?

To illustrate here is a log of my commits:
```
g56123f create file botfile
a2235d updated contributor.md
a5da0d modified botfile
```
Let's say I forgot to add a single word to the botfile.

There are 2 ways to go about this. The first is to have an entirely new commit that contains the change like so:
```
g56123f create file botfile
a2235d updated contributor.md
a5da0d modified botfile
b0ca8f added single word to botfile
```
The second way is to amend the a5da0d commit, add this new word and  push it to Github as one commit.
The second sounds better since it is just a minor change.

To achieve this, we would do the following:
*   Modify the file. In this case, I will modify the botfile to include the word I omitted previously.
*   Next, add the file to the staging area with ```git add <filename>```

Usually after adding files to the staging area, the next thing we do is git commit -m "our commit message" right?
But since what we want to achieve here is to amend the previous commit, we would instead run:

* ```git commit --amend```
 This would then bring up the text editor and prompt you to edit the message. You can decide to leave the message as it was before or change it.
* Exit the editor
* Push your changes with ```git push origin <branch-name>```

That way, both changes would be in one single commit.

## Modifying commits on remote

If the commit that you like to amend has been already pushed to the remote, amending this commit will lead to your local history being diverged from the remote (since you basically create a new commit and replace the amended one). Since you want to change the commit on the remote, you need to overwrite the remotes history on your branch. To achieve that, follow the same procedure as described above, but use force push when pushing your commit to the remote.

> **Warning**  
> Force pushing to the remote will overwrite (and discard) changes on the remote and only keep your pushed commits. Changes on the remote, that other team members did in the meantime, will be overwritten as well.

This is how you modify the last recent commit on the remote:

```bash
git add <your changed files>
git commit --amend -m "followed by your new commit message"
git push --force
```

> Using `--force-with-lease` is a safer option instead of `--force` which avoids overwriting other people's changes on the remote branch (if you do not intend to do so).

---

## Example: Branch and Remote Behavior When Amending `topic`

Amending a commit rewrites the tip of whichever branch is currently checked out (`HEAD`). It never affects other branches or their upstream tracking references. Here is an exact demonstration showing which refs move and which refs remain fixed.

### 1. Repository Setup

Create an isolated repository and a local bare remote `origin`:

```bash
# Set author identity
export GIT_AUTHOR_NAME="Course Student"
export GIT_AUTHOR_EMAIL="student@example.invalid"
export GIT_COMMITTER_NAME="Course Student"
export GIT_COMMITTER_EMAIL="student@example.invalid"

# Create bare remote repository (origin)
git init --bare remote.git

# Initialize working repository
git init -b main local
cd local
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

# Create branch topic at Commit B
git branch topic "$COMMIT_B"

# Commit C on main: add todo.txt
printf "one\n" > todo.txt
git add todo.txt
git commit -m "Commit C: add todo.txt"
COMMIT_C=$(git rev-parse HEAD)

# Push main and topic to origin
git push -u origin main
git push -u origin topic
```

Inspect the initial reference structure:

```bash
$ git log --oneline --graph --all
* <COMMIT_C> (HEAD -> main, origin/main) Commit C: add todo.txt
* <COMMIT_B> (topic, origin/topic) Commit B: append beta to notes.txt
* <COMMIT_A> Commit A: create notes.txt
```

Current references:
- `refs/heads/main` -> `<COMMIT_C>`
- `refs/remotes/origin/main` -> `<COMMIT_C>`
- `refs/heads/topic` -> `<COMMIT_B>`
- `refs/remotes/origin/topic` -> `<COMMIT_B>`

### 2. Switch to `topic` and Amend Commit B

Switch to `topic` so that `HEAD` points to `refs/heads/topic`:

```bash
git checkout topic
```

Now append `"gamma\n"` to `notes.txt`, stage it, and amend the commit:

```bash
printf "gamma\n" >> notes.txt
git add notes.txt
git commit --amend -m "Commit B amended: beta and gamma"
COMMIT_B_PRIME=$(git rev-parse HEAD)
```

### 3. Which Branch is Affected?

Git replaced Commit B with a new commit object (`<COMMIT_B_PRIME>`):

```bash
$ git branch -vv
  main  <COMMIT_C> [origin/main] Commit C: add todo.txt
* topic <COMMIT_B_PRIME> [origin/topic: ahead 1, behind 1] Commit B amended: beta and gamma
```

Notice the ref states:
- **`refs/heads/topic`**: **CHANGED** &rarr; now points to new commit `<COMMIT_B_PRIME>`.
- **`refs/heads/main`**: **FIXED** &rarr; unchanged, still points to `<COMMIT_C>`.
- **`refs/remotes/origin/main`**: **FIXED** &rarr; unchanged, still points to `<COMMIT_C>`.
- **`refs/remotes/origin/topic`**: **FIXED** &rarr; unchanged, still points to original `<COMMIT_B>`.

Because `<COMMIT_B_PRIME>` has rewritten history, `topic` is 1 commit ahead and 1 commit behind `origin/topic`.

### 4. Updating the Remote Tracking Branch

Attempting a normal `git push origin topic` will fail with a non-fast-forward error because the remote still holds the old Commit B:

```bash
$ git push origin topic
To file:///.../remote.git
 ! [rejected]        topic -> topic (non-fast-forward)
error: failed to push some refs to 'file:///.../remote.git'
```

To update `origin/topic`, push with `--force-with-lease`:

```bash
$ git push --force-with-lease origin topic
To file:///.../remote.git
 + <COMMIT_B>...<COMMIT_B_PRIME> topic -> topic (forced update)
```

Now verify all refs:

```bash
$ git branch -vv
  main  <COMMIT_C> [origin/main] Commit C: add todo.txt
* topic <COMMIT_B_PRIME> [origin/topic] Commit B amended: beta and gamma
```

- `origin/topic` now points to `<COMMIT_B_PRIME>`.
- `main` and `origin/main` remained completely untouched throughout the entire process.
