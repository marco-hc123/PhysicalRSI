"""Bind privileged diagnostics to the successful native process receipt only."""
import hashlib,json
from pathlib import Path
def select(root):
    root=Path(root);read=lambda p:json.loads(p.read_text());m=read(root/'analysis/matrix-analysis.json');selected=[];bindings=[]
    for condition in sorted(set(e['condition'] for e in m['episodes'])):
        e=next(e for e in m['episodes'] if e['condition']==condition)
        process=root/Path(e['receipt']).parents[1]/'native/processes/simulator/process.json';record=read(process)
        assert record['state']=='completed' and record['returncode']==0
        p=root/'sim-diagnostics'/condition/f'simulator-{record["pid"]}.jsonl';assert p.is_file()
        selected.append(p);bindings.append(dict(condition=condition,process_record=str(process.relative_to(root)),pid=record['pid'],path=str(p.relative_to(root)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    excluded=[dict(path=str(p.relative_to(root)),reason='Not the completed cohort simulator PID; retained as deployment evidence') for p in (root/'sim-diagnostics').rglob('*.jsonl') if p not in selected]
    return selected,dict(selected=bindings,excluded=excluded)
