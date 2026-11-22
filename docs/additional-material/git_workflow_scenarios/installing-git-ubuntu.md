# Installing Git Ubuntu OS

Git may already be installed on Ubuntu. Check by opening a terminal and
running:

```shell
$ git --version
```

If Git is installed, the command prints its version. The version number varies
by Ubuntu release and installation source; `2.34.1` below is only an example,
not a required version:

```shell
Output
$ git version 2.34.1
```

If this applies to you, proceed to [set up Git](#set-up-git) below.

If the command is not found, install Git using Ubuntu's APT package manager.

Update your local package index first by using the apt package management tools. Head back to your terminal and enter the following command.

```shell
$ sudo apt update
```

Once the package index update is complete, install Git:

```shell
$ sudo apt install git
```

After installation, run the same version command again. It reports the version
now available in your environment; it need not be `2.34.1`.

```shell
$ git --version
```

```shell
Output
$ git version 2.34.1
```

With Git installed, proceed below to configure it.

# Set up Git

Configure the name and email Git records in your commits. The `--global`
option saves these values for your user account and applies them to
repositories that do not override them with repository-specific settings:

```shell
$ git config --global user.name "Your Name"
$ git config --global user.email "youremail@domain.com"
```

You can display all the configuration items that have been set by entering the following command in your terminal:

```shell
$ git config --list
```

The output should contain the values you set, for example:

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
