"""Read-only independent checks after the controller completes all 10 cases."""
import concurrent.futures,datetime,hashlib,json,re,subprocess,sys,time
from pathlib import Path
R=Path('/mnt/data/physical-RSI');O=R/'result/40_transport_destination_20261107';C=O/'native-campaign';A=O/'analysis'
I=R/'result/25_system2_integration_20261030T050100Z/integration-sources'
sys.path.insert(0,str(I));sys.path.insert(0,str(I/'framework-validation-v3'))
from PhysicalRSI_core.self_harness.artifacts import verify_harness
from PhysicalRSI_baselines.robodojo.evidence import episode_receipt,verify_case
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
start=time.monotonic();campaign=read(C/'campaign.json');status=read(C/'status.json');analysis=read(A/'matrix-analysis.json')
assert status['state']=='diagnostic_matrix_completed' and status['completed_cases']==campaign['planned_cases']
assert status['api_calls']==status['paid_cost_usd']==0
assert sha(campaign['protocol'])==campaign['protocol_sha256'];assert sha(campaign['runtime'])==campaign['runtime_sha256']
for case in campaign['cases']:verify_case(case,campaign['layout_root'])
receipts=[]
for entry in campaign['entries']:
    assert sha(entry['runtime'])==entry['runtime_sha256']
    assert verify_harness(entry['harness'])==entry['harness_sha256']
    base=C/'runs'/entry['name'];done=read(base/'completed.json');folder=Path(done['output'])
    paths=sorted((folder/'episodes').glob('*.json'),key=lambda p:int(p.stem));assert len(paths)==len(campaign['cases'])
    for i,(p,case) in enumerate(zip(paths,campaign['cases'])):
        record=episode_receipt(p,directory=folder,task=case['task'],split=case['split'],layout_sha256=case['layout_sha256'],expert=entry['expert'],harness_sha256=entry['harness_sha256'])
        a=next(x for x in analysis['episodes'] if x['condition']==entry['name'] and x['layout_id']==i)
        assert record['episode_score']==a['normalized_score'] and record['success']==a['success']
        receipts.append(dict(condition=entry['name'],layout_id=i,receipt_sha256=sha(p),harness_sha256=entry['harness_sha256'],state='passed'))
assert len(receipts)==campaign['planned_cases'] and len(analysis['videos'])==3*campaign['planned_cases']
ff=R/'envs/simulator/bin/ffmpeg'
def decode(v):
    p=O/v['file'];assert sha(p)==v['sha256']
    cmd=[str(ff),'-v','error','-xerror','-threads','1','-i',str(p),'-map','0:v:0','-an','-threads','1','-progress','pipe:1','-nostats','-f','null','-']
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    frames=[int(x) for x in re.findall(r'^frame=(\d+)',result.stdout,re.M)]
    episode=next(x for x in analysis['episodes'] if x['condition']==v['condition'] and x['layout_id']==v['layout_id'])
    expected=episode['native_action_count']+1
    valid=result.returncode==0 and bool(frames) and frames[-1]==expected and 'progress=end' in result.stdout
    return dict(file=v['file'],sha256=v['sha256'],state='passed' if valid else 'failed',returncode=result.returncode,decoded_frames=frames[-1] if frames else None,expected_frames=expected,error=result.stderr[-1000:])
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:videos=list(pool.map(decode,analysis['videos']))
(A/'video-decode-validation.json').write_text(json.dumps(videos,indent=2)+'\n')
bad=[v for v in videos if v['state']!='passed']
result=dict(state='passed' if not bad else 'failed',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),valid_native_cases=campaign['planned_cases'],receipt_checks=receipts,decoded_videos=len(videos),failed_videos=len(bad),protocol_sha256=campaign['protocol_sha256'],runtime_sha256=campaign['runtime_sha256'],elapsed_seconds=time.monotonic()-start,api_calls=0,gpu_used=False,scope='Frozen episode_receipt revalidation, live source and harness digest checks, layout identity, analysis/raw agreement, full original video decoding. No experiment rerun.')
(A/'independent-validation.json').write_text(json.dumps(result,indent=2)+'\n')
assert not bad,[(x['file'],x['error']) for x in bad[:3]]
print(json.dumps({k:v for k,v in result.items() if k!='receipt_checks'}))
