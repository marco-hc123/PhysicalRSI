"""One post-run audit dispatch; never restarts scientific work or model calls."""
from pathlib import Path
from datetime import datetime,timezone
import fcntl,hashlib,json,os,subprocess,sys,time
O=Path(sys.argv[1]).resolve()
lock=(O/'finisher.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def record(stage,**kwargs):
    value=dict(utc=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),stage=stage,**kwargs)
    temporary=O/'.postrun-status.tmp';temporary.write_text(json.dumps(value));temporary.replace(O/'postrun-status.json')
record('waiting_for_scientific_controller',no_native_or_model_dispatch=True)
while not (O/'iteration-result.json').exists():
    if (O/'iteration-failed.json').exists():
        record('scientific_interruption_requires_diagnosis',automatic_retry=False);sys.exit(2)
    status=json.loads((O/'controller-status.json').read_text());pid=status.get('pid')
    if pid and not Path('/proc/'+str(pid)).exists():
        record('controller_disappeared_requires_reconciliation',automatic_retry=False);sys.exit(3)
    time.sleep(15)
for i in range(24):
    active=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
    if not active:break
    time.sleep(5)
else:
    record('native_cleanup_not_confirmed',automatic_retry=False);sys.exit(4)
script=O/'procedure-sources/step5_audit.py'
registration=json.loads((O/'audit-registration.json').read_text())
assert hashlib.sha256(script.read_bytes()).hexdigest()==registration['audit_sha256']
record('auditing_completed_scientific_evidence',new_native_episodes=0,new_http_attempts=0)
with (O/'audit.log').open('x') as stream:
    result=subprocess.run(['/mnt/data/physical-RSI/models/skill-assets/implementations/openpi/.venv/bin/python',str(script),str(O)],stdout=stream,stderr=subprocess.STDOUT)
record('audit_complete' if result.returncode==0 else 'audit_requires_diagnosis',audit_exit_code=result.returncode,automatic_retry=False)
sys.exit(result.returncode)
