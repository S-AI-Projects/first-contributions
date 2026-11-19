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

## Troubleshooting: `git commit` says it does not know who you are

**Triggering state.** You staged a change and ran `git commit`, but git cannot find a `user.name` and a `user.email` in any of the three places described above (command line, repository, global), and it cannot guess them from your computer. You can check this with `git var GIT_AUTHOR_IDENT`, which fails in the same way when no identity is available.

**Error category.** This is a fatal configuration error, not a problem with your change. `git commit` exits with a nonzero status (typically 128) and creates no commit. The exact wording of the message differs between git versions and between computers (on some computers git guesses a name and email, so you may never see it), so look for "Author identity unknown" or "Please tell me who you are" rather than for the exact text. Your change is not lost: it is still staged.

```
$ git commit -m "Add gamma"
Author identity unknown

*** Please tell me who you are.
...
$ git status --short
M  notes.txt
```

**Smallest correction.** Tell git who you are, then run the same commit command again. Nothing else needs to change:

```
$ git config user.email "you@example.com"
$ git config user.name "Your Name"
$ git commit -m "Add gamma"
```

These two settings apply to this repository only. Use the `--global` versions from the message above to set them once for every repository, or supply them for a single command with `git -c user.name='Your Name' -c user.email='you@example.com' commit -m "Add gamma"`. A `-c` setting is not saved, so the next plain `git commit` fails again.

Once the identity is stored with `git config` (with or without `--global`), `git var GIT_AUTHOR_IDENT` prints your name and email, and `git log -1` shows them on the new commit.

## Beyond User Details

We have dealt with only the user details till now while working with the config. However, there are several other configuration options available. Some of them are:

1.  `core.editor` - to specify the name of the editor used for writing commit messages, etc.
2.  `commit.template` - to specify a file on the system as the initial commit template.
3.  `color.ui` - to specify a boolean value for using colors in git's output.

We have abstracted some details for ease of understanding. For further reading, head over to [git-scm.com](https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration).
