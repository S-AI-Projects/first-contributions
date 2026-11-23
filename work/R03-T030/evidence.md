# Verification Evidence for R03-T030

## Overview
- **Task**: R03-T030 (10 of 10)
- **Target Guide**: `docs/additional-material/git_workflow_scenarios/installing-git-arch.md`
- **Command Anchors**:
  - `git version 2.34.1`
  - `git config --global user.name "Your Name"`
  - `git config --global user.email "youremail@domain.com"`
- **Author Identity**: `Course Student <student@example.invalid>`

## State Transition Verification
| Layer | Predicted State | Actual State (Run 1) | Actual State (Run 2) | Verified? |
| :--- | :--- | :--- | :--- | :--- |
| **Active Ref (`HEAD`)** | `refs/heads/topic` | `refs/heads/topic` | `refs/heads/topic` | Pass |
| **`HEAD` Target SHA** | Commit B | `ae3a2a8d43c4f1817ab79629763862469af6010b` | `ae3a2a8d43c4f1817ab79629763862469af6010b` | Pass |
| **Branch `main`** | Fixed at Commit C | `37ef2a1e2050792e8c7c85978c331ac97ad481d8` | `37ef2a1e2050792e8c7c85978c331ac97ad481d8` | Pass |
| **Branch `topic`** | Fixed at Commit B | `ae3a2a8d43c4f1817ab79629763862469af6010b` | `ae3a2a8d43c4f1817ab79629763862469af6010b` | Pass |
| **Index (`notes.txt`)** | Tracked | Present | Present | Pass |
| **Index (`todo.txt`)** | Removed | Absent | Absent | Pass |
| **Worktree `todo.txt`** | Removed from disk | Absent (`exists=False`) | Absent (`exists=False`) | Pass |
| **Worktree `notes.txt`**| `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | `"alpha\nbeta\n"` | Pass |
| **Author Metadata** | Configured author | `Course Student <student@example.invalid>` | `Course Student <student@example.invalid>` | Pass |

## Negative Test Verification
Execution with `FORCE_FAIL=1` raised an AssertionError, confirming that non-zero exit code triggers on verification failure.
