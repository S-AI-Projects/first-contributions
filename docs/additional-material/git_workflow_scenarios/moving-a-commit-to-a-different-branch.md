# Moving a commit to a different branch
What if you commit a change, and then realize that you committed to a different branch?
How can you change that? This is what this tutorial covers.

## Moving the latest commits to an existing branch
To do this, type:

```shell
git reset HEAD~ --soft
```

This moves the current branch back one commit but keeps that commit's changes
staged in the index. The changes are still available; they have not been
discarded.

```shell
git stash
git checkout name-of-the-correct-branch
git stash pop
```

`git stash` saves the staged changes and cleans the working tree so you can
switch branches. After checking out the correct branch, `git stash pop` reapplies
the saved changes and removes that stash entry if it applies successfully.
Review the restored changes, then stage and commit them on the correct branch:

```shell
git add <files>
git commit -m "your message here"
```

For example, if commit C was accidentally made on `main` after commit B, and
`topic` points to B, this sequence moves C's changes onto `topic`. `main` stays
at B, while `topic` receives a new commit containing the restored changes.


### Moving the latest commits to a new Branch
To do this, type:  
```git branch newbranch``` -  Creates a new Branch. Saving all the Commits.  
```git reset --hard HEAD~#``` - Move the current branch back by # commits. Remember, these commits will be gone from it  
```git checkout newbranch``` - Goes to the branch you created. It will have all the commits.  

Remember: Any changes not committed will be LOST.
