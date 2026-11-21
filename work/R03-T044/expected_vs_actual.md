| check | expected | actual | ok |
|---|---|---|---|
| run1: Fact 1a - Workflow 1 author is global identity | `"Course Student <student@example.invalid>"` | `"Course Student <student@example.invalid>"` | yes |
| run1: Fact 1b - Workflow 1 committer is global identity | `"Course Student <student@example.invalid>"` | `"Course Student <student@example.invalid>"` | yes |
| run1: Fact 2 - repo1 local config has no user.name | `1` | `1` | yes |
| run1: Fact 3a - Workflow 2 author is local identity | `"Project Contributor <contributor@project.invalid>"` | `"Project Contributor <contributor@project.invalid>"` | yes |
| run1: Fact 3b - Workflow 2 committer is local identity | `"Project Contributor <contributor@project.invalid>"` | `"Project Contributor <contributor@project.invalid>"` | yes |
| run1: Fact 4a - global user.name is still Course Student | `"Course Student"` | `"Course Student"` | yes |
| run1: Fact 4b - global user.email is still student@example.invalid | `"student@example.invalid"` | `"student@example.invalid"` | yes |
| run1: Fact 5 - repo2 uses global identity | `"Course Student <student@example.invalid>"` | `"Course Student <student@example.invalid>"` | yes |
| run1: Fact 6 - topic in repo1 points to commit B | `"876bc04db55cd61354f7a992f5b18db71cb00eb0"` | `"876bc04db55cd61354f7a992f5b18db71cb00eb0"` | yes |
| run2: Fact 1a - Workflow 1 author is global identity | `"Course Student <student@example.invalid>"` | `"Course Student <student@example.invalid>"` | yes |
| run2: Fact 1b - Workflow 1 committer is global identity | `"Course Student <student@example.invalid>"` | `"Course Student <student@example.invalid>"` | yes |
| run2: Fact 2 - repo1 local config has no user.name | `1` | `1` | yes |
| run2: Fact 3a - Workflow 2 author is local identity | `"Project Contributor <contributor@project.invalid>"` | `"Project Contributor <contributor@project.invalid>"` | yes |
| run2: Fact 3b - Workflow 2 committer is local identity | `"Project Contributor <contributor@project.invalid>"` | `"Project Contributor <contributor@project.invalid>"` | yes |
| run2: Fact 4a - global user.name is still Course Student | `"Course Student"` | `"Course Student"` | yes |
| run2: Fact 4b - global user.email is still student@example.invalid | `"student@example.invalid"` | `"student@example.invalid"` | yes |
| run2: Fact 5 - repo2 uses global identity | `"Course Student <student@example.invalid>"` | `"Course Student <student@example.invalid>"` | yes |
| run2: Fact 6 - topic in repo1 points to commit B | `"a08c3013239cb68958768c3f79db780f0f20e2a6"` | `"a08c3013239cb68958768c3f79db780f0f20e2a6"` | yes |
