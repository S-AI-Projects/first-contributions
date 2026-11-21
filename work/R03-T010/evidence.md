# R03-T010 verification evidence

- Command: `python3 work/R03-T010/check.py`
- Input: Temporary local Git repository using branch main and author Course Student <student@example.invalid>; commit A creates notes.txt with alpha, B appends beta, C adds todo.txt with one, and create topic at B. The task check adds only the divergence or file state needed for its scenario.
- Expected: main, develop, and origin/develop point to C; topic remains at B; tracking is configured; index and worktree remain clean.
- Actual: `PASS: main=7558e90, develop=7558e90, origin/develop=7558e90; topic remains 68caf47, clean tree`
- Git: `git version 2.55.0`
- Python: `Python 3.15.2`
