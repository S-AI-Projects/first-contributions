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

---

# Automated Guide Verification

To ensure that your Git installation, global user configuration (`user.name` and `user.email`), and credential helpers are functioning properly without polluting your personal host environment, this guide includes an automated integration test located at `tests/guides/test_installing_git_arch.py`.

### Running the Test

Run the test suite using Python's built-in `unittest` runner:

```shell
$ python3 -m unittest tests/guides/test_installing_git_arch.py
```

### What the Test Verifies

1. **Git Installation & Version**: Verifies that the `git` binary is accessible on the system and reports a valid version string matching `git --version`.
2. **User Identity Configuration**: Verifies configuring `user.name` and `user.email` globally and confirms both values appear in `git config --list`.
3. **Commit Metadata Attribution**: Creates a test commit in an isolated repository to verify that Git embeds the configured identity into commit author headers (`git log -1 --format="%an <%ae>"`).
4. **Credential Helper Configuration**: Verifies setting and retrieving `credential.helper` configuration.
