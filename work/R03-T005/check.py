import subprocess,tempfile
from pathlib import Path
def g(r,*a): return subprocess.run(['git',*a],cwd=r,text=True,capture_output=True,check=True).stdout.strip()
with tempfile.TemporaryDirectory() as d:
 r=Path(d); g(r,'init','-b','main'); g(r,'config','user.name','Course Student'); g(r,'config','user.email','student@example.invalid')
 (r/'notes.txt').write_text('alpha\n'); g(r,'add','notes.txt'); g(r,'commit','-m','A'); (r/'notes.txt').write_text('alpha\nbeta\n'); g(r,'add','notes.txt'); g(r,'commit','-m','B'); g(r,'branch','topic'); (r/'todo.txt').write_text('one\n'); g(r,'add','todo.txt'); g(r,'commit','-m','C')
 (r/'release notes.txt').write_text('release notes\n'); (r/'sample data').mkdir(); (r/'sample data'/'input.txt').write_text('sample\n')
 g(r,'add','--','release notes.txt','sample data'); staged=g(r,'diff','--cached','--name-only').splitlines(); assert staged==['release notes.txt','sample data/input.txt']
 g(r,'commit','-m','add paths with spaces'); assert g(r,'log','-1','--format=%s')=='add paths with spaces'
 assert (r/'release notes.txt').read_text()=='release notes\n' and (r/'sample data'/'input.txt').read_text()=='sample\n'
 assert g(r,'config','--local','user.name')=='Course Student' and g(r,'config','--local','user.email')=='student@example.invalid'
 assert g(r,'status','--porcelain')==''
 print(f'PASS: staged exact spaced paths={staged}; local author config; clean')
