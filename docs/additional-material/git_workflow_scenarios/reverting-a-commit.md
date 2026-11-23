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

## Recovery: Undoing an Accidental Revert

A common mistake when using `git revert` is accidentally reverting the wrong commit—such as reverting a needed feature commit (e.g. Commit C which added `todo.txt`). This creates a new revert commit that removes `todo.txt` from the project.

Here is how to recover the original file and repository state using documented Git mechanisms in an isolated disposable repository.

### 1. Minimal Setup and the Mistake

Set up a temporary repository with branch `main`, author `Course Student <student@example.invalid>`, and three commits (A, B, C), with branch `topic` pointing to B:

```sh
tmp=$(mktemp -d)
git -C "$tmp" init -b main
git -C "$tmp" config user.name 'Course Student'
git -C "$tmp" config user.email 'student@example.invalid'
cd "$tmp"

# Commit A: creates notes.txt
printf 'alpha\n' > notes.txt
git add notes.txt && git commit -m 'A: add notes'

# Commit B: appends beta
printf 'beta\n' >> notes.txt
git add notes.txt && git commit -m 'B: append notes'
B=$(git rev-parse HEAD)
git branch topic "$B"

# Commit C: adds todo.txt
printf 'one\n' > todo.txt
git add todo.txt && git commit -m 'C: add todo'
C=$(git rev-parse HEAD)
TREE_C=$(git rev-parse HEAD^{tree})

# Mistaken Operation: accidentally reverting commit C
git revert --no-edit "$C"
```

After the mistaken revert:
- A new revert commit is created: `Revert "C: add todo"`.
- `todo.txt` is removed from the working tree.
- The repository state no longer contains the file added by Commit C.

### 2. Recovery Points and Execution

To recover the original state, you have two Git mechanisms depending on whether the mistaken revert commit was already shared/pushed:

#### Method 1: Reverting the Revert (Safe for shared/pushed commits)

Revert the revert commit itself:

```sh
git revert --no-edit HEAD
```

- **Effect:** Git creates a new commit that inverts the deletion, restoring `todo.txt` with its original content (`"one\n"`).
- **Tree Verification:** The resulting tree hash (`git rev-parse HEAD^{tree}`) matches `TREE_C` exactly.
- **What cannot be recovered by this method:** A completely clean, unblemished linear git log; the history retains both the accidental revert and the recovery revert commits.

#### Method 2: Resetting the Branch (Safe for local, unpushed commits)

If the mistaken revert has not been pushed to a remote, restore the exact commit and branch tip:

```sh
git reset --hard "$C"
```

- **Effect:** HEAD and `main` immediately point back to Commit C.
- **Tree Verification:** Both commit hash and tree hash match Commit C.
- **What cannot be recovered by this method:** Any uncommitted modifications present in the working tree when running `git reset --hard` are permanently overwritten.

### 3. Verification Commands

Verify the recovered state:

```text
$ git rev-parse HEAD^{tree}
# matches TREE_C

$ cat todo.txt
one

$ git status --short
# clean (no modified or untracked files)
```
