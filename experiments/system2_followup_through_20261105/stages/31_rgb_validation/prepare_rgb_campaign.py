"""Package exact saved candidates for the frozen, API-free native campaign.

The historical candidate assets manifest contained two outer campaign metadata
keys. They are retained in provenance; the runtime's own exact identity is used
in new physical harness directories. No frozen runtime/source file is edited.
"""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sys

R=Path('/mnt/data/physical-RSI')
O=R/'result/31_rgb_supplement_20261105'
I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path.insert(0,str(I/'framework-validation-v3'))
from PhysicalRSI_core.infra.storage import atomic_json, digest, file_digest, read_json
from PhysicalRSI_core.self_harness.artifacts import CLOSURE, verify_harness
from PhysicalRSI_baselines.robodojo.native_runtime import NativeRuntime
from PhysicalRSI_baselines.robodojo.evidence import verify_case
from PhysicalRSI_baselines.robodojo.workflow import manifest

P=O/'protocol/diagnostic-matrix-v1.json'
assert file_digest(P)=='60816ebccd9fc07bae5e252efb67d8806a941adadbe84d788bbb7695d81d665d'
protocol=read_json(P)
runtime_path=Path(protocol['runtime']['path'])
assert file_digest(runtime_path)==protocol['runtime']['sha256']
config=read_json(runtime_path)
runtime=NativeRuntime(config)
identity=runtime.identity()
old=runtime_path.parent/'workspace/rounds/round-000000'
old_assets=read_json(old/'candidate/assets.json')
extras={k:v for k,v in old_assets.items() if k not in identity}
assert set(extras)=={'campaign_adapter_sha256','historical_exclusions_sha256'}
assert all(old_assets[k]==v for k,v in identity.items())
cases=read_json(old/'validation-cases.json')
layout_root=old/'validation-layouts'
assert len(cases)==5
for case,row in zip(cases,protocol['matrix']['layouts']):
    assert case['file']==row['file'] and case['layout_sha256']==row['layout_sha256']
    assert file_digest(layout_root/case['file'])==row['raw_file_sha256']
    verify_case(case,layout_root)

destination=O/'native-campaign'
destination.mkdir(exist_ok=True)
index_path=destination/'campaign.json'
if index_path.exists():
    existing=read_json(index_path)
    for item in existing['entries']:
        assert verify_harness(item['harness'])==item['harness_sha256']
    print(json.dumps(dict(state='already_prepared',entries=len(existing['entries']))))
    raise SystemExit(0)

saved={x['name']:x for x in protocol['matrix']['saved_candidates']}
entries=[]
for name in protocol['matrix']['execution_order']:
    path=destination/'harnesses'/name
    path.mkdir(parents=True,exist_ok=False)
    for kind in sorted(CLOSURE):
        shutil.copy2(old/'candidate'/(kind+'.json'),path/(kind+'.json'))
    for value in read_json(path/'skills.json').values():
        source=value['source']; (path/source).parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(old/'candidate'/source,path/source)
    atomic_json(path/'assets.json',identity)
    if name=='pi05':
        expert=config['experts']['pi05']['spec']['expert']
        origin=dict(role='retained pretrained pi05; no Agent planner or model generation')
    else:
        row=saved[name]
        source=Path(row['source'])
        assert file_digest(source)==row['source_sha256']
        assert file_digest(source.parent/'proposal.json')==row['proposal_sha256']
        shutil.copy2(source,path/'code/classify_objects.py')
        expert=dict(name='code.classify_objects',revision=row['source_sha256'])
        atomic_json(path/'skills.json',{expert['name']:dict(revision=expert['revision'],source='code/classify_objects.py')})
        origin=dict(role='saved candidate execution; no new generation',**row)
    atomic_json(path/'skill_selection.json',dict(skill_choices={'classify_objects':expert}))
    harness=manifest(path,'rgb_'+name)
    revision=verify_harness(harness)
    admission=runtime.admit(harness,O/'native-preparation'/'admission'/name)
    assert admission['accepted'],admission
    entries.append(dict(name=name,harness=harness,harness_sha256=revision,expert=expert,origin=origin))

record=dict(schema='physicalrsi.rgb-campaign/v1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    protocol=str(P),protocol_sha256=file_digest(P),runtime=str(runtime_path),runtime_sha256=file_digest(runtime_path),
    layout_root=str(layout_root),cases=cases,entries=entries,planned_cases=35,
    bookkeeping=dict(historical_outer_campaign_metadata=extras,
      runtime_shared_fields_unchanged=True,old_assets_sha256=file_digest(old/'candidate/assets.json'),
      new_assets_sha256=file_digest(destination/'harnesses/pi05/assets.json'),
      changes='New physical harness copies; exact native identity manifest; exact saved source SHA and explicit frozen expert selection per condition. Historical evidence untouched.'),
    api_calls=0,selection='diagnostic only; retained pi05 unchanged')
atomic_json(index_path,record)
atomic_json(O/'native-preparation/initial-layout-evidence-check.json',dict(state='verified',cases=5,original_artifacts_restored=True))
print(json.dumps(dict(state='prepared',entries=len(entries),cases=5,planned_native_cases=35,index=str(index_path),api_calls=0)))
