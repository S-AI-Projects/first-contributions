# Storing Credentials

You might have complained about this before - entering your username and password each time you access the repository can be a hassle and can interrupt your workflow if it takes too long. But it doesn't need to be that way.

We will be covering one of the methods available to us - [git credential cache](https://git-scm.com/docs/git-credential-cache).

**Note:** Please follow the security policies of your place of work/study.

## Caching

The `cache` helper keeps credentials in the memory of a Git credential-cache
daemon for a limited time. It does not write them to a plaintext credentials
file. The default timeout is 900 seconds (15 minutes); credentials can be
forgotten sooner if the daemon exits, for example when the system restarts.

This is temporary caching, not persistent credential storage.

### Global Credential Cache

To configure the cache helper at the global scope, run:

```
$ git config --global credential.helper cache
```

**Reminder:** Please follow the security policies of your place of work/study.

### Repository Credential Cache

To configure a helper for only the current repository, run this inside its
working tree:

```
$ git config credential.helper cache
```

**Reminder:** Please follow the security policies of your place of work/study.

Git reads configuration from multiple scopes. If a helper is configured both
globally and for a repository, the values can be combined rather than the
repository value automatically replacing the global value. Inspect the
effective values with:

```
git config --show-origin --get-all credential.helper
```

### Cache Timeout

To choose how many seconds credentials remain in the cache, set a timeout:

```
git config credential.helper 'cache --timeout=3600'
```

This example sets a one-hour timeout for the configured helper. Without an
explicit timeout, the cache helper uses its 900-second default. Cached
credentials remain in memory and are forgotten after the timeout or if the
cache daemon exits.

#### References
[Stack Overflow](https://stackoverflow.com/questions/35942754/how-can-i-save-username-and-password-in-git)

### [Additional Material](additional-material.md)