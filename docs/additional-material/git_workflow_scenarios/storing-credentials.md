# Storing Credentials

You might have complained about this before - entering your username and password each time you access the repository can be a hassle and can interrupt your workflow if it takes too long. But it doesn't need to be that way.

We will be covering one of the methods available to us - [git credential cache](https://git-scm.com/docs/git-credential-cache).

**Note:** Please follow the security policies of your place of work/study.

## Caching

We can use git credential cache to store our username and password.

**Attention:** This method saves the credentials in *plaintext* on your PC's disk. Everyone on your computer can access it, e.g. malicious NPM modules.

### Global Credential Cache

If we wish to, we can store the credentials for every repository we are working with using one simple command:

```
$ git config --global credential.helper cache
```

**Reminder:** Please follow the security policies of your place of work/study.

### Repository Credential Cache

We can store the credentials for the repository we are working with using one simple command, similar to before: 

```
$ git config credential.helper cache
```

**Reminder:** Please follow the security policies of your place of work/study.

### Cache Timeout

If we do not specify a length of time to store our credentials, they can potentially be stored forever. However, we can determine how long they will be kept in memory using this command:

```
git config credential.helper 'cache --timeout=<timeout>'
```

Using the helper, the credentials will never touch the disk and will be erased after the specified timeout. The default value is 900 seconds (15 minutes).

---

## Git State Transition Analysis

Configuring credential caching with `git config credential.helper cache` (or `--global`) modifies configuration files rather than repository history or the working tree. Below is a state diagram showing what changes—and what remains untouched—when configuring credential caching in a repository with three commits (A, B, C) and branch `topic` at B:

### State Before `git config credential.helper cache`

```text
Commit Ancestry:
  (A: notes.txt "alpha\n")
      ^
      |
  (B: notes.txt "alpha\nbeta\n") <--- [refs/heads/topic]
      ^
      |
  (C: todo.txt "one\n")          <--- [refs/heads/main] <--- HEAD

Refs:
  - HEAD -> refs/heads/main (Commit C)
  - refs/heads/main -> Commit C
  - refs/heads/topic -> Commit B

Index (Staging Area):
  - Clean (matches Commit C's tree: notes.txt, todo.txt)

Working Tree:
  - Clean (notes.txt: "alpha\nbeta\n", todo.txt: "one\n")

Configuration (.git/config):
  - credential.helper is unset
```

### State After `git config credential.helper cache`

```text
Commit Ancestry:
  (A: notes.txt "alpha\n")
      ^
      |
  (B: notes.txt "alpha\nbeta\n") <--- [refs/heads/topic] (UNCHANGED)
      ^
      |
  (C: todo.txt "one\n")          <--- [refs/heads/main] <--- HEAD (UNCHANGED)

Refs:
  - HEAD -> refs/heads/main (Commit C) [UNCHANGED]
  - refs/heads/main -> Commit C [UNCHANGED]
  - refs/heads/topic -> Commit B [UNCHANGED]

Index (Staging Area):
  - Clean (no files staged, index hash matches Commit C's tree) [UNCHANGED]

Working Tree:
  - Clean (no modified, untracked, or deleted files) [UNCHANGED]

Configuration (.git/config):
  - credential.helper = cache [CHANGED: configuration setting recorded]
```

### Key State Transition Summary

| Component | State Transition | Verification Command |
|---|---|---|
| **HEAD** | Unchanged (points to `refs/heads/main`) | `git symbolic-ref HEAD` |
| **`refs/heads/main`** | Unchanged (points to Commit C) | `git rev-parse refs/heads/main` |
| **`refs/heads/topic`** | Unchanged (points to Commit B) | `git rev-parse refs/heads/topic` |
| **Commit Ancestry** | Unchanged (A <- B <- C; 3 commits total) | `git rev-list --count HEAD` |
| **Index (Staging Area)** | Unchanged (clean, diff is empty) | `git diff --cached` |
| **Working Tree** | Unchanged (clean, porcelain status empty) | `git status --porcelain` |
| **Local Config** | Updated: `credential.helper=cache` | `git config --local credential.helper` |

#### References
[Stack Overflow](https://stackoverflow.com/questions/35942754/how-can-i-save-username-and-password-in-git)

### [Additional Material](additional-material.md)
