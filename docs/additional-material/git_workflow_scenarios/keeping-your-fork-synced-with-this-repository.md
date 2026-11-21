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

## Two ways to integrate upstream

After configuring the `upstream` remote, you can make the fetch and integration steps explicit:

```sh
git fetch upstream
git switch main
git rebase upstream/main
```

Or fetch and rebase in one command:

```sh
git switch main
git pull --rebase upstream main
```

Both update local `main` with upstream's commits. The first leaves `upstream/main` as an inspectable remote-tracking ref after fetch and lets you review it before rebasing. `pull --rebase` fetches and rebases immediately, so there is no pause to inspect before integration. Both replay local-only commits and can stop for conflicts; resolve them before continuing. With plain `git pull upstream main`, Git merges by default unless configured otherwise, which can create a merge commit when the histories have diverged. These commands update your local branch; pushing `main` to `origin` is a separate step that updates your fork.

## Check prerequisites before syncing

Before running the sync commands, confirm:

- You are inside the intended clone (`git rev-parse --show-toplevel`).
- `main` exists locally and is the branch you intend to update (`git branch --show-current`). Save or commit work before switching; check both staged and unstaged changes with `git status --short`.
- `origin` points to your fork and `upstream` points to the source repository (`git remote -v`). Add `upstream` only if it is absent; do not add a duplicate remote.
- If you will create commits during conflict resolution, a repository-local `user.name` and `user.email` are configured. Set them with `git config user.name 'Course Student'` and `git config user.email 'student@example.invalid'`; omit `--global` to avoid changing identity for other repositories.

A minimal safe setup is:

```sh
git status --short --branch
git remote -v
git config --local user.name 'Course Student'
git config --local user.email 'student@example.invalid'
# Only when upstream is not already listed:
git remote add upstream https://github.com/firstcontributions/first-contributions.git
```

Keep a clean working tree before switching to `main`. The local config commands are examples; use your own commit identity in your repository.
