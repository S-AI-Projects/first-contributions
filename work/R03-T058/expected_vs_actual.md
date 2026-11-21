| check | expected | actual | ok |
|---|---|---|---|
| commands run only inside the temp repo | `true` | `true` | yes |
| start: current branch is main | `"main"` | `"main"` | yes |
| start: main is E, C, B, A | `["E: change line 2 on main", "C: add todo.txt", "B: append beta", "A: create notes.txt"]` | `["E: change line 2 on main", "C: add todo.txt", "B: append beta", "A: create notes.txt"]` | yes |
| start: topic is D, B, A | `["D: change line 2 on topic", "B: append beta", "A: create notes.txt"]` | `["D: change line 2 on topic", "B: append beta", "A: create notes.txt"]` | yes |
| start: authors are Course Student | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | yes |
| start: the working tree is clean | `""` | `""` | yes |
| start: git status says so in words | `true` | `true` | yes |
| start: name and email come from the repository's own config | `["Course Student", "student@example.invalid"]` | `["Course Student", "student@example.invalid"]` | yes |
| start: no merge is in progress | `null` | `null` | yes |
| merge: git merge topic exits with status 1 | `1` | `1` | yes |
| merge: git reports a content conflict in notes.txt | `true` | `true` | yes |
| conflict: git status names the current branch | `true` | `true` | yes |
| conflict: git status says there are unmerged paths | `true` | `true` | yes |
| conflict: git status --short shows UU for notes.txt only | `["UU notes.txt"]` | `["UU notes.txt"]` | yes |
| conflict: MERGE_HEAD is D, the tip of topic | `"1b3fd7813d87258c7a17dace7a42d79037f77142"` | `"1b3fd7813d87258c7a17dace7a42d79037f77142"` | yes |
| conflict: no commit was made, main is still E | `"070efb552da0c3dfd37f4575a07128d6ea961cb7"` | `"070efb552da0c3dfd37f4575a07128d6ea961cb7"` | yes |
| conflict: the index holds three versions of notes.txt (base B, ours E, theirs D) | `[[1, "fbbee861521bd5355538b096fa3998541cd33909", "notes.txt"], [2, "2f4d31084a6d0e66680fe59f9552b10a8bfadfc7", "notes.txt"], [3, "1f082a118551d29f5baa0bf16dd47648eaf4b0f9", "notes.txt"]]` | `[[1, "fbbee861521bd5355538b096fa3998541cd33909", "notes.txt"], [2, "2f4d31084a6d0e66680fe59f9552b10a8bfadfc7", "notes.txt"], [3, "1f082a118551d29f5baa0bf16dd47648eaf4b0f9", "notes.txt"]]` | yes |
| conflict: notes.txt contains the conflict markers | `"alpha\n<<<<<<< HEAD\nbeta from main\n=======\nbeta from topic\n>>>>>>> topic\n"` | `"alpha\n<<<<<<< HEAD\nbeta from main\n=======\nbeta from topic\n>>>>>>> topic\n"` | yes |
| conflict: todo.txt was not touched | `"one\n"` | `"one\n"` | yes |
| conflict: git diff --check reports the leftover markers | `true` | `true` | yes |
| commit before git add: fails | `128` | `128` | yes |
| commit before git add: the complaint is about unmerged files | `true` | `true` | yes |
| commit before git add: nothing changed (still merging, still unmerged, main at E) | `["1b3fd7813d87258c7a17dace7a42d79037f77142", 3, "070efb552da0c3dfd37f4575a07128d6ea961cb7"]` | `["1b3fd7813d87258c7a17dace7a42d79037f77142", 3, "070efb552da0c3dfd37f4575a07128d6ea961cb7"]` | yes |
| resolved: no unmerged index entries are left | `[]` | `[]` | yes |
| resolved: git status --short shows the file as staged | `["M  notes.txt"]` | `["M  notes.txt"]` | yes |
| resolved: git status says all conflicts are fixed but the merge is not finished | `true` | `true` | yes |
| resolved: no conflict markers are left, staged or unstaged | `[0, 0]` | `[0, 0]` | yes |
| resolved: still merging (MERGE_HEAD is D) and main is still E | `["1b3fd7813d87258c7a17dace7a42d79037f77142", "070efb552da0c3dfd37f4575a07128d6ea961cb7"]` | `["1b3fd7813d87258c7a17dace7a42d79037f77142", "070efb552da0c3dfd37f4575a07128d6ea961cb7"]` | yes |
| commit without name/email: fails | `128` | `128` | yes |
| commit without name/email: the complaint is about the identity | `true` | `true` | yes |
| commit without name/email: the merge is still in progress, resolved file still staged | `["1b3fd7813d87258c7a17dace7a42d79037f77142", "070efb552da0c3dfd37f4575a07128d6ea961cb7", ["M  notes.txt"]]` | `["1b3fd7813d87258c7a17dace7a42d79037f77142", "070efb552da0c3dfd37f4575a07128d6ea961cb7", ["M  notes.txt"]]` | yes |
| done: the merge commit has two parents, E then D | `["f34545888ad099170edd7a8f29c450810108f48b", "070efb552da0c3dfd37f4575a07128d6ea961cb7", "1b3fd7813d87258c7a17dace7a42d79037f77142"]` | `["f34545888ad099170edd7a8f29c450810108f48b", "070efb552da0c3dfd37f4575a07128d6ea961cb7", "1b3fd7813d87258c7a17dace7a42d79037f77142"]` | yes |
| done: the commit message is the guide's | `"Resolved merge conflicts"` | `"Resolved merge conflicts"` | yes |
| done: author is Course Student | `"Course Student <student@example.invalid>"` | `"Course Student <student@example.invalid>"` | yes |
| done: MERGE_HEAD is gone, the working tree is clean | `[null, ""]` | `[null, ""]` | yes |
| done: notes.txt has the resolved content | `"alpha\nbeta from main and topic\n"` | `"alpha\nbeta from main and topic\n"` | yes |
| done: the committed notes.txt is the resolved content | `"alpha\nbeta from main and topic\n"` | `"alpha\nbeta from main and topic\n"` | yes |
| done: only refs/heads/main changed; topic is still D | `[["refs/heads/main"], "1b3fd7813d87258c7a17dace7a42d79037f77142"]` | `[["refs/heads/main"], "1b3fd7813d87258c7a17dace7a42d79037f77142"]` | yes |
| done: main is the merge commit | `"f34545888ad099170edd7a8f29c450810108f48b"` | `"f34545888ad099170edd7a8f29c450810108f48b"` | yes |
| global config: user.name is not set | `1` | `1` | yes |
| global config: no .gitconfig was created in the temporary HOME | `false` | `false` | yes |
