
from pathlib import Path
import subprocess,threading,time,json,datetime
root=Path('/mnt/data/physical-RSI');out=root/'result/31_rgb_supplement_20261105/rgb-smoke'
stop=threading.Event();samples=[]
def monitor():
 with (out/'gpu_samples.jsonl').open('w') as f:
  while not stop.is_set():
   p=subprocess.run(['nvidia-smi','--query-gpu=timestamp,memory.used,utilization.gpu,temperature.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=15)
   row={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'values':p.stdout.strip(),'exit_code':p.returncode}
   f.write(json.dumps(row)+'\n');f.flush()
   try:samples.append(float(p.stdout.split(',')[1].strip()))
   except (ValueError,IndexError):pass
   stop.wait(1)
thread=threading.Thread(target=monitor,daemon=True);thread.start();start=time.monotonic();code=None
try:
 with (out/'stdout.log').open('w') as log:
  p=subprocess.run([str(root/'envs/run-simulator.sh'),str(out/'render_rgb.py')],stdout=log,stderr=subprocess.STDOUT,timeout=1200)
  code=p.returncode
finally:
 stop.set();thread.join(timeout=20)
 result={'process_exit_code':code,'elapsed_seconds':time.monotonic()-start,'gpu_peak_memory_mib':max(samples) if samples else None,'gpu_sample_count':len(samples),'robot_episodes':0,'api_calls':0}
 (out/'execution.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
 print((out/'stdout.log').read_text(errors='replace')[-7000:],flush=True)
if code:raise SystemExit(code)
