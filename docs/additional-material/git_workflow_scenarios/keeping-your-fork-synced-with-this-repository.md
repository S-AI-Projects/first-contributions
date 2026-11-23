# Keeping your fork synced with this repository

First, the flow for a full sync should be understood, which is important. In this schema, there are 3 different repos: my public repo on Github `github.com/firstcontributions/first-contributions.git`, your fork of the repo on GitHub `github.com/Your-Name/first-contributions/` and your local machine's repo from which you are suppose to work. This kind of cooperation is typical for open source projects and called `Triangle Workflows`.

<img style="float;" src="https://firstcontributions.github.io/assets/additional-material/triangle_workflow.png" alt="triangle workflow" />

To keep your two repos up-to-date with my public repo, we first have to fetch and merge the public repo with your local machine's repo.
Our second move will be to push your local repo to your GitHub fork. As you've seen earlier, it's only from your fork that you can ask for a "pull request". So your GitHub fork is the last repo to be updated.

Now, let's see how to do it:

First, you must be on your main branch. To know which branch you are on, check the first line of:
```
git status
```
if you are not already on main:
```
git checkout main
```

Then you should add my public repo to your git with `add upstream remote-url`:
```
git remote add upstream https://github.com/firstcontributions/first-contributions.git
```
This is a way of telling git that another version of this project exists in the specified url and we're calling it `upstream`. Once your git has a name let's fetch the latest version of the public repository:
```
git fetch upstream
```

You've just fetched the latest version of my fork (`upstream` remote). Now, you need to merge the public repository into your main branch.
```
git rebase upstream/main
```
Here you're merging the public repository with your main branch. Your local machine's main branch is now up-to-date. Lastly, if you push your main branch to your fork, your GitHub fork will also have the changes:
```
git push origin main
```
Notice here you're pushing to the remote named `origin`.

If you want to fetch and merge the latest changes of my fork (`upstream` remote) to your local branch at same time then you can directly go for:
```
git pull upstream main
```

So by now or at this point, all your repositories are up-to-date. Well done! You should do this, every time your GitHub repo tells you that you are a few commits behind.

## Troubleshooting Common Sync Failures

When synchronizing your fork, you may encounter command failures if certain preconditions are violated. Below are the most common failure scenarios, their underlying error categories, and the smallest corrections needed to fix them.

| Step | Triggering State | Error Category & Message | Violated Precondition | Corrected Command |
| :--- | :--- | :--- | :--- | :--- |
| `git remote add upstream <url>` | `upstream` is already configured in `.git/config` | Remote collision (`fatal: remote upstream already exists.`, exit code non-zero) | Remote alias must not already exist | `git remote set-url upstream <url>` |
| `git checkout main` | Current branch has untracked or modified files that exist on `main` | Checkout overwrite collision (`error: The following untracked working tree files would be overwritten by checkout...`, exit code non-zero) | Working tree files must not conflict with target branch tree | `git stash -u && git checkout main` |

---

### Failure 1: `fatal: remote upstream already exists.`

#### Triggering State
You previously configured the `upstream` remote (or set it up during a previous contribution), and run:
```bash
git remote add upstream https://github.com/firstcontributions/first-contributions.git
```

#### Git Diagnostic
Git exits with a non-zero exit code and outputs:
```
fatal: remote upstream already exists.
```

#### Why It Fails
The `git remote add` command requires that the specified remote name does not already exist in your local repository configuration.

#### Smallest Correction
Check your existing remotes first:
```bash
git remote -v
```
If `upstream` is already pointing to the correct URL, you do not need to add it again; proceed directly to `git fetch upstream`. If you need to update its URL, use `git remote set-url`:
```bash
git remote set-url upstream https://github.com/firstcontributions/first-contributions.git
```

---

### Failure 2: Conflicting changes when checking out `main`

#### Triggering State
You are working on a topic branch (e.g., `topic`), and your working tree contains uncommitted edits or untracked files that conflict with commits on `main`. Running:
```bash
git checkout main
```

#### Git Diagnostic
Git refuses to switch branches and exits with a non-zero exit code:
```
error: The following untracked working tree files would be overwritten by checkout:
    <file-name>
Please move or remove them before you switch branches.
Aborting
```

#### Why It Fails
Git protects your uncommitted work from being overwritten or lost when checking out a branch where that file already exists or has differing contents.

#### Smallest Correction
Safely stash your working changes (including untracked files with `-u`) before switching to `main`:
```bash
git stash -u
git checkout main
```
After completing your sync on `main`, switch back to your topic branch and restore your stashed work:
```bash
git checkout topic
git stash pop
```

