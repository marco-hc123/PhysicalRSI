"""Small read-only streaming status; disconnect never stops the experiment."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys,time
O=Path(sys.argv[1]).resolve()
while True:
    s=json.loads((O/'controller-status.json').read_text())
    b=json.loads((O/'native-budget.json').read_text()) if (O/'native-budget.json').exists() else {}
    last=[row for row in b.get('batches',[]) if row['state']=='completed'][-1:]
    row=dict(utc=datetime.now(timezone.utc).isoformat(),stage=s['stage'],round=s.get('round_index'),
        requested=b.get('requested',0),completed=b.get('completed',0),
        recent=[dict(split=x['split'],scores=x.get('scores'),successes=x.get('successes')) for x in last],
        gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip())
    print(json.dumps(row),flush=True)
    if (O/'iteration-result.json').exists() or (O/'iteration-failed.json').exists():
        if (O/'iteration-failed.json').exists():
            d=json.loads((O/'iteration-failed.json').read_text());print(json.dumps({k:v for k,v in d.items() if k!='traceback'}),flush=True)
        break
    if s.get('pid') and not Path('/proc/'+str(s['pid'])).exists():
        print('Controller no longer exists; reconcile before retry',flush=True);break
    time.sleep(45)
