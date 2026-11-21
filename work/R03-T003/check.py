import subprocess,tempfile
from pathlib import Path
def g(r,*a,check=True): return subprocess.run(['git',*a],cwd=r,text=True,capture_output=True,check=check).stdout.strip()
with tempfile.TemporaryDirectory() as d:
 r=Path(d); g(r,'init','-b','main'); g(r,'config','user.name','Course Student'); g(r,'config','user.email','student@example.invalid')
 (r/'notes.txt').write_text('alpha\n'); g(r,'add','notes.txt'); g(r,'commit','-m','A'); (r/'notes.txt').write_text('alpha\nbeta\n'); g(r,'add','notes.txt'); g(r,'commit','-m','B'); b=g(r,'rev-parse','HEAD'); g(r,'branch','topic',b)
 (r/'todo.txt').write_text('one\n'); g(r,'add','todo.txt'); g(r,'commit','-m','C'); (r/'main.txt').write_text('main update\n'); g(r,'add','main.txt'); g(r,'commit','-m','main update')
 g(r,'switch','topic'); (r/'topic.txt').write_text('topic work\n'); g(r,'add','topic.txt'); g(r,'commit','-m','D'); old=g(r,'rev-parse','HEAD'); tree=g(r,'rev-parse','HEAD^{tree}')
 g(r,'rebase','main'); rebased=g(r,'rev-parse','HEAD'); assert rebased!=old and (r/'main.txt').exists() and (r/'topic.txt').exists()
 g(r,'reset','--hard','ORIG_HEAD'); assert g(r,'rev-parse','HEAD')==old and g(r,'rev-parse','HEAD^{tree}')==tree
 assert g(r,'rev-parse','topic')==old and (r/'notes.txt').read_text()=='alpha\nbeta\n' and not (r/'main.txt').exists()
 assert g(r,'status','--porcelain')=='' and g(r,'rev-parse','main')!=old
 print(f'PASS: rebase made {rebased[:7]}, ORIG_HEAD restored original topic D={old[:7]} tree={tree[:7]}, clean')
