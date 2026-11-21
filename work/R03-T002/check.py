import subprocess, tempfile
from pathlib import Path

def g(repo, *args):
    return subprocess.run(['git', *args], cwd=repo, text=True, check=True, capture_output=True).stdout.strip()

with tempfile.TemporaryDirectory() as d:
    r=Path(d); g(r,'init','-b','main'); g(r,'config','user.name','Course Student'); g(r,'config','user.email','student@example.invalid')
    (r/'notes.txt').write_text('alpha\n'); g(r,'add','notes.txt'); g(r,'commit','-m','A')
    (r/'notes.txt').write_text('alpha\nbeta\n'); g(r,'add','notes.txt'); g(r,'commit','-m','B'); b=g(r,'rev-parse','HEAD')
    g(r,'branch','topic',b); (r/'todo.txt').write_text('one\n'); g(r,'add','todo.txt'); g(r,'commit','-m','C'); c=g(r,'rev-parse','HEAD'); before_tree=g(r,'rev-parse','HEAD^{tree}')
    g(r,'reset','--soft','HEAD~2'); assert g(r,'rev-parse','main') != c
    assert g(r,'rev-parse','HEAD') == g(r,'rev-parse','main')
    staged=g(r,'diff','--cached','--name-only').splitlines(); assert staged == ['notes.txt','todo.txt']
    g(r,'commit','-m','Combine notes and todo'); s=g(r,'rev-parse','HEAD')
    assert g(r,'rev-parse','HEAD^{tree}') == before_tree and g(r,'rev-parse','topic') == b
    assert g(r,'rev-list','--count','main') == '2' and g(r,'status','--porcelain') == ''
    print(f'PASS: main={s[:7]}, topic={b[:7]}, former C={c[:7]}, same tree={before_tree[:7]}, staged files={staged}, clean')
