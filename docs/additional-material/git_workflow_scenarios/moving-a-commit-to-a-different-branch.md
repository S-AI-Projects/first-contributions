# Moving a commit to a different branch
What if you commit a change, and then realize that you committed to a different branch?
How can you change that? This is what this tutorial covers.

## Moving the latest commits to an existing branch
To do this, type:

```git reset HEAD~ --soft``` - Undoes the last commit, but leaves the changes available.  
```git stash``` - Records the state of the directory.  

```git checkout name-of-the-correct-branch``` - Switches to another branch.
```git stash pop``` - Removes latest stashed state.  
```git add .``` - Or try adding individual files.  
```git commit -m "your message here"``` - Saves and Commits the changes.  

Now your changes are on the correct branch


### Moving the latest commits to a new Branch
To do this, type:  
```git branch newbranch``` -  Creates a new Branch. Saving all the Commits.  
```git reset --hard HEAD~#``` - Move the current branch back by # commits. Remember, these commits will be gone from it  
```git checkout newbranch``` - Goes to the branch you created. It will have all the commits.  

Remember: Any changes not committed will be LOST.

## Troubleshooting: switching branches with local edits

The `checkout` step assumes your working tree will not overwrite files that differ on the destination branch. Reproduce a common failure in a disposable repository: edit a tracked file on `main` without committing it, then switch to `topic`, where that path is absent or has a different version. Git exits unsuccessfully because the uncommitted edit would be overwritten. The exact wording varies by Git version; the error category is an overwrite protection refusal.

The smallest correction is to preserve the edit before switching:

```sh
git stash push -m 'work before switching'
git checkout topic
# If the edit belongs on main, return there before applying it.
git checkout main
git stash pop
```

If the edit belongs on `topic`, apply it there only when it does not conflict with topic files; otherwise return to `main` before applying the stash, as shown. Commit the edit on the branch where it belongs. `git stash pop` can itself report conflicts when both versions changed; resolve those before continuing. Do not use `git reset --hard` to silence the error unless you intend to discard the work.
