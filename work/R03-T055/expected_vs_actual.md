| check | expected | actual | ok |
|---|---|---|---|
| commands run only inside the temp repo | `true` | `true` | yes |
| start: main at C, topic at B | `{"refs/heads/main": "db8525698ca25c069a0d1bf9f470ba74517e9523", "refs/heads/topic": "a3df8fbb59e2b733733d126f56bdea940e94535e"}` | `{"refs/heads/main": "db8525698ca25c069a0d1bf9f470ba74517e9523", "refs/heads/topic": "a3df8fbb59e2b733733d126f56bdea940e94535e"}` | yes |
| start: topic is checked out | `"refs/heads/topic"` | `"refs/heads/topic"` | yes |
| start: A, B, C were made by Course Student | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | yes |
| bad case: user.name is not set anywhere | `1` | `1` | yes |
| bad case: user.email is not set anywhere | `1` | `1` | yes |
| bad case: git cannot determine an author identity | `true` | `true` | yes |
| bad case: the change is staged | `["M  notes.txt"]` | `["M  notes.txt"]` | yes |
| bad case: git commit exits with git's fatal-error status | `128` | `128` | yes |
| bad case: the complaint is about the identity | `true` | `true` | yes |
| bad case: no commit was made and no ref moved | `{"refs/heads/main": "db8525698ca25c069a0d1bf9f470ba74517e9523", "refs/heads/topic": "a3df8fbb59e2b733733d126f56bdea940e94535e"}` | `{"refs/heads/main": "db8525698ca25c069a0d1bf9f470ba74517e9523", "refs/heads/topic": "a3df8fbb59e2b733733d126f56bdea940e94535e"}` | yes |
| bad case: the change is still staged | `["M  notes.txt"]` | `["M  notes.txt"]` | yes |
| repair A: git can now determine the author identity | `true` | `true` | yes |
| repair A: the commit's parent is B | `"a3df8fbb59e2b733733d126f56bdea940e94535e"` | `"a3df8fbb59e2b733733d126f56bdea940e94535e"` | yes |
| repair A: author is Course Student | `"Course Student <student@example.invalid>"` | `"Course Student <student@example.invalid>"` | yes |
| repair A: message is D: add gamma | `"D: add gamma"` | `"D: add gamma"` | yes |
| repair A: the staged change is in the commit | `"alpha\nbeta\ngamma\n"` | `"alpha\nbeta\ngamma\n"` | yes |
| repair A: topic moved to the new commit, main still at C | `{"refs/heads/main": "db8525698ca25c069a0d1bf9f470ba74517e9523", "refs/heads/topic": "694df2e5584bca6e1034ca3091f2c29c198f8ffa"}` | `{"refs/heads/main": "db8525698ca25c069a0d1bf9f470ba74517e9523", "refs/heads/topic": "694df2e5584bca6e1034ca3091f2c29c198f8ffa"}` | yes |
| repair A: the setting is stored in this repository | `"Course Student"` | `"Course Student"` | yes |
| repair A: nothing was written to the global config | `1` | `1` | yes |
| commands run only inside the temp repo | `true` | `true` | yes |
| -c case: user.name is not set anywhere | `1` | `1` | yes |
| -c case: user.email is not set anywhere | `1` | `1` | yes |
| -c case: git cannot determine an author identity | `true` | `true` | yes |
| -c case: the change is staged | `["M  notes.txt"]` | `["M  notes.txt"]` | yes |
| repair B (-c): the commit's parent is B | `"a3df8fbb59e2b733733d126f56bdea940e94535e"` | `"a3df8fbb59e2b733733d126f56bdea940e94535e"` | yes |
| repair B (-c): author is Course Student | `"Course Student <student@example.invalid>"` | `"Course Student <student@example.invalid>"` | yes |
| repair B (-c): message is D: add gamma | `"D: add gamma"` | `"D: add gamma"` | yes |
| repair B (-c): the staged change is in the commit | `"alpha\nbeta\ngamma\n"` | `"alpha\nbeta\ngamma\n"` | yes |
| repair B (-c): topic moved to the new commit, main still at C | `{"refs/heads/main": "db8525698ca25c069a0d1bf9f470ba74517e9523", "refs/heads/topic": "694df2e5584bca6e1034ca3091f2c29c198f8ffa"}` | `{"refs/heads/main": "db8525698ca25c069a0d1bf9f470ba74517e9523", "refs/heads/topic": "694df2e5584bca6e1034ca3091f2c29c198f8ffa"}` | yes |
| repair B (-c): nothing was saved to any config file | `1` | `1` | yes |
| repair B (-c): the next plain git commit fails again | `128` | `128` | yes |
| commands run only inside the temp repo | `true` | `true` | yes |
| --global case: user.name is not set anywhere | `1` | `1` | yes |
| --global case: user.email is not set anywhere | `1` | `1` | yes |
| --global case: git cannot determine an author identity | `true` | `true` | yes |
| --global case: the change is staged | `["M  notes.txt"]` | `["M  notes.txt"]` | yes |
| repair C (--global): the commit's parent is B | `"a3df8fbb59e2b733733d126f56bdea940e94535e"` | `"a3df8fbb59e2b733733d126f56bdea940e94535e"` | yes |
| repair C (--global): author is Course Student | `"Course Student <student@example.invalid>"` | `"Course Student <student@example.invalid>"` | yes |
| repair C (--global): message is D: add gamma | `"D: add gamma"` | `"D: add gamma"` | yes |
| repair C (--global): the staged change is in the commit | `"alpha\nbeta\ngamma\n"` | `"alpha\nbeta\ngamma\n"` | yes |
| repair C (--global): topic moved to the new commit, main still at C | `{"refs/heads/main": "db8525698ca25c069a0d1bf9f470ba74517e9523", "refs/heads/topic": "694df2e5584bca6e1034ca3091f2c29c198f8ffa"}` | `{"refs/heads/main": "db8525698ca25c069a0d1bf9f470ba74517e9523", "refs/heads/topic": "694df2e5584bca6e1034ca3091f2c29c198f8ffa"}` | yes |
| repair C (--global): written to the temporary HOME's .gitconfig, not a real one | `"/private/var/folders/nb/nkm7f7f54f5fb_swprmbm9jr0000gn/T/r03-t055-pfrvqr3k/s3/home/.gitconfig"` | `"/private/var/folders/nb/nkm7f7f54f5fb_swprmbm9jr0000gn/T/r03-t055-pfrvqr3k/s3/home/.gitconfig"` | yes |
| repair C (--global): the repository's own config has no user.name | `1` | `1` | yes |
