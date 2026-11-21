# Deleting a locally created Branch

This will be handy when you accidentally misspelled a branch name.

This can be done in *3* ways

```
git branch -D <branch_name>
```

```
git branch --delete --force <branch_name>  # Same as -D
```

```
git branch --delete  <branch_name>         # Error on unmerge
```

-D stands for --delete --force which will delete the branch even it's not merged (force delete), but you can also use -d which stands for --delete which throws an error respective of the branch merge status...

## Which branch is deleted?

Branch deletion affects a **local ref** in the repository where you run the command. It does not delete a branch from `origin`.

```sh
git switch topic
git branch --delete topic       # refuses: cannot delete the current branch
git switch main
git branch --delete topic       # refuses if topic has unmerged commits
git branch --delete --force topic  # removes local topic even when unmerged
git push origin --delete topic  # separate operation: deletes origin/topic
```

You cannot delete the branch that is currently checked out. For example, with `main` checked out and `topic` pointing to unmerged commit B, the safe `--delete` command refuses and leaves both refs unchanged. Switch to `main` before removing `topic`; `--force` discards only the local branch ref. A remote-tracking ref such as `origin/topic` is updated by fetch/prune, and a remote branch is removed only by an explicit push deletion like the final command.
