"""Verify videos, scan portable evidence, and archive a completed cloud study."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
from cloud_catalogue_common import sha256,verify_source_pins,write_json

parser=argparse.ArgumentParser()
parser.add_argument('--suite',type=Path,required=True)
args=parser.parse_args()
suite=args.suite
controller=json.loads((suite/'controller-status.json').read_text())
assert controller['finished'] and len(controller['jobs'])==30
verify_source_pins(suite)
report=suite/'suite-report-v2.json'
assert report.is_file(), 'Corrected offline report must be generated first'
videos=json.loads((suite/'video-manifest.json').read_text())
if isinstance(videos,dict):
    videos=videos.get('videos',videos.get('files',[]))
streams=[]
for path in sorted(suite.glob('r*_layout*/videos/*.mp4')):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames',
        '-show_entries','stream=width,height,nb_read_frames,codec_name,duration','-of','json',str(path)],text=True))
    assert len(data['streams'])==1,str(path)
    stream=data['streams'][0]
    assert stream['width']>0 and stream['height']>0 and int(stream['nb_read_frames'])>0,str(path)
    streams.append(dict(path=str(path.relative_to(suite)),bytes=path.stat().st_size,**stream))
native=[j for j in controller['jobs'] if j['native_complete']]
assert len(streams)==3*len(native),(len(streams),len(native))
for job in native:
    group=[s for s in streams if Path(s['path']).parts[0]==job['name']]
    assert len(group)==3 and len({int(s['nb_read_frames']) for s in group})==1,job['name']
write_json(suite/'video-audit.json',dict(passed=True,native_episodes=len(native),video_streams=len(streams),
    total_frames=sum(int(s['nb_read_frames']) for s in streams),streams=streams))
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip()
assert int(gpu.split(',')[0].split()[0])==0, 'Experiment GPU memory has not been released'
write_json(suite/'final-server-state.json',dict(utc=datetime.now(timezone.utc).isoformat(),gpu=gpu,
    ecs_action='Instance remains running; not stopped or released',
    disk_usage=subprocess.check_output(['df','-h','/mnt/data','/'],text=True)))
write_json(suite/'COMPLETION.json',dict(completed_utc=datetime.now(timezone.utc).isoformat(),
    evaluated_cases=30,native_episodes=len(native),api_only_cases=10,video_streams=len(streams),
    final_report='suite-report-v2.json',report_sha256=sha256(report),source_pins_reverified=True,
    scope='Developmental general_pickup catalogue projection comparison on five layouts with three repeats',
    server_stopped=False))
secret=json.loads((Path.home()/'.config/physicalrsi/agent.json').read_text())['api_key'].encode()
files=[]
for path in sorted(suite.rglob('*')):
    if not path.is_file() or path.name=='archive-manifest.json' or path.name.endswith('.lock'):continue
    assert not path.is_symlink(),str(path)
    digest=hashlib.sha256()
    tail=b''
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            assert secret not in tail+block,'Credential found in evidence; archive refused'
            tail=block[-len(secret):]
            digest.update(block)
    files.append(dict(path=str(path.relative_to(suite)),bytes=path.stat().st_size,sha256=digest.hexdigest()))
write_json(suite/'archive-manifest.json',dict(file_count=len(files),exact_api_key_matches=0,files=files))
archive=suite.with_suffix('.tar.gz')
assert not archive.exists(),'Keep completed archive immutable'
with tarfile.open(archive,'w:gz',compresslevel=2) as tar:
    tar.add(suite,arcname=suite.name,filter=lambda info:None if info.name.endswith('.lock') else info)
receipt=dict(archive=str(archive),bytes=archive.stat().st_size,sha256=sha256(archive),file_count=len(files),
             report_sha256=sha256(report),exact_api_key_matches=0)
write_json(suite.parent/(suite.name+'-archive-receipt.json'),receipt)
write_json(suite.parent/'CURRENT_COMPLETED_CATALOGUE_STUDY.json',dict(directory=str(suite),**receipt))
print(json.dumps(receipt))
