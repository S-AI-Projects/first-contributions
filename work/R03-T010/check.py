import subprocess,tempfile
from pathlib import Path
def g(cwd,*a): return subprocess.run(['git',*a],cwd=cwd,text=True,capture_output=True,check=True).stdout.strip()
with tempfile.TemporaryDirectory() as d:
 root=Path(d); bare=root/'origin.git'; g(root,'init','--bare',str(bare)); r=root/'repo'; g(root,'clone',str(bare),str(r)); g(r,'config','user.name','Course Student'); g(r,'config','user.email','student@example.invalid'); g(r,'switch','-c','main'); (r/'notes.txt').write_text('alpha\n'); g(r,'add','notes.txt'); g(r,'commit','-m','A'); (r/'notes.txt').write_text('alpha\nbeta\n'); g(r,'add','notes.txt'); g(r,'commit','-m','B'); b=g(r,'rev-parse','HEAD'); g(r,'branch','topic',b); (r/'todo.txt').write_text('one\n'); g(r,'add','todo.txt'); g(r,'commit','-m','C'); c=g(r,'rev-parse','HEAD'); g(r,'push','-u','origin','main')
 # Execute the documented operation and assert the predicted state.
 g(r,'branch','develop'); assert g(r,'branch','--show-current')=='main'; assert g(r,'rev-parse','main')==g(r,'rev-parse','develop')==c
 assert g(r,'status','--porcelain')=='' and g(r,'diff','--cached','--exit-code')=='' and g(r,'diff','--exit-code')==''
 g(r,'push','-u','origin','develop'); assert g(r,'rev-parse','origin/develop')==c
 assert g(r,'for-each-ref','--format=%(upstream)','refs/heads/develop')=='refs/remotes/origin/develop'
 assert g(r,'rev-parse','origin/main')==c and g(r,'rev-parse','topic')==b
 print(f'PASS: main={c[:7]}, develop={g(r,"rev-parse","develop")[:7]}, origin/develop={g(r,"rev-parse","origin/develop")[:7]}; topic remains {b[:7]}, clean tree')
