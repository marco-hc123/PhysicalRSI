"""Cloud-only meaningful isolation probes; these are not physical evaluations."""
from pathlib import Path
import json
import os
import sys

O = Path('/mnt/data/physical-RSI/result/25_system2_integration_20261030T050100Z')
cfg = json.loads((O/'attempt-03/runtime.json').read_text())
os.environ.update(cfg['policy_environment'])
sys.path[:0] = cfg['policy_environment']['PYTHONPATH'].split(':')
from PhysicalRSI_core.infra.isolation import execute

(O/'boundary-canary.txt').write_text('non-secret isolation canary')
positive = '''import json, os
json.dump({"uid":os.getuid(),"gid":os.getgid(),"value":2+3},open("/output/result.json","w"))
'''
negative = '''import json, socket
r={}
try:
 open("/mnt/data/physical-RSI/result/25_system2_integration_20261030T050100Z/boundary-canary.txt", "r").read()
 r["host_read_blocked"]=False
except FileNotFoundError:
 r["host_read_blocked"]=True
try:
 socket.socket()
 r["socket_blocked"]=False
except PermissionError:
 r["socket_blocked"]=True
json.dump(r,open("/output/result.json","w"))
'''
rows = {}
for name,source in [('positive',positive),('negative',negative)]:
    (O/(name+'-boundary-probe.py')).write_text(source)
    rows[name] = execute(source,{},runtime=O/'isolation-runtime',output=O/('isolation-'+name),timeout_s=15)
assert rows['positive'] == dict(uid=65534,gid=65534,value=5), rows
assert rows['negative'] == dict(host_read_blocked=True,socket_blocked=True), rows
(O/'isolation-boundary-verification.json').write_text(json.dumps(dict(passed=True,
    scope='software isolation only; no physical task score', results=rows)))
print(rows)
