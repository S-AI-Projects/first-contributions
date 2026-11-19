| check | expected | actual | ok |
|---|---|---|---|
| destructive commands run only inside the temp repo | `true` | `true` | yes |
| start: main is checked out | `"refs/heads/main"` | `"refs/heads/main"` | yes |
| start: main at C, topic at B | `{"refs/heads/main": "6022b9fbe073c50a629eab4c69501a17c002d190", "refs/heads/topic": "b24f3082e96c5ac778ad9f5db932929ea4772272"}` | `{"refs/heads/main": "6022b9fbe073c50a629eab4c69501a17c002d190", "refs/heads/topic": "b24f3082e96c5ac778ad9f5db932929ea4772272"}` | yes |
| start: author is Course Student | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | yes |
| guide: `git log -n 2` lists C then B | `["6022b9fbe073c50a629eab4c69501a17c002d190", "b24f3082e96c5ac778ad9f5db932929ea4772272"]` | `["6022b9fbe073c50a629eab4c69501a17c002d190", "b24f3082e96c5ac778ad9f5db932929ea4772272"]` | yes |
| guide: `git log --all -- todo.txt` lists C | `["6022b9fbe073c50a629eab4c69501a17c002d190"]` | `["6022b9fbe073c50a629eab4c69501a17c002d190"]` | yes |
| uncommitted edit is present | `" M notes.txt\n"` | `" M notes.txt\n"` | yes |
| mistake: main now points at B | `"b24f3082e96c5ac778ad9f5db932929ea4772272"` | `"b24f3082e96c5ac778ad9f5db932929ea4772272"` | yes |
| mistake: topic did not move | `"b24f3082e96c5ac778ad9f5db932929ea4772272"` | `"b24f3082e96c5ac778ad9f5db932929ea4772272"` | yes |
| mistake: HEAD is still on main | `"refs/heads/main"` | `"refs/heads/main"` | yes |
| mistake: git log lists only B, A | `["b24f3082e96c5ac778ad9f5db932929ea4772272", "5a80489fdd5bc6181aa618bc3f72d546d8683044"]` | `["b24f3082e96c5ac778ad9f5db932929ea4772272", "5a80489fdd5bc6181aa618bc3f72d546d8683044"]` | yes |
| mistake: even `git log --all` no longer lists C | `["b24f3082e96c5ac778ad9f5db932929ea4772272", "5a80489fdd5bc6181aa618bc3f72d546d8683044"]` | `["b24f3082e96c5ac778ad9f5db932929ea4772272", "5a80489fdd5bc6181aa618bc3f72d546d8683044"]` | yes |
| mistake: todo.txt is gone from the working tree | `false` | `false` | yes |
| mistake: the commit object still exists | `0` | `0` | yes |
| recovery point: the reflog has exactly one entry for C, with C's id | `["6022b9fbe073c50a629eab4c69501a17c002d190"]` | `["6022b9fbe073c50a629eab4c69501a17c002d190"]` | yes |
| recovery point: main@{1} is also C | `"6022b9fbe073c50a629eab4c69501a17c002d190"` | `"6022b9fbe073c50a629eab4c69501a17c002d190"` | yes |
| recovered: main points at C again | `"6022b9fbe073c50a629eab4c69501a17c002d190"` | `"6022b9fbe073c50a629eab4c69501a17c002d190"` | yes |
| recovered: tree hash equals the saved tree hash of C | `"70d571a7a75867c09d38254b1252d5e2402adaa6"` | `"70d571a7a75867c09d38254b1252d5e2402adaa6"` | yes |
| recovered: git log lists C, B, A | `["6022b9fbe073c50a629eab4c69501a17c002d190", "b24f3082e96c5ac778ad9f5db932929ea4772272", "5a80489fdd5bc6181aa618bc3f72d546d8683044"]` | `["6022b9fbe073c50a629eab4c69501a17c002d190", "b24f3082e96c5ac778ad9f5db932929ea4772272", "5a80489fdd5bc6181aa618bc3f72d546d8683044"]` | yes |
| recovered: notes.txt content | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | yes |
| recovered: todo.txt content | `"one\n"` | `"one\n"` | yes |
| recovered: working tree clean | `""` | `""` | yes |
| recovered: all refs are back where they started | `{"refs/heads/main": "6022b9fbe073c50a629eab4c69501a17c002d190", "refs/heads/topic": "b24f3082e96c5ac778ad9f5db932929ea4772272"}` | `{"refs/heads/main": "6022b9fbe073c50a629eab4c69501a17c002d190", "refs/heads/topic": "b24f3082e96c5ac778ad9f5db932929ea4772272"}` | yes |
| NOT recoverable: the uncommitted 'gamma' edit stays lost | `false` | `false` | yes |
