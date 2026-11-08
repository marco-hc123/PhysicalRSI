"""Post-hoc read-only-source audit; never relax or rerun a frozen candidate."""
import ast, datetime, hashlib, json
from pathlib import Path
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for phase,prefix,count in [('sampling','sample',5),('round2','round2',3)]:
    audit=json.loads((O/phase/'native-preparation/candidate-audit.json').read_text())
    for i in range(1,count+1):
        name=f'{prefix}_{i:02}';request=O/'requests'/(name+'.json');source=O/'candidates'/name/'candidate.py'
        d=json.loads(request.read_text());visible=json.dumps(d['messages']);code=source.read_text();lines=code.splitlines()
        nodes=[dict(line=n.lineno,text=lines[n.lineno-1]) for n in ast.walk(ast.parse(code)) if isinstance(n,ast.Nonlocal)]
        a=next(x for x in audit if x['name']==name)
        rows.append(dict(phase=phase,candidate=name,admitted=a['admitted'],errors=a.get('errors',[]),nonlocal_statements=nodes,nonlocal_mentioned_in_request='nonlocal' in visible.lower(),source_sha256=sha(source),request_sha256=sha(request),native_outcome='evaluated' if a['admitted'] else 'not_evaluated_not_zero_score'))
out=dict(state='audited',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate_rows=rows,frozen_admission_source=dict(path='round2/native-preparation/candidate-audit.json',sha256=sha(O/'round2/native-preparation/candidate-audit.json')),study_guard_source=dict(path='prepare_phase.py',sha256=sha(O/'prepare_phase.py')),finding='The study-specific preparation guard rejects ast.Nonlocal. Both rejected round2 candidates use it only for a nested call counter. The serialized model-visible requests do not mention nonlocal. This is a disclosed generation/admission contract gap in this campaign; it is not a demonstrated upstream PhysicalRSI defect and it supplies no physical outcome for those candidates.',consequences=['Preserve frozen candidates, admission decisions, selection and heldout protocol unchanged.','Do not treat syntactic parse success as native admission.','Do not fabricate two five-layout groups or assign them score0.','Future study should make the full frozen grammar/allowed builtins explicit and preflight it before paying for generation; any relaxation or semantics-preserving counter rewrite is a separately labeled intervention, not this round.'],new_api_calls=0,new_native_episodes=0,gpu_used=False)
p=O/'admission-contract-audit.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(state=out['state'],generated=len(rows),rejected=sum(not x['admitted'] for x in rows),new_native_episodes=0)))
