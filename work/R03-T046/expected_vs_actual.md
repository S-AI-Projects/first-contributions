| check | expected | actual | ok |
|---|---|---|---|
| run1: start HEAD is commit C | `"94526beb46b78b7048f843ee46d1e2ff66279835"` | `"94526beb46b78b7048f843ee46d1e2ff66279835"` | yes |
| run1: start branch topic is commit B | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | yes |
| run1: start working tree is clean | `""` | `""` | yes |
| run1: Fact 1a - bad reset exits non-zero | `true` | `true` | yes |
| run1: Fact 1b - error identifies ambiguous revision | `true` | `true` | yes |
| run1: Fact 2a - HEAD still at commit C after failure | `"94526beb46b78b7048f843ee46d1e2ff66279835"` | `"94526beb46b78b7048f843ee46d1e2ff66279835"` | yes |
| run1: Fact 2b - working tree remains clean | `""` | `""` | yes |
| run1: Fact 2c - topic still at commit B | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | yes |
| run1: Fact 3 - repaired reset exits 0 | `0` | `0` | yes |
| run1: Fact 4 - HEAD updated to commit B | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | yes |
| run1: Fact 5 - todo.txt is untracked | `["?? todo.txt"]` | `["?? todo.txt"]` | yes |
| run1: Fact 5b - todo.txt content preserved on disk | `"one\n"` | `"one\n"` | yes |
| run1: Fact 6 - topic still points to commit B | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | yes |
| run2: start HEAD is commit C | `"94526beb46b78b7048f843ee46d1e2ff66279835"` | `"94526beb46b78b7048f843ee46d1e2ff66279835"` | yes |
| run2: start branch topic is commit B | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | yes |
| run2: start working tree is clean | `""` | `""` | yes |
| run2: Fact 1a - bad reset exits non-zero | `true` | `true` | yes |
| run2: Fact 1b - error identifies ambiguous revision | `true` | `true` | yes |
| run2: Fact 2a - HEAD still at commit C after failure | `"94526beb46b78b7048f843ee46d1e2ff66279835"` | `"94526beb46b78b7048f843ee46d1e2ff66279835"` | yes |
| run2: Fact 2b - working tree remains clean | `""` | `""` | yes |
| run2: Fact 2c - topic still at commit B | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | yes |
| run2: Fact 3 - repaired reset exits 0 | `0` | `0` | yes |
| run2: Fact 4 - HEAD updated to commit B | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | yes |
| run2: Fact 5 - todo.txt is untracked | `["?? todo.txt"]` | `["?? todo.txt"]` | yes |
| run2: Fact 5b - todo.txt content preserved on disk | `"one\n"` | `"one\n"` | yes |
| run2: Fact 6 - topic still points to commit B | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | `"1bb6aea1d20a1f72464a7a2d1b74286a2bed0d42"` | yes |
