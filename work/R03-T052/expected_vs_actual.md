| check | expected | actual | ok |
|---|---|---|---|
| s1: current branch is topic | `"refs/heads/topic"` | `"refs/heads/topic"` | yes |
| s1: only main (at C) and topic (at B) exist | `{"refs/heads/main": "39a805ddd9f07e9cac5102304a3af856d834d9f4", "refs/heads/topic": "4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b"}` | `{"refs/heads/main": "39a805ddd9f07e9cac5102304a3af856d834d9f4", "refs/heads/topic": "4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b"}` | yes |
| s1: commit author is Course Student | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | yes |
| s1: `git log` lists B and A but not C | `[true, true, false]` | `[true, true, false]` | yes |
| s1: topic history is B, A | `["4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b", "8631e769fd2f9a9999e591a2a837b27361ef3bad"]` | `["4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b", "8631e769fd2f9a9999e591a2a837b27361ef3bad"]` | yes |
| s1: HEAD~2 does not exist on topic (only 2 commits) | `true` | `true` | yes |
| s1: `git rebase -i HEAD~2` fails on topic | `true` | `true` | yes |
| s1: failed rebase changed no refs | `{"refs/heads/main": "39a805ddd9f07e9cac5102304a3af856d834d9f4", "refs/heads/topic": "4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b"}` | `{"refs/heads/main": "39a805ddd9f07e9cac5102304a3af856d834d9f4", "refs/heads/topic": "4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b"}` | yes |
| s1: no rebase left in progress | `false` | `false` | yes |
| s2: current branch is topic | `"refs/heads/topic"` | `"refs/heads/topic"` | yes |
| s2: only main (at C) and topic (at B) exist | `{"refs/heads/main": "39a805ddd9f07e9cac5102304a3af856d834d9f4", "refs/heads/topic": "4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b"}` | `{"refs/heads/main": "39a805ddd9f07e9cac5102304a3af856d834d9f4", "refs/heads/topic": "4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b"}` | yes |
| s2: commit author is Course Student | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | yes |
| s2: main..topic is empty (nothing unique to squash) | `[]` | `[]` | yes |
| s2: topic..main is exactly C | `["39a805ddd9f07e9cac5102304a3af856d834d9f4"]` | `["39a805ddd9f07e9cac5102304a3af856d834d9f4"]` | yes |
| s2: main did not move | `"39a805ddd9f07e9cac5102304a3af856d834d9f4"` | `"39a805ddd9f07e9cac5102304a3af856d834d9f4"` | yes |
| s2: topic was fast-forwarded to main's tip, not squashed | `"39a805ddd9f07e9cac5102304a3af856d834d9f4"` | `"39a805ddd9f07e9cac5102304a3af856d834d9f4"` | yes |
| s2: history is still three commits | `3` | `3` | yes |
| s3: current branch is topic | `"refs/heads/topic"` | `"refs/heads/topic"` | yes |
| s3: only main (at C) and topic (at B) exist | `{"refs/heads/main": "39a805ddd9f07e9cac5102304a3af856d834d9f4", "refs/heads/topic": "4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b"}` | `{"refs/heads/main": "39a805ddd9f07e9cac5102304a3af856d834d9f4", "refs/heads/topic": "4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b"}` | yes |
| s3: commit author is Course Student | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | yes |
| s3: the only ref that changed is refs/heads/topic | `["refs/heads/topic"]` | `["refs/heads/topic"]` | yes |
| s3: refs/heads/main still points at C | `"39a805ddd9f07e9cac5102304a3af856d834d9f4"` | `"39a805ddd9f07e9cac5102304a3af856d834d9f4"` | yes |
| s3: new topic tip is a new commit (not A, B or C) | `true` | `true` | yes |
| s3: topic is now a single root commit | `1` | `1` | yes |
| s3: squashed commit has the same tree as old B | `"f85b72cccab2aab0cfca333f78ab1ff302be5f7b"` | `"f85b72cccab2aab0cfca333f78ab1ff302be5f7b"` | yes |
| s3: squashed commit message is the one we entered | `"Add notes.txt with alpha and beta"` | `"Add notes.txt with alpha and beta"` | yes |
| s3: main history untouched (C, B, A) | `["39a805ddd9f07e9cac5102304a3af856d834d9f4", "4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b", "8631e769fd2f9a9999e591a2a837b27361ef3bad"]` | `["39a805ddd9f07e9cac5102304a3af856d834d9f4", "4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b", "8631e769fd2f9a9999e591a2a837b27361ef3bad"]` | yes |
| s3: main..topic is exactly the squashed commit | `["ffa42a02fc5a9c52a98cf9ae8f2d3c73e13f4b20"]` | `["ffa42a02fc5a9c52a98cf9ae8f2d3c73e13f4b20"]` | yes |
| s3: topic and main have diverged (neither is an ancestor of the other) | `[1, 1]` | `[1, 1]` | yes |
| s3: old topic tip B is still recoverable via topic@{1} | `"4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b"` | `"4aa1b8e6ab3d91eb1e1c51fdafee52e8cec0582b"` | yes |
| s3: HEAD is still on topic | `"refs/heads/topic"` | `"refs/heads/topic"` | yes |
| s3: notes.txt content | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | yes |
| s3: todo.txt (from C) is not on topic | `false` | `false` | yes |
| s3: working tree clean | `""` | `""` | yes |
