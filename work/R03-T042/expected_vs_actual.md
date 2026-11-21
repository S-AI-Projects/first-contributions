| check | expected | actual | ok |
|---|---|---|---|
| run1: start history is [C, B, A] | `["3f222f16f6356d11b70163af99e1fa0a3c81791a", "952c3bc35f52898eccd106fe88787ac0625faa40", "464c3332ccdc818073e0fe1fa05700ff9998aad8"]` | `["3f222f16f6356d11b70163af99e1fa0a3c81791a", "952c3bc35f52898eccd106fe88787ac0625faa40", "464c3332ccdc818073e0fe1fa05700ff9998aad8"]` | yes |
| run1: branch topic points to commit B | `"952c3bc35f52898eccd106fe88787ac0625faa40"` | `"952c3bc35f52898eccd106fe88787ac0625faa40"` | yes |
| run1: notes.txt initial content | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | yes |
| run1: todo.txt initial content | `"one\n"` | `"one\n"` | yes |
| run1: squashed commit is distinct from C | `false` | `false` | yes |
| run1: history now contains 2 commits [BC, A] | `2` | `2` | yes |
| run1: commit C is no longer in rev-list | `false` | `false` | yes |
| run1: ORIG_HEAD points to pre-rebase commit C | `"3f222f16f6356d11b70163af99e1fa0a3c81791a"` | `"3f222f16f6356d11b70163af99e1fa0a3c81791a"` | yes |
| run1: Fact 1 - HEAD points to original commit C | `"3f222f16f6356d11b70163af99e1fa0a3c81791a"` | `"3f222f16f6356d11b70163af99e1fa0a3c81791a"` | yes |
| run1: Fact 2 - Main history is fully restored to [C, B, A] | `["3f222f16f6356d11b70163af99e1fa0a3c81791a", "952c3bc35f52898eccd106fe88787ac0625faa40", "464c3332ccdc818073e0fe1fa05700ff9998aad8"]` | `["3f222f16f6356d11b70163af99e1fa0a3c81791a", "952c3bc35f52898eccd106fe88787ac0625faa40", "464c3332ccdc818073e0fe1fa05700ff9998aad8"]` | yes |
| run1: Fact 3 - Recovered tree hash matches pre-squash tree hash | `"70d571a7a75867c09d38254b1252d5e2402adaa6"` | `"70d571a7a75867c09d38254b1252d5e2402adaa6"` | yes |
| run1: Fact 4a - notes.txt content matches | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | yes |
| run1: Fact 4b - todo.txt content matches | `"one\n"` | `"one\n"` | yes |
| run1: Fact 5 - Branch topic still points to commit B | `"952c3bc35f52898eccd106fe88787ac0625faa40"` | `"952c3bc35f52898eccd106fe88787ac0625faa40"` | yes |
| run1: Fact 6 - Working tree status is clean | `""` | `""` | yes |
| run2: start history is [C, B, A] | `["3f222f16f6356d11b70163af99e1fa0a3c81791a", "952c3bc35f52898eccd106fe88787ac0625faa40", "464c3332ccdc818073e0fe1fa05700ff9998aad8"]` | `["3f222f16f6356d11b70163af99e1fa0a3c81791a", "952c3bc35f52898eccd106fe88787ac0625faa40", "464c3332ccdc818073e0fe1fa05700ff9998aad8"]` | yes |
| run2: branch topic points to commit B | `"952c3bc35f52898eccd106fe88787ac0625faa40"` | `"952c3bc35f52898eccd106fe88787ac0625faa40"` | yes |
| run2: notes.txt initial content | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | yes |
| run2: todo.txt initial content | `"one\n"` | `"one\n"` | yes |
| run2: squashed commit is distinct from C | `false` | `false` | yes |
| run2: history now contains 2 commits [BC, A] | `2` | `2` | yes |
| run2: commit C is no longer in rev-list | `false` | `false` | yes |
| run2: reflog records pre-rebase commit C | `true` | `true` | yes |
| run2: Fact 1 - HEAD points to original commit C | `"3f222f16f6356d11b70163af99e1fa0a3c81791a"` | `"3f222f16f6356d11b70163af99e1fa0a3c81791a"` | yes |
| run2: Fact 2 - Main history is fully restored to [C, B, A] | `["3f222f16f6356d11b70163af99e1fa0a3c81791a", "952c3bc35f52898eccd106fe88787ac0625faa40", "464c3332ccdc818073e0fe1fa05700ff9998aad8"]` | `["3f222f16f6356d11b70163af99e1fa0a3c81791a", "952c3bc35f52898eccd106fe88787ac0625faa40", "464c3332ccdc818073e0fe1fa05700ff9998aad8"]` | yes |
| run2: Fact 3 - Recovered tree hash matches pre-squash tree hash | `"70d571a7a75867c09d38254b1252d5e2402adaa6"` | `"70d571a7a75867c09d38254b1252d5e2402adaa6"` | yes |
| run2: Fact 4a - notes.txt content matches | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | yes |
| run2: Fact 4b - todo.txt content matches | `"one\n"` | `"one\n"` | yes |
| run2: Fact 5 - Branch topic still points to commit B | `"952c3bc35f52898eccd106fe88787ac0625faa40"` | `"952c3bc35f52898eccd106fe88787ac0625faa40"` | yes |
| run2: Fact 6 - Working tree status is clean | `""` | `""` | yes |
