import re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; guide=(ROOT/'docs/additional-material/git_workflow_scenarios/amending-a-commit.md').read_text()
blocks=re.findall(r'```sh\n(.*?)\n```',guide,re.S); seq=next((b for b in blocks if 'git commit --amend --no-edit' in b),None)
assert seq and 'git commit --amend --no-edit' in seq,'decisive amend command missing from published sequence'
def run(r,*a): return subprocess.run(a,cwd=r,text=True,capture_output=True,check=True).stdout.strip()
with tempfile.TemporaryDirectory() as d:
 r=Path(d); run(r,'git','init','-b','main'); run(r,'git','config','user.name','Course Student'); run(r,'git','config','user.email','student@example.invalid'); (r/'notes.txt').write_text('alpha\n'); run(r,'git','add','notes.txt'); run(r,'git','commit','-m','A'); (r/'notes.txt').write_text('alpha\nbeta\n'); run(r,'git','add','notes.txt'); run(r,'git','commit','-m','B'); (r/'todo.txt').write_text('one\n'); run(r,'git','add','todo.txt'); run(r,'git','commit','-m','C'); parent=run(r,'git','rev-parse','HEAD^')
 # Execute the actual published shell block in this temp repo.
 before=run(r,'git','rev-parse','HEAD'); result=subprocess.run(['bash','-eu','-c',seq],cwd=r,text=True,capture_output=True); assert result.returncode==0,result.stderr; after=run(r,'git','rev-parse','HEAD')
 assert before!=after and run(r,'git','rev-parse','HEAD^')==parent
 assert 'corrected line' in run(r,'git','show','HEAD:notes.txt') and run(r,'git','status','--porcelain')==''
 print(f'PASS: amended {before[:7]} -> {after[:7]}, parent preserved, staged content included, clean')
