# R03-T004 verification evidence

- Command: `python3 work/R03-T004/check.py`
- Input: Temporary local Git repository using branch main and author Course Student <student@example.invalid>; commit A creates notes.txt with alpha, B appends beta, C adds todo.txt with one, and create topic at B. The task check adds only the divergence or file state needed for its scenario.
- Expected: The current-branch and unmerged safe-delete attempts fail; force deletion removes only local topic; main remains at C and no remote exists.
- Actual: `PASS: local topic at D=b7ecd32 deleted; main remains C=460cc55; no remote ref changed`
- Git: `git version 2.55.0`
- Python: `Python 3.15.2`
