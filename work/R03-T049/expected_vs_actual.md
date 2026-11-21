| check | expected | actual | ok |
|---|---|---|---|
| run1: start HEAD is commit C | `"f41cac98b88cb1b63f1fae52df821723774014f4"` | `"f41cac98b88cb1b63f1fae52df821723774014f4"` | yes |
| run1: start branch topic is commit B | `"158ca3ec9fd59670940fe0717ff538c384693e51"` | `"158ca3ec9fd59670940fe0717ff538c384693e51"` | yes |
| run1: start todo.txt exists on disk | `true` | `true` | yes |
| run1: git revert exits 0 | `0` | `0` | yes |
| run1: Fact 1a - commit D is distinct from C | `false` | `false` | yes |
| run1: Fact 1b - main history is [D, C, B, A] | `["2cda84011ac7f1a568005b9b480b24dfaa369047", "f41cac98b88cb1b63f1fae52df821723774014f4", "158ca3ec9fd59670940fe0717ff538c384693e51", "0c13bf14cf2ae81e4012e789d4054a5495080e75"]` | `["2cda84011ac7f1a568005b9b480b24dfaa369047", "f41cac98b88cb1b63f1fae52df821723774014f4", "158ca3ec9fd59670940fe0717ff538c384693e51", "0c13bf14cf2ae81e4012e789d4054a5495080e75"]` | yes |
| run1: Fact 2 - parent of D is commit C | `"f41cac98b88cb1b63f1fae52df821723774014f4"` | `"f41cac98b88cb1b63f1fae52df821723774014f4"` | yes |
| run1: Fact 3 - commit D tree contains only notes.txt | `["notes.txt"]` | `["notes.txt"]` | yes |
| run1: Fact 4 - todo.txt deleted from disk | `false` | `false` | yes |
| run1: Fact 5 - notes.txt content matches | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | yes |
| run1: Fact 6 - working tree status is clean | `""` | `""` | yes |
| run1: Fact 7 - branch topic still points to commit B | `"158ca3ec9fd59670940fe0717ff538c384693e51"` | `"158ca3ec9fd59670940fe0717ff538c384693e51"` | yes |
| run2: start HEAD is commit C | `"f41cac98b88cb1b63f1fae52df821723774014f4"` | `"f41cac98b88cb1b63f1fae52df821723774014f4"` | yes |
| run2: start branch topic is commit B | `"158ca3ec9fd59670940fe0717ff538c384693e51"` | `"158ca3ec9fd59670940fe0717ff538c384693e51"` | yes |
| run2: start todo.txt exists on disk | `true` | `true` | yes |
| run2: git revert exits 0 | `0` | `0` | yes |
| run2: Fact 1a - commit D is distinct from C | `false` | `false` | yes |
| run2: Fact 1b - main history is [D, C, B, A] | `["2cda84011ac7f1a568005b9b480b24dfaa369047", "f41cac98b88cb1b63f1fae52df821723774014f4", "158ca3ec9fd59670940fe0717ff538c384693e51", "0c13bf14cf2ae81e4012e789d4054a5495080e75"]` | `["2cda84011ac7f1a568005b9b480b24dfaa369047", "f41cac98b88cb1b63f1fae52df821723774014f4", "158ca3ec9fd59670940fe0717ff538c384693e51", "0c13bf14cf2ae81e4012e789d4054a5495080e75"]` | yes |
| run2: Fact 2 - parent of D is commit C | `"f41cac98b88cb1b63f1fae52df821723774014f4"` | `"f41cac98b88cb1b63f1fae52df821723774014f4"` | yes |
| run2: Fact 3 - commit D tree contains only notes.txt | `["notes.txt"]` | `["notes.txt"]` | yes |
| run2: Fact 4 - todo.txt deleted from disk | `false` | `false` | yes |
| run2: Fact 5 - notes.txt content matches | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | yes |
| run2: Fact 6 - working tree status is clean | `""` | `""` | yes |
| run2: Fact 7 - branch topic still points to commit B | `"158ca3ec9fd59670940fe0717ff538c384693e51"` | `"158ca3ec9fd59670940fe0717ff538c384693e51"` | yes |
