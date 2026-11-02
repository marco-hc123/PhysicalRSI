"""Read-only GPU telemetry for an already-running fifth-step experiment."""
from pathlib import Path
from datetime import datetime,timezone
import csv,fcntl,json,os,subprocess,sys,time
O=Path(sys.argv[1]).resolve()
lock=(O/'telemetry.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
with (O/'gpu-telemetry.csv').open('x') as stream:
    writer=csv.writer(stream);writer.writerow(['utc','observer_pid','controller_pid','stage','round_index','native_requested','native_completed','gpu_memory_MiB','gpu_util_percent','power_W'])
    while True:
        status=json.loads((O/'controller-status.json').read_text())
        budget=json.loads((O/'native-budget.json').read_text()) if (O/'native-budget.json').exists() else {}
        values=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu,power.draw','--format=csv,noheader,nounits'],text=True).strip().split(', ')
        writer.writerow([datetime.now(timezone.utc).isoformat(),os.getpid(),status.get('pid'),status.get('stage'),status.get('round_index'),budget.get('requested',0),budget.get('completed',0),*values]);stream.flush()
        if (O/'iteration-result.json').exists() or (O/'iteration-failed.json').exists():
            break
        pid=status.get('pid')
        if pid and not Path('/proc/'+str(pid)).exists():
            break
        time.sleep(10)
