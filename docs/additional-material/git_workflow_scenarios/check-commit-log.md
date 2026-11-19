# Check commit log

In order to check commits log for a branch, or, a file, following command can be used:

`git log [options] [path]`

The output of this command is given in reverse chronological order by default.

## Command output example
```
$ git log
commit e3fabb30ab536bd5876461d8a749301a321e714f (HEAD -> check-commit-log-ko, upstream/main, origin/main, origin/HEAD, main)
Author: Dan Yunheum Seol <yunheum.seol@mail.mcgill.ca>
Date:   Tue Jun 4 01:07:25 2024 -0400

    Add dan-seol to Contributors list (#84962)

commit 4af4ec8a56e057ce8768af77eda528453974d0bc
Author: Edgar Humberto Tijerina Tamez <168693312+EdgarHTT@users.noreply.github.com>
Date:   Mon Jun 3 23:06:05 2024 -0600

    Add Edgar Tijerina to Contributors list (#84961)
```


## Command variations and options 
- In order to perform the commits reachable from a particular commit ids: <i>(In this case, `foo` and `bar`)</i><br>
    `git log foo bar ` 
- It is also possible to remove the commits reachable from a given commit id by adding a `^` in front of commit id: <i>(In this case, `baz`)</i><br>
    `git log foo bar ^baz`
- Commit log for a particular file: <br> 
    `git log --all <filename>`
- Limit number of commits in log: <i>(In this case, `5`)</i><br> 
    `git log -n 5`

## Recovering a commit that disappeared from the log

`git log` lists only commits that can be reached from a branch. If a branch is moved back by mistake, for example with `git reset --hard`, the commits it skipped disappear from the log. Git has not deleted them yet, and the reflog records where the branch used to point.

The example below uses a throw-away repository, because `git reset --hard` discards changes. `main` has commits A, B and C, and `topic` points at B.

Check the log and note the commit ids and the tree id of `main`:

```
git log --oneline -n 3
git rev-parse main^{tree}
```

The mistake: reset `main` to B, thinking "go back one commit":

```
git reset --hard <id-of-B>
```

Now `git log` lists only B and A. `git log --all` does too, because no branch points at C any more. Only `main` has moved; `topic` is unchanged.

The recovery point is the reflog entry from before the reset. List the reflog and copy the id of the commit you lost (here, the entry whose message ends with "C: add todo.txt"):

```
git reflog
```

Move `main` back to it. Right after the mistake, `main@{1}` is the same commit:

```
git reset --hard <id-of-C>
```

Verify the result:

```
git log --oneline
git status
git rev-parse main^{tree}
```

`git log` lists C, B and A again, `git status` is clean, and the tree id printed by `git rev-parse main^{tree}` equals the one you noted before the mistake.

What this cannot recover:

- Uncommitted changes to tracked files. `git reset --hard` throws them away, and no commit or reflog entry holds them.
- Commits whose reflog entries have expired and been removed by `git gc`.
- Anything on another machine. The reflog is local to your repository and is not pushed.

## Refer
- [Official documentation](https://git-scm.com/docs/git-log)
