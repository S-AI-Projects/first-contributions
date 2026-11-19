| check | expected | actual | ok |
|---|---|---|---|
| commands run only inside the temp repo | `true` | `true` | yes |
| start: topic is checked out | `"refs/heads/topic"` | `"refs/heads/topic"` | yes |
| start: main at C, topic at B | `{"refs/heads/main": "98b2de3674304273bf6eb551f64bcc99ac8e6da0", "refs/heads/topic": "240ced8c1f937d8885fc57a43bb283058c4634a7"}` | `{"refs/heads/main": "98b2de3674304273bf6eb551f64bcc99ac8e6da0", "refs/heads/topic": "240ced8c1f937d8885fc57a43bb283058c4634a7"}` | yes |
| start: author is Course Student | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | `["Course Student <student@example.invalid>", "Course Student <student@example.invalid>", "Course Student <student@example.invalid>"]` | yes |
| unquoted file name: git add fails | `true` | `true` | yes |
| unquoted file name: git looks for a file called 'release' | `true` | `true` | yes |
| unquoted directory name: git looks for 'sample' | `true` | `true` | yes |
| failed adds staged nothing | `[]` | `[]` | yes |
| quoted paths: exactly the intended files are staged | `["release notes.txt", "sample data/readings.csv"]` | `["release notes.txt", "sample data/readings.csv"]` | yes |
| git status --short shows the names in quotes (display only) | `["A  \"release notes.txt\"", "A  \"sample data/readings.csv\""]` | `["A  \"release notes.txt\"", "A  \"sample data/readings.csv\""]` | yes |
| D sits on top of B | `"240ced8c1f937d8885fc57a43bb283058c4634a7"` | `"240ced8c1f937d8885fc57a43bb283058c4634a7"` | yes |
| only the intended file is staged | `["release notes.txt"]` | `["release notes.txt"]` | yes |
| git status --short: staged file quoted, unrelated edit unstaged | `[" M notes.txt", "M  \"release notes.txt\""]` | `[" M notes.txt", "M  \"release notes.txt\""]` | yes |
| amend: the only ref that changed is refs/heads/topic | `["refs/heads/topic"]` | `["refs/heads/topic"]` | yes |
| amend: main still points at C | `"98b2de3674304273bf6eb551f64bcc99ac8e6da0"` | `"98b2de3674304273bf6eb551f64bcc99ac8e6da0"` | yes |
| amend: topic points at a new commit | `true` | `true` | yes |
| amend: the new commit has the same parent (B) | `"240ced8c1f937d8885fc57a43bb283058c4634a7"` | `"240ced8c1f937d8885fc57a43bb283058c4634a7"` | yes |
| amend: the message was kept | `"D: add release notes and sample data"` | `"D: add release notes and sample data"` | yes |
| amend: release notes.txt in the new commit has both lines | `"v1\nv2 line\n"` | `"v1\nv2 line\n"` | yes |
| amend: the commit contains the two intended paths | `["release notes.txt", "sample data/readings.csv"]` | `["release notes.txt", "sample data/readings.csv"]` | yes |
| amend: unrelated notes.txt was not swept into the commit | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | yes |
| amend: the unrelated edit is still there, unstaged | `["notes.txt"]` | `["notes.txt"]` | yes |
| amend: the old commit D is still reachable as topic@{1} | `"ee362a417ca796f08051f246ae61197483dd8bce"` | `"ee362a417ca796f08051f246ae61197483dd8bce"` | yes |
| git log -- "release notes.txt" lists the commit that holds it | `["D: add release notes and sample data"]` | `["D: add release notes and sample data"]` | yes |
| quoted path also works without --, when it is not ambiguous | `["D: add release notes and sample data"]` | `["D: add release notes and sample data"]` | yes |
| file named like a branch: git log refuses to guess | `true` | `true` | yes |
| ambiguity error text | `true` | `true` | yes |
| `git log topic --` means the branch | `["D: add release notes and sample data", "B: append beta", "A: create notes.txt"]` | `["D: add release notes and sample data", "B: append beta", "A: create notes.txt"]` | yes |
| `git log -- topic` means the file (no history) | `[]` | `[]` | yes |
