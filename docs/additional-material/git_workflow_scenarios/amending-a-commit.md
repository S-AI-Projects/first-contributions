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

## Amending a commit when a path contains spaces

Names that contain spaces must be quoted in the shell. Without quotes the shell splits the name into separate words, and git receives the wrong paths. This example uses a file named `release notes.txt` and a directory named `sample data`, on a branch called `topic`.

Without quotes, git receives two separate paths, `release` and `notes.txt`, and refuses. The same happens for `sample data`. Nothing is staged:

```
$ git add release notes.txt
fatal: pathspec 'release' did not match any files
$ git add sample data
fatal: pathspec 'sample' did not match any files
```

With quotes, each name reaches git as one path. `--` marks everything after it as a path:

```
$ git add -- "release notes.txt" "sample data"
$ git commit -m "D: add release notes and sample data"
```

Later you notice that a line is missing from `release notes.txt`. Edit the file, stage only that file, and amend, as described above:

```
$ git add -- "release notes.txt"
$ git status --short
 M notes.txt
M  "release notes.txt"
$ git commit --amend --no-edit
```

The quotes around `release notes.txt` in the `git status --short` output are only how git displays a name with spaces. They are not part of the name. The other modified file, `notes.txt`, was not staged, so it is not part of the amended commit. `--no-edit` keeps the old message and does not open the editor.

Only the `topic` branch is affected. It now points to a new commit that replaces the old one, with the same parent and the same message. Other branches, such as `main`, do not move.

### When `--` is required

`--` separates revisions (branches, tags, commit ids) from paths. Commands such as `git log` accept both, so git has to decide which one a word is. If a file has the same name as a branch, git refuses to guess:

```
$ git log --oneline topic
fatal: ambiguous argument 'topic': both revision and filename
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
```

Put `--` after the word to mean the branch, or before it to mean the file:

```
$ git log --oneline topic --     # history of the branch topic
$ git log --oneline -- topic     # history of the file topic
```

`git add` takes only paths, so this ambiguity cannot happen there. Quoted paths with spaces also work without `--`, for example `git log "release notes.txt"`, as long as the name is not also a revision. Writing `git log -- "release notes.txt"` removes any doubt.

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
