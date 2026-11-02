"""Wait for the experiment, then audit and archive without any new API trials."""
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from cloud_catalogue_common import sha256,write_json

suite=Path(sys.argv[1])
root=Path('/mnt/data/physical-RSI')
state=dict(stage='waiting_for_all_30_cases',finished=False)


def save(stage,**extra):
    state.update(stage=stage,utc=datetime.now(timezone.utc).isoformat(),**extra)
    write_json(suite/'finalization-status.json',state)


try:
    save('waiting_for_all_30_cases')
    while True:
        path=suite/'controller-status.json'
        if path.exists():
            control=json.loads(path.read_text())
            if control.get('needs_review'):raise RuntimeError('Controller requires review; no final archive created')
            if control.get('finished'):break
        time.sleep(10)
    save('waiting_for_original_report_pipeline_exit')
    deadline=time.monotonic()+180
    while subprocess.run(['tmux','has-session','-t','=physicalrsi-catalogue'],capture_output=True).returncode==0:
        if time.monotonic()>deadline:raise RuntimeError('Original report pipeline has not exited')
        time.sleep(3)
    report=json.loads((suite/'suite-report.json').read_text())
    assert report['comparison_valid'], 'Original report has audit issues requiring review'
    analysis=suite/'analysis-sources';analysis.mkdir(exist_ok=True)
    names=['cloud_catalogue_analysis_corrections.py','cloud_catalogue_initial_audit.py','cloud_catalogue_archive.py','cloud_catalogue_finalize.py','cloud_catalogue_finalize_v2.py','catalogue_audit_20261029.txt']
    for name in names:shutil.copy2(root/'result'/name,analysis/name)
    write_json(analysis/'source-hashes.json',{name:sha256(analysis/name) for name in names})
    commands=[
        ('correcting_offline_report',['python3',str(root/'result/cloud_catalogue_analysis_corrections.py'),'--suite',str(suite)]),
        ('checking_paired_initial_observations',[str(root/'models/skill-assets/implementations/openpi/.venv/bin/python'),str(root/'result/cloud_catalogue_initial_audit.py'),'--suite',str(suite)]),
        ('auditing_videos_and_archiving',['python3',str(root/'result/cloud_catalogue_archive.py'),'--suite',str(suite)])]
    for stage,command in commands:
        save(stage)
        with (suite/(stage+'.log')).open('w') as stream:
            subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,check=True)
    save('complete',finished=True,archive=str(suite.with_suffix('.tar.gz')))
    print('FINALIZATION_COMPLETE',str(suite),flush=True)
except Exception as exc:
    save('needs_review',error=dict(type=type(exc).__name__,message=str(exc)))
    raise
