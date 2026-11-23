# Installing Git on Arch Linux

To install Git on Arch Linux, you can use the package manager pacman. First, open a terminal and update the system with the following command:

```shell
$ sudo pacman -Syu
```

Next, install Git by running:

```shell
$ sudo pacman -S git
```

To confirm that Git has been installed correctly, run the following command:

```shell
$ git --version
```

You should see output similar to:

```shell
Output
$ git version 2.34.1
```

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

# Persist Git Credentials

By default, Git will prompt you to re-enter your username and password every time you interact with a remote repository. You can configure Git to cache or store your credentials to avoid this. Below are two common methods:

### 1. Credential Caching

Git can temporarily store your credentials in memory, so you don't need to re-enter them frequently. Run the following command to enable credential caching:

```shell
$ git config --global credential.helper cache
```

By default, credentials will be cached for 15 minutes. To adjust the timeout period (e.g., 1 hour), use:

```shell
$ git config --global credential.helper 'cache --timeout=3600'
```

---

### 2. Credential Storing

If you prefer to store your credentials permanently in plain text (less secure but convenient), you can use the following command:

```shell
$ git config --global credential.helper store
```

When using this method, your credentials will be saved in plain text in `~/.git-credentials`. Be cautious with this approach, especially on shared or public machines.

# Worked Exercise: Predict, Execute, and Verify Git State and Identity

After installing and configuring Git, verify your configuration and understand how Git records identity and manages references, index (staging area), and working tree state across branch switches.

### Exercise Scenario Setup

Consider a repository created with branch `main` and configured with user identity:
- **Author/Committer**: `Course Student <student@example.invalid>`
- **Commit A**: creates `notes.txt` with content `"alpha\n"`
- **Commit B**: appends `"beta\n"` to `notes.txt` (content is `"alpha\nbeta\n"`)
- Branch `topic` created pointing to Commit B
- **Commit C**: adds `todo.txt` with content `"one\n"` on branch `main`

The initial state on branch `main` at Commit C is:
- `HEAD` points to `refs/heads/main`
- `main` points to Commit C (tree contains `notes.txt` and `todo.txt`)
- `topic` points to Commit B (tree contains only `notes.txt`)

### 1. Predict the State Transition

We want to switch branches from `main` to `topic`:

```shell
$ git checkout topic
```

Before executing this command, predict the resulting Git state:

| State Layer | Predicted State After `git checkout topic` |
| :--- | :--- |
| **Active Reference (`HEAD`)** | `HEAD` updates from pointing to `refs/heads/main` to pointing to `refs/heads/topic` (symbolic ref). |
| **Branch References** | `refs/heads/main` remains unchanged at Commit C; `refs/heads/topic` remains unchanged at Commit B. |
| **Index (Staging Area)** | Updated to match the tree of Commit B: contains `notes.txt` (version from Commit B); `todo.txt` is removed from the index. |
| **Working Tree** | Updated to match Commit B: `notes.txt` has content `"alpha\nbeta\n"`; `todo.txt` is removed from disk; `git status --porcelain` is clean (no untracked or modified files). |
| **Author Identity** | In commits A, B, and C, author and committer metadata is permanently recorded as `Course Student <student@example.invalid>`. |

### 2. Execute and Verify

Run the following commands in the repository to execute and verify the predicted state:

```shell
# 1. Switch to the topic branch
$ git checkout topic
Switched to branch 'topic'

# 2. Verify active reference and branch positions
$ git symbolic-ref HEAD
refs/heads/topic

$ git rev-parse HEAD
# Output matches the SHA-1 of Commit B

$ git rev-parse topic
# Output matches the SHA-1 of Commit B

$ git rev-parse main
# Output matches the SHA-1 of Commit C

# 3. Verify index contents
$ git ls-files -s
100644 <blob-sha-notes-b> 0	notes.txt

# 4. Verify working tree files and contents
$ cat notes.txt
alpha
beta

$ test ! -f todo.txt && echo "todo.txt absent as predicted"
todo.txt absent as predicted

$ git status --porcelain
# (empty output: working tree clean)

# 5. Verify commit author identity
$ git log -1 --format="%an <%ae>" main
Course Student <student@example.invalid>

$ git log -1 --format="%an <%ae>" topic
Course Student <student@example.invalid>
```

### 3. Explanation of Results

1. **Symbolic Reference Update**: The command `git checkout topic` updates the symbolic reference file `.git/HEAD` to contain `ref: refs/heads/topic`. Git does not detach `HEAD` because `topic` is an existing local branch.
2. **Index and Working Tree Synchronization**: Git synchronizes both the staging index (`.git/index`) and the working directory files to match the tree of the destination commit (Commit B). Because `todo.txt` existed in Commit C but does not exist in Commit B, Git safely removes `todo.txt` from the index and disk since it had no uncommitted changes.
3. **Identity Immutability**: The configured `user.name` and `user.email` are embedded into each commit object at creation time. Changing configuration or switching branches has zero retroactive effect on existing commit objects, ensuring cryptographic immutability.
