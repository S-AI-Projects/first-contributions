import subprocess,tempfile
from pathlib import Path
def g(r,*a,check=True): return subprocess.run(['git',*a],cwd=r,text=True,capture_output=True,check=check)
with tempfile.TemporaryDirectory() as d:
 r=Path(d); g(r,'init','-b','main'); g(r,'config','user.name','Course Student'); g(r,'config','user.email','student@example.invalid'); (r/'notes.txt').write_text('alpha\n'); g(r,'add','notes.txt'); g(r,'commit','-m','A'); (r/'notes.txt').write_text('alpha\nbeta\n'); g(r,'add','notes.txt'); g(r,'commit','-m','B'); b=g(r,'rev-parse','HEAD').stdout.strip(); g(r,'branch','topic',b); (r/'todo.txt').write_text('one\n'); g(r,'add','todo.txt'); g(r,'commit','-m','C'); c=g(r,'rev-parse','HEAD').stdout.strip()
 g(r,'switch','topic'); (r/'topic.txt').write_text('topic work\n'); g(r,'add','topic.txt'); g(r,'commit','-m','D on topic'); topic=g(r,'rev-parse','HEAD').stdout.strip()
 failed=g(r,'branch','--delete','topic',check=False); assert failed.returncode != 0 and g(r,'rev-parse','main').stdout.strip()==c
 g(r,'switch','main'); failed=g(r,'branch','--delete','topic',check=False); assert failed.returncode != 0 and 'topic' in g(r,'branch','--list').stdout
 g(r,'branch','--delete','--force','topic'); assert 'topic' not in g(r,'branch','--list').stdout
 assert g(r,'rev-parse','main').stdout.strip()==c and g(r,'status','--porcelain').stdout.strip()==''
 assert g(r,'remote').stdout.strip()==''
 print(f'PASS: local topic at D={topic[:7]} deleted; main remains C={c[:7]}; no remote ref changed')
