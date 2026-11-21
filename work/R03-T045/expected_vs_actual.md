| check | expected | actual | ok |
|---|---|---|---|
| run1: switched to branch topic | `"refs/heads/topic"` | `"refs/heads/topic"` | yes |
| run1: Fact 1 - unquoted add fails | `true` | `true` | yes |
| run1: Fact 1b - error mentions pathspec 'release' | `true` | `true` | yes |
| run1: Fact 2 - staged files include 'release notes.txt' | `true` | `true` | yes |
| run1: Fact 2b - staged files include 'sample data/data.txt' | `true` | `true` | yes |
| run1: Fact 3a - rebase creates new commit | `false` | `false` | yes |
| run1: Fact 3b - history length on topic is 4 | `4` | `4` | yes |
| run1: Fact 3c - commit C is direct parent of topic tip | `"1a29c354757fd6c6554be073653a7c9150de9bf3"` | `"1a29c354757fd6c6554be073653a7c9150de9bf3"` | yes |
| run1: Fact 4a - todo.txt from main exists | `true` | `true` | yes |
| run1: Fact 4b - release notes.txt exists | `true` | `true` | yes |
| run1: Fact 4c - sample data/data.txt exists | `true` | `true` | yes |
| run1: file modified | `"notes for release\naccidental line\n"` | `"notes for release\naccidental line\n"` | yes |
| run1: Fact 5 - checkout -- restores clean file content | `"notes for release\n"` | `"notes for release\n"` | yes |
| run1: Fact 6 - branch main still points to commit C | `"1a29c354757fd6c6554be073653a7c9150de9bf3"` | `"1a29c354757fd6c6554be073653a7c9150de9bf3"` | yes |
| run1: Fact 7 - working tree is clean | `""` | `""` | yes |
| run2: switched to branch topic | `"refs/heads/topic"` | `"refs/heads/topic"` | yes |
| run2: Fact 1 - unquoted add fails | `true` | `true` | yes |
| run2: Fact 1b - error mentions pathspec 'release' | `true` | `true` | yes |
| run2: Fact 2 - staged files include 'release notes.txt' | `true` | `true` | yes |
| run2: Fact 2b - staged files include 'sample data/data.txt' | `true` | `true` | yes |
| run2: Fact 3a - rebase creates new commit | `false` | `false` | yes |
| run2: Fact 3b - history length on topic is 4 | `4` | `4` | yes |
| run2: Fact 3c - commit C is direct parent of topic tip | `"1a29c354757fd6c6554be073653a7c9150de9bf3"` | `"1a29c354757fd6c6554be073653a7c9150de9bf3"` | yes |
| run2: Fact 4a - todo.txt from main exists | `true` | `true` | yes |
| run2: Fact 4b - release notes.txt exists | `true` | `true` | yes |
| run2: Fact 4c - sample data/data.txt exists | `true` | `true` | yes |
| run2: file modified | `"notes for release\naccidental line\n"` | `"notes for release\naccidental line\n"` | yes |
| run2: Fact 5 - checkout -- restores clean file content | `"notes for release\n"` | `"notes for release\n"` | yes |
| run2: Fact 6 - branch main still points to commit C | `"1a29c354757fd6c6554be073653a7c9150de9bf3"` | `"1a29c354757fd6c6554be073653a7c9150de9bf3"` | yes |
| run2: Fact 7 - working tree is clean | `""` | `""` | yes |
