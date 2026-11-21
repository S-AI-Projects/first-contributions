import subprocess,tempfile
from pathlib import Path
def g(r,*a): return subprocess.run(['git',*a],cwd=r,text=True,capture_output=True,check=True).stdout.strip()
def global_config():
 p=subprocess.run(['git','config','--global','--list'],text=True,capture_output=True); return (p.returncode,p.stdout)
global_before=global_config()
with tempfile.TemporaryDirectory() as d:
 root=Path(d); r=root/'repo'; r.mkdir(); g(r,'init','-b','main'); g(r,'config','user.name','Course Student'); g(r,'config','user.email','student@example.invalid'); (r/'notes.txt').write_text('alpha\n'); g(r,'add','notes.txt'); g(r,'commit','-m','A'); (r/'notes.txt').write_text('alpha\nbeta\n'); g(r,'add','notes.txt'); g(r,'commit','-m','B'); g(r,'branch','topic'); (r/'todo.txt').write_text('one\n'); g(r,'add','todo.txt'); g(r,'commit','-m','C')
 # Add a local bare upstream only after checking absence.
 assert g(r,'remote').strip()==''; bare=root/'upstream.git'; g(root,'init','--bare',str(bare)); g(r,'remote','add','upstream',bare.as_uri())
 assert g(r,'branch','--show-current')=='main'
 assert g(r,'config','--local','user.name')=='Course Student' and g(r,'config','--local','user.email')=='student@example.invalid'
 assert g(r,'status','--porcelain')=='' and 'upstream' in g(r,'remote')
 assert global_config()==global_before
 print('PASS: clean main, local identity configured, upstream added once, global config untouched')
