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

# A complete example: check, configure, commit

This example starts in an empty folder and uses nothing that is not listed here. It shows what `git --version` and `git config --global user.name` do. Use your own name and email in the two `git config` lines.

**Note.** The two `git config --global` commands change your own global git configuration (usually `~/.gitconfig`). To try the example without touching it, first run `export HOME="$(mktemp -d)"` in a new terminal window. This only affects that window.

```
git --version
git config --global user.name "Your Name"
git config --global user.email "youremail@domain.com"
git init -b main
printf 'alpha\n' > notes.txt
git add notes.txt
git commit -m "A: create notes.txt"
printf 'beta\n' >> notes.txt
git commit -am "B: append beta"
printf 'one\n' > todo.txt
git add todo.txt
git commit -m "C: add todo.txt"
git branch topic HEAD~1
git switch topic
```

`git --version` prints the installed version, for example `git version 2.34.1`. Your number may be different.

The two `git config --global` commands write your name and email to the global config file. You can check what they did:

```
$ git config --global user.name
Your Name
$ git config --global --list
user.name=Your Name
user.email=youremail@domain.com
$ cat ~/.gitconfig
[user]
	name = Your Name
	email = youremail@domain.com
```

The `git config --list` command shown earlier prints exactly these two lines only when you run it outside a repository and nothing else is configured. Inside a repository it also lists the repository's own settings, for example `core.bare=false`. Use `git config --global --list` to see only the global ones.

After the example, the repository looks like this:

```
$ git status
On branch topic
nothing to commit, working tree clean
$ git branch
  main
* topic
$ git log --format='%an <%ae>: %s'
Your Name <youremail@domain.com>: B: append beta
Your Name <youremail@domain.com>: A: create notes.txt
$ git log --format='%an <%ae>: %s' main
Your Name <youremail@domain.com>: C: add todo.txt
Your Name <youremail@domain.com>: B: append beta
Your Name <youremail@domain.com>: A: create notes.txt
```

The name and email on every commit come from `git config --global`. The repository has no `user.name` of its own: `git config --local user.name` prints nothing. `main` has the three commits A, B and C. `topic` is checked out and points at B, so its log does not show C, and the index and the working tree contain only `notes.txt` with the lines `alpha` and `beta`. Running the example again in another empty folder gives the same files, branches, index and config file. Only the commit ids differ, because they depend on the time you commit.

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
