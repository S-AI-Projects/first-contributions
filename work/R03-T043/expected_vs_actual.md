| check | expected | actual | ok |
|---|---|---|---|
| run1: start refs/heads/main points to commit C | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | yes |
| run1: start refs/heads/topic points to commit B | `"a70fd31a854c425ca0fa0cd152742f1c7e807bae"` | `"a70fd31a854c425ca0fa0cd152742f1c7e807bae"` | yes |
| run1: start refs/remotes/origin/main points to commit C | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | yes |
| run1: start refs/remotes/origin/topic points to commit B | `"a70fd31a854c425ca0fa0cd152742f1c7e807bae"` | `"a70fd31a854c425ca0fa0cd152742f1c7e807bae"` | yes |
| run1: checked out branch is topic | `"refs/heads/topic"` | `"refs/heads/topic"` | yes |
| run1: Fact 1a - topic tip is distinct from original B | `false` | `false` | yes |
| run1: Fact 1b - topic tip is distinct from C | `false` | `false` | yes |
| run1: Fact 1c - topic tip is distinct from A | `false` | `false` | yes |
| run1: Fact 2 - refs/heads/main unchanged at commit C | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | yes |
| run1: Fact 3 - origin/main unchanged at commit C | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | yes |
| run1: Fact 4 - origin/topic still at old commit B before push | `"a70fd31a854c425ca0fa0cd152742f1c7e807bae"` | `"a70fd31a854c425ca0fa0cd152742f1c7e807bae"` | yes |
| run1: Fact 5 - normal git push origin topic fails | `true` | `true` | yes |
| run1: Fact 6a - origin/topic updated to amended commit B' | `"85801e43a8fcb21f2758081ec1ba78d214f5fee5"` | `"85801e43a8fcb21f2758081ec1ba78d214f5fee5"` | yes |
| run1: Fact 6b - local tracking ref origin/topic matches B' | `"85801e43a8fcb21f2758081ec1ba78d214f5fee5"` | `"85801e43a8fcb21f2758081ec1ba78d214f5fee5"` | yes |
| run1: Fact 7a - main still at commit C | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | yes |
| run1: Fact 7b - origin/main still at commit C | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | yes |
| run1: Fact 8a - notes.txt content | `"alpha\nbeta\ngamma\n"` | `"alpha\nbeta\ngamma\n"` | yes |
| run1: Fact 8b - todo.txt does not exist on topic | `false` | `false` | yes |
| run1: Fact 8c - working tree is clean | `""` | `""` | yes |
| run2: start refs/heads/main points to commit C | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | yes |
| run2: start refs/heads/topic points to commit B | `"a70fd31a854c425ca0fa0cd152742f1c7e807bae"` | `"a70fd31a854c425ca0fa0cd152742f1c7e807bae"` | yes |
| run2: start refs/remotes/origin/main points to commit C | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | yes |
| run2: start refs/remotes/origin/topic points to commit B | `"a70fd31a854c425ca0fa0cd152742f1c7e807bae"` | `"a70fd31a854c425ca0fa0cd152742f1c7e807bae"` | yes |
| run2: checked out branch is topic | `"refs/heads/topic"` | `"refs/heads/topic"` | yes |
| run2: Fact 1a - topic tip is distinct from original B | `false` | `false` | yes |
| run2: Fact 1b - topic tip is distinct from C | `false` | `false` | yes |
| run2: Fact 1c - topic tip is distinct from A | `false` | `false` | yes |
| run2: Fact 2 - refs/heads/main unchanged at commit C | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | yes |
| run2: Fact 3 - origin/main unchanged at commit C | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | yes |
| run2: Fact 4 - origin/topic still at old commit B before push | `"a70fd31a854c425ca0fa0cd152742f1c7e807bae"` | `"a70fd31a854c425ca0fa0cd152742f1c7e807bae"` | yes |
| run2: Fact 5 - normal git push origin topic fails | `true` | `true` | yes |
| run2: Fact 6a - origin/topic updated to amended commit B' | `"85801e43a8fcb21f2758081ec1ba78d214f5fee5"` | `"85801e43a8fcb21f2758081ec1ba78d214f5fee5"` | yes |
| run2: Fact 6b - local tracking ref origin/topic matches B' | `"85801e43a8fcb21f2758081ec1ba78d214f5fee5"` | `"85801e43a8fcb21f2758081ec1ba78d214f5fee5"` | yes |
| run2: Fact 7a - main still at commit C | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | yes |
| run2: Fact 7b - origin/main still at commit C | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | `"528a8d4b2326ee42ee4fc0936d97533953d80eea"` | yes |
| run2: Fact 8a - notes.txt content | `"alpha\nbeta\ngamma\n"` | `"alpha\nbeta\ngamma\n"` | yes |
| run2: Fact 8b - todo.txt does not exist on topic | `false` | `false` | yes |
| run2: Fact 8c - working tree is clean | `""` | `""` | yes |
