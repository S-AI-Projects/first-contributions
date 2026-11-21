# R03-T002 verification evidence

- Command: `python3 work/R03-T002/check.py`
- Input: Temporary local Git repository using branch main and author Course Student <student@example.invalid>; commit A creates notes.txt with alpha, B appends beta, C adds todo.txt with one, and create topic at B. The task check adds only the divergence or file state needed for its scenario.
- Expected: After squash, main has one replacement commit with the same final tree; topic remains at B; index and worktree are clean.
- Actual: `PASS: main=44f6cd4, topic=d960f80, former C=f93494a, same tree=70d571a, staged files=['notes.txt', 'todo.txt'], clean`
- Git: `git version 2.55.0`
- Python: `Python 3.15.2`
