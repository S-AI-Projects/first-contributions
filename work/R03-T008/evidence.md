# R03-T008 verification evidence

- Command: `python3 work/R03-T008/check.py`
- Input: Temporary local Git repository using branch main and author Course Student <student@example.invalid>; commit A creates notes.txt with alpha, B appends beta, C adds todo.txt with one, and create topic at B. The task check adds only the divergence or file state needed for its scenario.
- Expected: The published amend shell sequence creates a new commit, retains its parent, includes corrected content, and leaves a clean worktree.
- Actual: `PASS: amended fcc6ce3 -> 816f605, parent preserved, staged content included, clean`
- Git: `git version 2.55.0`
- Python: `Python 3.15.2`
