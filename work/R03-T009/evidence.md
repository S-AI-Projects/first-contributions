# R03-T009 verification evidence

- Command: `python3 work/R03-T009/check.py`
- Input: Temporary local Git repository using branch main and author Course Student <student@example.invalid>; commit A creates notes.txt with alpha, B appends beta, C adds todo.txt with one, and create topic at B. The task check adds only the divergence or file state needed for its scenario.
- Expected: The check confirms clean main, one upstream remote, repository-local identity, and unchanged global Git configuration.
- Actual: `PASS: clean main, local identity configured, upstream added once, global config untouched`
- Git: `git version 2.55.0`
- Python: `Python 3.15.2`
