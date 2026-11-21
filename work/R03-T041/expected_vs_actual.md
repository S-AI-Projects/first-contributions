| check | expected | actual | ok |
|---|---|---|---|
| run1: commit A is ancestor of B | `0` | `0` | yes |
| run1: commit B is ancestor of C | `0` | `0` | yes |
| run1: branch topic points to commit B | `"240107be52a6dfd7429929273d804391c4b8ca61"` | `"240107be52a6dfd7429929273d804391c4b8ca61"` | yes |
| run1: branch main points to commit C | `"7902cc1df9f19fb8034433881ce30bdb56bc1497"` | `"7902cc1df9f19fb8034433881ce30bdb56bc1497"` | yes |
| run1: origin/main points to commit C | `"7902cc1df9f19fb8034433881ce30bdb56bc1497"` | `"7902cc1df9f19fb8034433881ce30bdb56bc1497"` | yes |
| run1: notes.txt content before removal | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | yes |
| run1: todo.txt content before removal | `"one\n"` | `"one\n"` | yes |
| run1: working tree is clean before removal | `""` | `""` | yes |
| run1: git rm --cached todo.txt exits 0 | `0` | `0` | yes |
| run1: Fact 1 - todo.txt is removed from index | `1` | `1` | yes |
| run1: Fact 1b - staged diff contains todo.txt deletion | `["todo.txt"]` | `["todo.txt"]` | yes |
| run1: Fact 2 - todo.txt exists on disk | `true` | `true` | yes |
| run1: Fact 2b - todo.txt content is preserved | `"one\n"` | `"one\n"` | yes |
| run1: Fact 3 - status shows staged deletion and untracked file | `["?? todo.txt", "D  todo.txt"]` | `["?? todo.txt", "D  todo.txt"]` | yes |
| run1: Fact 4a - commit D is distinct from C | `false` | `false` | yes |
| run1: Fact 4b - HEAD commit tree contains only notes.txt | `["notes.txt"]` | `["notes.txt"]` | yes |
| run1: Fact 4c - todo.txt still exists on disk after commit | `true` | `true` | yes |
| run1: Fact 5a - remote main ref matches commit D | `"77fbcbd0e691a9cf95879622daec7fd896f05c6c"` | `"77fbcbd0e691a9cf95879622daec7fd896f05c6c"` | yes |
| run1: Fact 5b - remote main tree does not contain todo.txt | `["notes.txt"]` | `["notes.txt"]` | yes |
| run1: Fact 6 - topic branch still points to commit B | `"240107be52a6dfd7429929273d804391c4b8ca61"` | `"240107be52a6dfd7429929273d804391c4b8ca61"` | yes |
| run2: commit A is ancestor of B | `0` | `0` | yes |
| run2: commit B is ancestor of C | `0` | `0` | yes |
| run2: branch topic points to commit B | `"240107be52a6dfd7429929273d804391c4b8ca61"` | `"240107be52a6dfd7429929273d804391c4b8ca61"` | yes |
| run2: branch main points to commit C | `"7902cc1df9f19fb8034433881ce30bdb56bc1497"` | `"7902cc1df9f19fb8034433881ce30bdb56bc1497"` | yes |
| run2: origin/main points to commit C | `"7902cc1df9f19fb8034433881ce30bdb56bc1497"` | `"7902cc1df9f19fb8034433881ce30bdb56bc1497"` | yes |
| run2: notes.txt content before removal | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | yes |
| run2: todo.txt content before removal | `"one\n"` | `"one\n"` | yes |
| run2: working tree is clean before removal | `""` | `""` | yes |
| run2: git rm --cached todo.txt exits 0 | `0` | `0` | yes |
| run2: Fact 1 - todo.txt is removed from index | `1` | `1` | yes |
| run2: Fact 1b - staged diff contains todo.txt deletion | `["todo.txt"]` | `["todo.txt"]` | yes |
| run2: Fact 2 - todo.txt exists on disk | `true` | `true` | yes |
| run2: Fact 2b - todo.txt content is preserved | `"one\n"` | `"one\n"` | yes |
| run2: Fact 3 - status shows staged deletion and untracked file | `["?? todo.txt", "D  todo.txt"]` | `["?? todo.txt", "D  todo.txt"]` | yes |
| run2: Fact 4a - commit D is distinct from C | `false` | `false` | yes |
| run2: Fact 4b - HEAD commit tree contains only notes.txt | `["notes.txt"]` | `["notes.txt"]` | yes |
| run2: Fact 4c - todo.txt still exists on disk after commit | `true` | `true` | yes |
| run2: Fact 5a - remote main ref matches commit D | `"77fbcbd0e691a9cf95879622daec7fd896f05c6c"` | `"77fbcbd0e691a9cf95879622daec7fd896f05c6c"` | yes |
| run2: Fact 5b - remote main tree does not contain todo.txt | `["notes.txt"]` | `["notes.txt"]` | yes |
| run2: Fact 6 - topic branch still points to commit B | `"240107be52a6dfd7429929273d804391c4b8ca61"` | `"240107be52a6dfd7429929273d804391c4b8ca61"` | yes |
