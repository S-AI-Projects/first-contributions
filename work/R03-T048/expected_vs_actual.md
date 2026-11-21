| check | expected | actual | ok |
|---|---|---|---|
| the guide test file is present | `true` | `true` | yes |
| as it is: guide test exits 0 | `0` | `0` | yes |
| all four tests are ok | `true` | `true` | yes |
| reset omitted: guide test fails (exit 1) | `1` | `1` | yes |
| sequence test FAILs when reset omitted | `"FAIL"` | `"FAIL"` | yes |
| no temporary directory is left behind | `[]` | `[]` | yes |
