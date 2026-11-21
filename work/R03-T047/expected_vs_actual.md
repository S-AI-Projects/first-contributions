| check | expected | actual | ok |
|---|---|---|---|
| run1: Prereq 1 - inside work tree | `"true"` | `"true"` | yes |
| run1: Prereq 2 - current branch is main | `"main"` | `"main"` | yes |
| run1: Prereq 3 - working tree clean | `""` | `""` | yes |
| run1: Prereq 4 - commit B exists in rev-list | `true` | `true` | yes |
| run1: Prereq 5 - local user.name is Course Student | `"Course Student"` | `"Course Student"` | yes |
| run1: git reset commit_b exits 0 | `0` | `0` | yes |
| run1: Fact 1 - HEAD points to commit B | `"ea93e9f8511580ffb66054a2a316c6c5a35a17c5"` | `"ea93e9f8511580ffb66054a2a316c6c5a35a17c5"` | yes |
| run1: Fact 1b - refs/heads/main points to commit B | `"ea93e9f8511580ffb66054a2a316c6c5a35a17c5"` | `"ea93e9f8511580ffb66054a2a316c6c5a35a17c5"` | yes |
| run1: Fact 2 - main history contains [B, A] | `["ea93e9f8511580ffb66054a2a316c6c5a35a17c5", "b83e7b1d4d0a76b681a26324425ae68c3d962416"]` | `["ea93e9f8511580ffb66054a2a316c6c5a35a17c5", "b83e7b1d4d0a76b681a26324425ae68c3d962416"]` | yes |
| run1: Fact 3 - todo.txt is untracked | `["?? todo.txt"]` | `["?? todo.txt"]` | yes |
| run1: Fact 4a - todo.txt content preserved | `"one\n"` | `"one\n"` | yes |
| run1: Fact 4b - notes.txt content preserved | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | yes |
| run1: Fact 5 - branch topic still points to commit B | `"ea93e9f8511580ffb66054a2a316c6c5a35a17c5"` | `"ea93e9f8511580ffb66054a2a316c6c5a35a17c5"` | yes |
| run2: Prereq 1 - inside work tree | `"true"` | `"true"` | yes |
| run2: Prereq 2 - current branch is main | `"main"` | `"main"` | yes |
| run2: Prereq 3 - working tree clean | `""` | `""` | yes |
| run2: Prereq 4 - commit B exists in rev-list | `true` | `true` | yes |
| run2: Prereq 5 - local user.name is Course Student | `"Course Student"` | `"Course Student"` | yes |
| run2: git reset commit_b exits 0 | `0` | `0` | yes |
| run2: Fact 1 - HEAD points to commit B | `"ea93e9f8511580ffb66054a2a316c6c5a35a17c5"` | `"ea93e9f8511580ffb66054a2a316c6c5a35a17c5"` | yes |
| run2: Fact 1b - refs/heads/main points to commit B | `"ea93e9f8511580ffb66054a2a316c6c5a35a17c5"` | `"ea93e9f8511580ffb66054a2a316c6c5a35a17c5"` | yes |
| run2: Fact 2 - main history contains [B, A] | `["ea93e9f8511580ffb66054a2a316c6c5a35a17c5", "b83e7b1d4d0a76b681a26324425ae68c3d962416"]` | `["ea93e9f8511580ffb66054a2a316c6c5a35a17c5", "b83e7b1d4d0a76b681a26324425ae68c3d962416"]` | yes |
| run2: Fact 3 - todo.txt is untracked | `["?? todo.txt"]` | `["?? todo.txt"]` | yes |
| run2: Fact 4a - todo.txt content preserved | `"one\n"` | `"one\n"` | yes |
| run2: Fact 4b - notes.txt content preserved | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | yes |
| run2: Fact 5 - branch topic still points to commit B | `"ea93e9f8511580ffb66054a2a316c6c5a35a17c5"` | `"ea93e9f8511580ffb66054a2a316c6c5a35a17c5"` | yes |
