# R03-T006 verification evidence

- Command: `python3 work/R03-T006/check.py`
- Input: Temporary local Git repository using branch main and author Course Student <student@example.invalid>; commit A creates notes.txt with alpha, B appends beta, C adds todo.txt with one, and create topic at B. The task check adds only the divergence or file state needed for its scenario.
- Expected: fetch+rebase and pull --rebase produce equivalent histories based on upstream while retaining local commits and clean trees.
- Actual: `PASS: fetch+rebase and pull --rebase reach upstream tip; local commits retained; clean trees`
- Git: `git version 2.55.0`
- Python: `Python 3.15.2`
