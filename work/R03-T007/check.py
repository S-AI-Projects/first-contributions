import subprocess,tempfile
from pathlib import Path
def g(r,*a,check=True): return subprocess.run(['git',*a],cwd=r,text=True,capture_output=True,check=check)
with tempfile.TemporaryDirectory() as d:
 r=Path(d); g(r,'init','-b','main'); g(r,'config','user.name','Course Student'); g(r,'config','user.email','student@example.invalid'); (r/'notes.txt').write_text('alpha\n'); g(r,'add','notes.txt'); g(r,'commit','-m','A'); (r/'notes.txt').write_text('alpha\nbeta\n'); g(r,'add','notes.txt'); g(r,'commit','-m','B'); g(r,'branch','topic'); (r/'todo.txt').write_text('one\n'); g(r,'add','todo.txt'); g(r,'commit','-m','C')
 # Diverge the destination version, then create an uncommitted edit on main.
 g(r,'switch','topic'); (r/'notes.txt').write_text('topic version\n'); g(r,'add','notes.txt'); g(r,'commit','-m','topic version'); g(r,'switch','main'); (r/'todo.txt').write_text('local todo edit\n')
 failed=g(r,'checkout','topic',check=False); assert failed.returncode != 0 and 'main'==g(r,'branch','--show-current').stdout.strip() and (r/'todo.txt').read_text()=='local todo edit\n'
 g(r,'stash','push','-m','work before switching'); g(r,'checkout','topic'); g(r,'checkout','main'); pop=g(r,'stash','pop',check=False); assert pop.returncode==0
 assert g(r,'branch','--show-current').stdout.strip()=='main' and (r/'todo.txt').read_text()=='local todo edit\n'
 print(repr(g(r,'status','--porcelain').stdout)); assert 'todo.txt' in g(r,'status','--porcelain').stdout
 print('PASS: checkout rejected overwrite; stash allowed switch and restored local edit on main')
