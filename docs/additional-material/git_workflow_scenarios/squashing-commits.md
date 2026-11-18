# What is squashing?

In git, squashing refers to rewriting the history of your commits, so you end up with one commit with a description of the changes done.
It's usually done in open source projects because a lot of the history of a branch in open source projects is only relevant to the developer who created it, and this provides a simpler way to describe the changes made and also revert them if needed.

# How do you squash commits?

First, perform a git log to review the commits you would like to merge in your current branch.

```
git log
```

You should see a series of your commits like so:

```
commit blablabla
Author: omguhh
Date:   10/10/20
    Commit message 1

commit blablabla2
Author: omguhh
Date:   10/10/20
    Commit message 2
```

So now that you see the commits you wish to merge to one, we can move along into doing that with ```git rebase```. Assuming you're already familiar with ```git rebase```, we can starting squashing commits in the interactive mode of git rebase that you can activate like so:

```
git rebase -i
```

Now, with interactive rebasing you can specify the starting and end point of how far back you want to go with commits like so:

```
git rebase -i HEAD~2
```

Running this command will show you something like the following:

```
pick blablabla Changing test01.txt file
pick blablabla2 Adding dummy01.txt file

#
# Commands:
#  p, pick = use commit
#  r, reword = use commit, but edit the commit message
#  e, edit = use commit, but stop for amending
#  s, squash = use commit, but meld into previous commit
#  f, fixup = like "squash", but discard this commit's log message
#  x, exec = run command (the rest of the line) using shell
#
# These lines can be re-ordered; they are executed from top to bottom.
#
# If you remove a line here THAT COMMIT WILL BE LOST.
#
# However, if you remove everything, the rebase will be aborted.
#
# Note that empty commits are commented out
```

So if you want to squash ```blablabla2``` into ```blablablabla```, you would change the following :

```
pick blablabla Changing test01.txt file
squash blablabla2 Adding dummy01.txt file

```

If all goes well, you'd get a result that looks like this:

```
# This is a combination of 2 commits.
# The first commit's message is:
commit message 1

# This is the 2nd commit message:

commit message 2
```

That you can freely change before you decide to exit the editor to save these changes.

Running git log again should show you the commit message you entered before exiting the screen with the commits combined into one.

# Example: which branch does squashing change?

Squashing rewrites the branch that is checked out, so it helps to name every ref explicitly. Here is a small local example (no remote needed).

The local branch `main` has three commits, A, B and C. The local branch `topic` was created at B, and `topic` is checked out:

```
A --- B --- C   <- main
      ^
      topic (checked out)
```

`git log` shows the history of the checked-out branch, so it lists B and A, but not C. `HEAD~2` is counted from `topic`, not from `main`. `topic` has only two commits, so `HEAD~2` does not exist:

```
git rebase -i HEAD~2
fatal: invalid upstream 'HEAD~2'
```

Nothing changes when this fails. `git rebase -i main` does not help either: `git log --oneline main..topic` is empty, because `topic` has no commits that `main` lacks. There is nothing to squash, and git simply moves `topic` forward to the tip of `main`.

To squash A and B into one commit, rebase from the root of `topic`:

```
git rebase -i --root
```

Change the second `pick` to `squash`, then save and edit the combined message as described above.

Afterwards only the local branch `refs/heads/topic` has moved. It points to a new commit with the same files as B. The local branch `main` still has A, B and C, so `topic` and `main` no longer share history. A remote-tracking ref such as `origin/topic` is not touched by a local squash. The old commit B can still be found with `git reflog topic` until git cleans it up.

In everyday work a feature branch is usually ahead of `main`. In that case `git rebase -i main` lists exactly the commits in `main..topic`, which are the ones you can squash.
