# Installing Git Ubuntu OS

Git by default is likely already installed in your Ubuntu OS . You can confirm this by launching your terminal and entering following command in to your terminal:

```shell
$ git --version
```

If you receive output similar to the following, then Voila! you have readily installed Git on your machine.

```shell
Output
$ git version 2.34.1
```

If this applies to you, proceed to [set up git](#set-up-git) below.

If a Git version number was not on the output as shown above, you can still install it using Ubuntu's APT default package manager.

Update your local package index first by using the apt package management tools. Head back to your terminal and enter the following command.

```shell
$ sudo apt update
```

Once this is completed, then enter the following command to install in Git:

```shell
$ sudo apt install git
```

You can confirm that you have installed Git correctly by running the following command and checking that you receive relevant output.

```shell
$ git --version
```

```shell
Output
$ git version 2.34.1
```

With Git successfully installed, you can now proceed below by setting it up.

# Set up Git

Configuration can be achieved by using the git config command.
Specifically, you need to provide your name and email address because Git embeds this information into each commit you do.
You can add this information by typing:

Now that we are done with installing Git, let us configure it for first time use using "git config" command.
We need to make sure your username and email address are set correctly. To set them, use the command:

```shell
$ git config --global user.name "Your Name"
$ git config --global user.email "youremail@domain.com"
```

You can display all the configuration items that have been set by entering the following command in your terminal:

```shell
$ git config --list
```

If all config field have been set up to your need the output should look something like

```shell
user.name=Your Name
user.email=youremail@domain.com
```

...

# Persist Git Credentials

By default, Git will keep asking you for your details everytime you want to push to a remote repo.
In Git, you can configure the caching of your credentials to avoid entering your username and password repeatedly. There are a couple of methods to achieve this:

1. Credential caching: Git provides a credential caching system that can store your credentials in memory for a specified period. This way, you don't have to re-enter your details every time you interact with a remote repository.

To enable credential caching, you can use the following command:

```shell
$ git config --global credential.helper cache
```

By default, Git will cache your credentials for 15 minutes. You can adjust the cache timeout period by specifying the --timeout option followed by the desired number of seconds.

For example, to set the cache timeout to 1 hour (3600 seconds), you can use:

```shell
$ git config --global credential.helper 'cache --timeout=3600'

```

2. Credential Storing: This sets Git's credential helper to "store". When using this credential helper, Git will store the credentials for a remote repository in a plain-text file on disk. This method is the simplest but least secure option for credential storage.

```shell
$ git config --global crednetial.helper store
```

With the store credential helper, the credentials entered for a remote repository will be stored permanently in a file located at ~/.git-credentials on Linux or macOS, or %USERPROFILE%\.git-credentials on Windows. The credentials will be stored in plain text format, which means they are readable if someone gains access to the file.

The advantage of using the store credential helper is that you won't be prompted for credentials every time you interact with the remote repository. However, keep in mind the security implications of storing credentials in plain text, especially if you are using a shared or public machine.

# Git State Transition: From Install to First Commit

Understanding what Git "sees" at each stage helps you verify that your installation and configuration are working correctly. This section walks through the observable state transitions from a fresh install to your first commit.

## Stage 1 — Before Git is installed

Before Git is installed, any git command returns an error:

```shell
$ git --version
# bash: git: command not found
```

**State**: Git binary absent; no repository can exist.

## Stage 2 — After installation, before configuration

Immediately after `sudo apt install git`, the binary is available but no global identity has been set:

```shell
$ git --version
git version 2.34.1

$ git config --global user.name
# (no output — value is unset)

$ git config --global user.email
# (no output — value is unset)
```

**State**: Git installed, global config empty.

Attempting a commit at this stage will fail because Git cannot attach an author identity:

```shell
$ git commit -m "initial commit"
# Author identity unknown
#
# *** Please tell me who you are.
#
# Run
#
#   git config --global user.email "you@example.com"
#   git config --global user.name "Your Name"
```

## Stage 3 — After configuration, before `git init`

Once you set your name and email, the global config is populated:

```shell
$ git config --global user.name "Course Student"
$ git config --global user.email "student@example.invalid"

$ git config --list
user.name=Course Student
user.email=student@example.invalid
```

**State**: Git configured globally; still no repository in the working directory.

```shell
$ git status
# fatal: not a git repository (or any of the parent directories): .git
```

## Stage 4 — After `git init`

Initialising a repository creates the `.git/` directory and sets HEAD to point to the default branch (`main`):

```shell
$ mkdir my-project && cd my-project
$ git init
Initialized empty Git repository in /home/user/my-project/.git/

$ git status
On branch main

No commits yet

nothing to commit (create/copy files and use "git add" to tell Git what to track)
```

**State**: Empty repository. HEAD → `main` (unborn branch — no commits yet).

## Stage 5 — After staging a file (`git add`)

```shell
$ echo "alpha" > notes.txt
$ git add notes.txt

$ git status
On branch main

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   notes.txt
```

**State**: `notes.txt` moved from *untracked* → *staged* (index). HEAD still points to unborn `main`.

## Stage 6 — After the first commit (`git commit`)

```shell
$ git commit -m "commit A: add notes.txt"
[main (root-commit) a1b2c3d] commit A: add notes.txt
 1 file changed, 1 insertion(+)
 create mode 100644 notes.txt

$ git log --oneline
a1b2c3d (HEAD -> main) commit A: add notes.txt

$ git status
On branch main
nothing to commit, working tree clean
```

**State**: One commit object created. HEAD → `main` → commit `a1b2c3d`. Working tree and index match the commit — clean state.

## State Transition Summary

| Stage | `git status` result | HEAD target |
|---|---|---|
| Before install | command not found | — |
| Installed, unconfigured | depends on directory | — |
| Configured, no repo | fatal: not a git repository | — |
| After `git init` | No commits yet | `main` (unborn) |
| After `git add` | Changes to be committed | `main` (unborn) |
| After first `git commit` | nothing to commit, working tree clean | `main` → commit hash |

## Reproducible Walkthrough

You can verify every state above in a temporary directory without touching your real projects:

```shell
# 1. Create isolated environment
mkdir /tmp/git-state-demo && cd /tmp/git-state-demo

# 2. Confirm git is installed
git --version            # git version 2.34.1

# 3. Confirm config
git config --global user.name    # Course Student
git config --global user.email   # student@example.invalid

# 4. Initialise
git init
git status               # No commits yet

# 5. Stage
echo "alpha" > notes.txt
git add notes.txt
git status               # Changes to be committed: new file: notes.txt

# 6. Commit
git commit -m "commit A: add notes.txt"
git log --oneline        # a1b2c3d (HEAD -> main) commit A: add notes.txt
git status               # nothing to commit, working tree clean

# 7. Clean up
cd /tmp && rm -rf /tmp/git-state-demo
```

Each command's output directly reflects the state transition described in the table above.
