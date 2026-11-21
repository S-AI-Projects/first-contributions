import subprocess,tempfile
from pathlib import Path

def g(cwd,*args,check=True):
 return subprocess.run(['git',*args],cwd=cwd,text=True,capture_output=True,check=check).stdout.strip()
def commit(repo,name,contents):
 (repo/name).write_text(contents); g(repo,'add',name); g(repo,'commit','-m',name)
with tempfile.TemporaryDirectory() as d:
 root=Path(d); bare=root/'upstream.git'; g(root,'init','--bare',str(bare)); seed=root/'seed'; g(root,'clone',str(bare),str(seed)); g(seed,'config','user.name','Course Student'); g(seed,'config','user.email','student@example.invalid'); g(seed,'switch','-c','main'); commit(seed,'notes.txt','alpha\n'); commit(seed,'notes.txt','alpha\nbeta\n'); b_tip=g(seed,'rev-parse','HEAD'); g(seed,'branch','topic',b_tip); commit(seed,'todo.txt','one\n'); c_tip=g(seed,'rev-parse','HEAD'); g(seed,'push','-u','origin','main'); g(seed,'push','origin','topic'); g(bare,'symbolic-ref','HEAD','refs/heads/main')
 clones=[]
 for label in ('explicit','pull'):
  r=root/label; g(root,'clone',str(bare),str(r)); g(r,'config','user.name','Course Student'); g(r,'config','user.email','student@example.invalid'); g(r,'remote','rename','origin','upstream'); g(r,'switch','main'); assert g(r,'rev-parse','refs/remotes/upstream/topic')==b_tip; commit(r,f'{label}.txt',label+' local\n'); clones.append(r)
 g(seed,'switch','main'); commit(seed,'remote.txt','remote update\n'); g(seed,'push','origin','main')
 a,b=clones; g(a,'fetch','upstream'); upstream_tip=g(a,'rev-parse','upstream/main'); g(a,'rebase','upstream/main'); g(b,'pull','--rebase','upstream','main')
 for repo in clones:
  assert g(repo,'rev-parse','HEAD')==g(repo,'rev-parse','main')
  assert g(repo,'merge-base','HEAD','upstream/main')==upstream_tip
  assert g(repo,'status','--porcelain')=='' and (repo/'remote.txt').read_text()=='remote update\n'
 assert g(a,'rev-parse','upstream/main')==g(b,'rev-parse','upstream/main')
 print('PASS: fetch+rebase and pull --rebase reach upstream tip; local commits retained; clean trees')
