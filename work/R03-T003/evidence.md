# R03-T003 verification evidence

- Command: `python3 work/R03-T003/check.py`
- Input: Temporary local Git repository using branch main and author Course Student <student@example.invalid>; commit A creates notes.txt with alpha, B appends beta, C adds todo.txt with one, and create topic at B. The task check adds only the divergence or file state needed for its scenario.
- Expected: The mistaken rebase creates a replacement topic commit; ORIG_HEAD restores the saved original commit and tree with a clean worktree.
- Actual: `PASS: rebase made a0cf7d1, ORIG_HEAD restored original topic D=fcc4660 tree=73a72b9, clean`
- Git: `git version 2.55.0`
- Python: `Python 3.15.2`
