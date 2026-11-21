# Configuring git

The first time you tried to commit using git, you might have gotten a prompt like the one below:

```bash
$ git commit
*** Please tell me who you are.

Run

git config --global user.email "you@example.com"
git config --global user.name "Your Name"

to set your account's default identity.
Omit --global to set the identity only in this repository.
```

Git needs to know who you are when you create a commit. When you are working collaboratively, you should be able to see who modified what parts of the project and when, and thus, git has been designed to create commits tied to a name and an email.

There are multiple ways to provide the `git commit` command with your email and name, and we'll go through some of them below.

### Global Config

When you store something in the global config, it is accessible system wide in all the repositories you work on. This is the preferred way and works for most use cases.

To store something in the global config, you use the `config` command as follows:

`$ git config --global <variable name> <value>`

In the case of user details, we run it as follows:

```
$ git config --global user.email "you@example.com"
$ git config --global user.name "Your Name"
```

### Repository Config

As the name says, these configurations are scoped to your current repository. If you want to commit to a particular repository, say, a work related project, with your company's email, then you could use this method.

To store something in the repository config, you use the `config` command  by omitting the `--global` flag as follows:

`$ git config <variable name> <value>`

In the case of user details, we run it as follows:

```
$ git config user.email "you@alternate.com"
$ git config user.name "Your Name"
```

### Command-line Config

These type of configurations are scoped to the current command only. All git commands take `-c` arguments before the action verb to set temporary configuration data.

To store something in the command line config, run your command as follows:

`$ git -c <variable-1>=<value> -c <variable-2>=<value> <command>`

In our example, we would run the commit command as follows:

`git -c user.name='Your Name' -c user.email='you@example.com' commit -m "Your commit message"`

### Note on Precedence

Among the three methods described here, the precedence order is `command-line > repository > global`. This means that, if a variable is configured in the command-line as well as globally, the command-line value would be used for the operation.

## Beyond User Details

We have dealt with only the user details till now while working with the config. However, there are several other configuration options available. Some of them are:

1.  `core.editor` - to specify the name of the editor used for writing commit messages, etc.
2.  `commit.template` - to specify a file on the system as the initial commit template.
3.  `color.ui` - to specify a boolean value for using colors in git's output.

We have abstracted some details for ease of understanding. For further reading, head over to [git-scm.com](https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration).

---

## Comparison: Global Config vs. Local Repository Config

When setting your identity, Git allows you to choose between configuring settings globally (`--global`) or restricting them to a specific repository (`--local`).

### Comparison Table

| Attribute | Global Config (`git config --global`) | Local Repository Config (`git config --local`) |
|---|---|---|
| **Primary Use Case** | Setting default identity for personal machine | Setting custom/work identity for a specific repository |
| **Preconditions** | User is on their own machine, wants identity everywhere | User is inside a specific Git repository directory |
| **Target Storage** | `~/.gitconfig` (user's home directory) | `.git/config` (inside repository's `.git` folder) |
| **Precedence** | Lower (`local` overrides `global`) | Higher (takes precedence over `global`) |
| **Scope of Impact** | Affects all current and future repositories on the machine | Strictly isolated to the current repository |
| **Resulting Commit State** | Commits in any repository without local config use global identity | Commits in this repository use local identity |

---

### Reproducible Example: Demonstrating the Observable Difference

The following example demonstrates both approaches from equivalent initial fixtures and observes the difference in commit author metadata and config isolation.

#### 1. Repository Setup

We create a temporary repository with author `Course Student <student@example.invalid>` on branch `main` with three initial commits:
- **Commit A**: `notes.txt` with `"alpha\n"`
- **Commit B**: appends `"beta\n"` to `notes.txt`
- **Commit C**: `todo.txt` with `"one\n"`
- Branch `topic` created at Commit B.

```bash
# Global configuration
git config --global user.name "Course Student"
git config --global user.email "student@example.invalid"

# Initialize repository
git init -b main repo
cd repo

# Commit A
printf "alpha\n" > notes.txt
git add notes.txt
git commit -m "Commit A: create notes.txt"

# Commit B
printf "beta\n" >> notes.txt
git add notes.txt
git commit -m "Commit B: append beta to notes.txt"
COMMIT_B=$(git rev-parse HEAD)

# Branch topic at Commit B
git branch topic "$COMMIT_B"

# Commit C
printf "one\n" > todo.txt
git add todo.txt
git commit -m "Commit C: add todo.txt"
```

Verify initial commits:

```bash
$ git log -1 --format="%an <%ae>"
Course Student <student@example.invalid>
```

#### 2. Workflow 1: Committing with Global Configuration

In a clean repository using only the global identity:

```bash
printf "item\n" > item.txt
git add item.txt
git commit -m "Commit via global identity"
```

Verify the recorded author and committer:

```bash
$ git log -1 --format="Author: %an <%ae>%nCommitter: %cn <%ce>"
Author: Course Student <student@example.invalid>
Committer: Course Student <student@example.invalid>
```

#### 3. Workflow 2: Overriding Identity with Local Configuration

In the same repository (or an equivalent fixture), set local identity:

```bash
git config --local user.name "Project Contributor"
git config --local user.email "contributor@project.invalid"
```

Now create a commit in the repository:

```bash
printf "update\n" > update.txt
git add update.txt
git commit -m "Commit via local identity"
```

Verify the recorded author and committer:

```bash
$ git log -1 --format="Author: %an <%ae>%nCommitter: %cn <%ce>"
Author: Project Contributor <contributor@project.invalid>
Committer: Project Contributor <contributor@project.invalid>
```

#### 4. Observable Differences

1. **Config File Location**:
   - `git config --global --list` shows `user.name=Course Student` stored in `~/.gitconfig`.
   - `git config --local --list` shows `user.name=Project Contributor` stored in `.git/config`.
2. **Isolation Across Repositories**:
   - If you create a second repository, `git log` in the second repository automatically falls back to `Course Student <student@example.invalid>`.
   - The local override `Project Contributor` has zero effect outside of its own `.git` directory.
