"""Validate completed native reference; no retry or synthetic success."""
import json,hashlib,sys,subprocess,re,concurrent.futures,datetime
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[1];I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path[:0]=[str(I),str(I/'framework-validation-v3')]
from PhysicalRSI_baselines.robodojo.evidence import episode_receipt,verify_case
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert read(O/'status.json')['state']=='reference_completed'
req=read(O/'native/request.json');out=read(O/'outcomes.json');A=O/'analysis';A.mkdir(exist_ok=True)
assert out['native_cases']==5 and len(out['rows'])==5
receipts=[]
for i,case in enumerate(req['layouts']):
 verify_case(case,req['layout_root'])
 p=O/'native/episodes'/f'{i}.json';r=episode_receipt(p,directory=O/'native',task=case['task'],split=case['split'],layout_sha256=case['layout_sha256'],expert=req['expert'],harness_sha256=req['harness_sha256'])
 row=out['rows'][i];assert row['episode_score']==r['episode_score'] and row['success']==r['success']
 receipts.append(dict(layout=i,sha256=sha(p),score=r['episode_score'],success=r['success']))
videos=sorted((O/'native').rglob('*.mp4'));assert len(videos)==15
def decode(p):
 i=int(p.name.split('_')[1]);expected=out['rows'][i]['diagnostics']['action_count']+1
 command=[str(R/'envs/simulator/bin/ffmpeg'),'-v','error','-xerror','-threads','1','-i',str(p),'-map','0:v:0','-an','-threads','1','-progress','pipe:1','-nostats','-f','null','-']
 d=subprocess.run(command,capture_output=True,text=True,timeout=120);frames=[int(x) for x in re.findall(r'^frame=(\d+)',d.stdout,re.M)]
 return dict(file=str(p.relative_to(O)),layout=i,sha256=sha(p),frames=frames[-1] if frames else None,expected_frames=expected,state='passed' if d.returncode==0 and frames and frames[-1]==expected and 'progress=end' in d.stdout else 'failed',stderr=d.stderr[-1000:])
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:v=list(pool.map(decode,videos))
(A/'video-decode-validation.json').write_text(json.dumps(v,indent=2)+'\n');assert all(x['state']=='passed' for x in v)
events=[json.loads(x) for x in (O/'service-events.jsonl').read_text().splitlines()];resets=[x for x in events if x['event']=='reset'];assert len(resets)==5
episodes=[]
for i,row in enumerate(out['rows']):
 actions=[x for x in events if x.get('episode')==i and x['event']=='action'];init=[x for x in events if x.get('episode')==i and x['event']=='initial_observation']
 traces=sorted({x['trace'] for x in init if x['trace']});trace_events=[]
 for name in traces:trace_events += [json.loads(x) for x in Path(name).read_text().splitlines()]
 episodes.append(dict(**row,last_model_stage=actions[-1]['stage'] if actions else None,last_model_failure=actions[-1]['failure'] if actions else None,observed_stages=sorted(set(x['stage'] for x in actions)),source_traces=[str(Path(x).relative_to(O)) for x in traces],completed_basket_transfers=sum(x.get('completed_transfer')=='basket' for x in trace_events),incomplete_reasons=[x for x in trace_events if 'rgb_category_incomplete' in x or 'source_local_continuation' in x],note='Transfer events are controller reports, not native success or object-count ground truth.'))
result=dict(state='passed',native_cases=5,videos=15,receipt_checks=receipts,episodes=episodes,api_calls=0,scope='Released controller reference, not a System2 candidate or new independent validation')
(A/'independent-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(state='passed',cases=5,videos=15,scores=[100*x['episode_score'] for x in episodes],stages=[x['last_model_stage'] for x in episodes])))
