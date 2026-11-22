# Removing a file from Git

Use `git rm --cached` when you want Git to stop tracking a file without
deleting your working copy:

```shell
git rm --cached <file>
```

## So what happened?

The removal is staged in the index, but the file remains in your working
directory. Git will no longer include it in the next commit unless you add it
again. By contrast, `git rm <file>` removes the file from both the index and
your working directory.

To publish the removal, commit it and push that commit to the remote branch:

```shell
git commit -m "Stop tracking <file>"
git push origin <branch>
```

The remote repository removes the file when it receives the commit. Running
`git rm --cached` by itself changes only your local index.

## Additional features

-   To stop tracking multiple files while retaining their working copies, list
    each path after `--cached`:

    ```shell
    git rm --cached file1.js file2.js file3.js
    ```

-   You can also use a shell wildcard. For example, stage removal of tracked
    text files while keeping the files on disk:

    ```shell
    git rm --cached -- '*.txt'
    ```
