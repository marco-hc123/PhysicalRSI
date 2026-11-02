from pathlib import Path
import json, os, sys, traceback
from datetime import datetime, timezone
R=Path('/mnt/data/physical-RSI');O=R/'result/25_system2_integration_20261030T050100Z';S=O/'integration-sources';D=S/'native-simulator';F=S/'framework'
env=json.loads((O/'environment-v2.json').read_text());os.environ.update(env);sys.path[:0]=env['PYTHONPATH'].split(':')
from PhysicalRSI_baselines.robodojo import layouts,native_execution,native_preflight
from PhysicalRSI_core.infra.storage import atomic_json
wrapper=S/'simulator-python-v2'
def status(stage,**k):
 v=dict(stage=stage,pid=os.getpid(),complete=False,utc=datetime.now(timezone.utc).isoformat(),**k)
 atomic_json(O/'controller-status.json',v);atomic_json(R/'result/CURRENT_STEP4.json',dict(directory=str(O),**v));print(json.dumps(v),flush=True)
try:
 status('isolated_client_preflight')
 pre=native_preflight.inspect_client(D,python=wrapper,environment=env,output=O/'client-preflight-v2',timeout_s=90)
 assert pre['ready'],pre
 status('fresh_scene_generation')
 layouts.generate_batch(D,R/'code/RoboDojo/Assets',O/'initialization-layouts',tasks=['classify_objects'],count=1,split='development',seed=2026103004,timeout_s=180,workers=1)
 batch=layouts.verify_batch(O/'initialization-layouts/manifest.json',split='development')
 rows=[dict(task=e['task'],split='development',file=e['file'],layout_sha256=e['content_sha256']) for e in batch['entries']]
 status('native_reset_calibration')
 req=dict(simulator_root=str(D),assets_root=str(R/'code/RoboDojo/Assets'),task='classify_objects',split='development',layouts=rows,layout_root=str(O/'initialization-layouts'),gpu=0,seed=0,policy_name='physicalRSI',camera_calibration=True,robot_calibration=True,port=1,endpoint='ws://127.0.0.1:1')
 receipt=native_execution.initialize(req,python=wrapper,environment=env,output=O/'initialization',timeout_s=600)
 atomic_json(O/'initialization-result.json',dict(receipt=str(receipt),scene_hashes=[r['layout_sha256'] for r in rows],physical_actions=0,scope='native reset and calibration only'))
 status('initialization_complete',initialization_receipt=str(receipt))
except BaseException as e:
 status('initialization_failed',error=repr(e));traceback.print_exc();raise
