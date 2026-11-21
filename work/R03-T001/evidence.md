# R03-T001 verification evidence

- Command: `python3 work/R03-T001/check.py`
- Input: Temporary local Git repository using branch main and author Course Student <student@example.invalid>; commit A creates notes.txt with alpha, B appends beta, C adds todo.txt with one, and create topic at B. The task check adds only the divergence or file state needed for its scenario.
- Expected: Two independent runs end clean with main and topic at B, notes contain alpha and beta, and todo.txt is absent.
- Actual: `PASS: run 1: main=topic=B (b300630), clean index/worktree, notes preserved, todo absent; C=de2ca3c | run 2: main=topic=B (b300630), clean index/worktree, notes preserved, todo absent; C=de2ca3c`
- Git: `git version 2.55.0`
- Python: `Python 3.15.2`
