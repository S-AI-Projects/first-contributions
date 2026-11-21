# R03-T007 verification evidence

- Command: `python3 work/R03-T007/check.py`
- Input: Temporary local Git repository using branch main and author Course Student <student@example.invalid>; commit A creates notes.txt with alpha, B appends beta, C adds todo.txt with one, and create topic at B. The task check adds only the divergence or file state needed for its scenario.
- Expected: Checkout refuses to overwrite the uncommitted edit; stashing permits the switch and restores the edit on its intended branch.
- Actual: `' M todo.txt\n'
PASS: checkout rejected overwrite; stash allowed switch and restored local edit on main`
- Git: `git version 2.55.0`
- Python: `Python 3.15.2`
