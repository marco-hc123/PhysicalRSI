"""Freeze strategies before any heldout layout generation or evaluation."""
import datetime,hashlib,json
from pathlib import Path
from select_development import choose,metric
O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
assert not (O/'heldout-layouts').exists() and not (O/'selection-final.json').exists()
rows=[];entries={};sources=[]
for phase in ['parent','sampling','round2','repair']:
 assert read(O/phase/'analysis/independent-validation.json')['state']=='passed'
 m=read(O/phase/'analysis/matrix-analysis.json');rows+=m['episodes']
 for e in read(O/phase/'native-campaign/campaign.json')['entries']:entries[e['name']]=e
 p=O/phase/'analysis/matrix-analysis.json';sources.append(dict(path=str(p.relative_to(O)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
initial=read(O/'sampling-selection.json');parent=initial['budget5']['selected']
second=choose(rows,[f'round2_{i:02}' for i in range(1,4)],parent)
aliases=[dict(label='fixed_initial_parent',selected='fixed_parent'),dict(label='budget1',selected=initial['budget1']['selected']),dict(label='budget5',selected=parent),dict(label='two_round_feedback_search',selected=second['selected'])]
repair_rows={n:[x for x in rows if x['condition']==n] for n in ['target_control','target_offset']}
assert all(len(x)==5 for x in repair_rows.values())
manual_better=metric(repair_rows['target_offset'])>metric(repair_rows['target_control'])
if manual_better:aliases.append(dict(label='manual_target_repair_reference',selected='target_offset',scope='Separate human-designed repair, not a System2 candidate-count or autonomous-improvement claim'))
unique=[];identities={};identity_rows=[]
for a in aliases:
 e=entries[a['selected']];h=Path(e['harness']['root']);source=(h/'code/classify_objects.py').read_text();memory=read(h/'memory_rules.json')['classify_objects'];cfg=read(Path(e['runtime']))
 contract=dict(entrypoint=cfg['policy_spec']['entrypoint'],configuration={k:v for k,v in cfg['policy_spec']['configuration'].items() if k!='output'})
 assert contract['entrypoint']=='structured_feedback:assemble'
 key=hashlib.sha256(json.dumps(dict(source=source,memory=memory,contract=contract),sort_keys=True,separators=(',',':')).encode()).hexdigest()
 if key not in identities:
  identities[key]=e['name'];origin=e['origin'].copy();origin['name']=e['name'];unique.append(origin)
  identity_rows.append(dict(condition=e['name'],identity_sha256=key,source_sha256=hashlib.sha256(source.encode()).hexdigest(),memory_sha256=hashlib.sha256(json.dumps(memory,sort_keys=True,separators=(',',':')).encode()).hexdigest(),development_runtime=e['runtime']))
 a['evaluated_as']=identities[key];a['development_metric']=metric([x for x in rows if x['condition']==a['selected']])
assert 1<=len(unique)<=4
result=dict(frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),heldout_seen=False,round1_selection=initial,round2_selection=second,manual_repair_eligible=manual_better,manual_repair_development_metrics={k:metric(v) for k,v in repair_rows.items()},strategies=aliases,unique_entries=unique,identities=identity_rows,runtime_reference=entries['fixed_parent']['runtime'],development_sources=sources,heldout_selection_prohibited=True,scope='Five fresh native-qualified layouts generated only after this freeze. Identical source+memory+executor strategies share one physical evaluation and are explicitly marked as evidence reuse. The manual reference, if eligible, is reported separately and cannot count as a System2 success.',unchanged_global_policy_registry=True)
(O/'selection-final.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(state='selection_frozen',strategies=aliases,unique_physical_strategies=len(unique),round2_selected=second['selected'],manual_reference_included=manual_better)))
