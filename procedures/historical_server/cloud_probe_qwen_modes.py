"""Replay one fixed native observation, varying only Qwen's thinking flag."""
import base64
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request
import urllib.error

ROOT=Path('/mnt/data/physical-RSI/result')
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=False)
source=ROOT/'17_qwen_agent_episode_20261029T010919Z/api'
base=json.loads((source/'call-001-request.json').read_text())
for m in base['messages']:
    if not isinstance(m['content'],list):continue
    for part in m['content']:
        if part['type']=='image_url':
            data=(source/part['image_url']['artifact']).read_bytes()
            assert hashlib.sha256(data).hexdigest()==part['image_url']['sha256']
            part['image_url']={'url':'data:image/png;base64,'+base64.b64encode(data).decode()}
c=json.loads((Path.home()/'.config/physicalrsi/agent.json').read_text())
context=json.loads(base['messages'][1]['content'][0]['text'])
rows=[]
for repeat in range(1,4):
    for thinking in [False,True]:
        dest=OUT/f"{'thinking' if thinking else 'nonthinking'}-{repeat}"
        payload=deepcopy(base);payload['enable_thinking']=thinking;payload['model']=c['model']
        body=json.dumps(payload).encode();tick=time.monotonic()
        row=dict(thinking=thinking,repeat=repeat,model=c['model'],started_utc=datetime.now(timezone.utc).isoformat(),
                 payload_sha256=hashlib.sha256(body).hexdigest(),robot_executed=False)
        try:
            request=urllib.request.Request(c['endpoint'],data=body,headers={'Authorization':'Bearer '+c['api_key'],'Content-Type':'application/json'})
            with urllib.request.urlopen(request,timeout=300) as response:data=json.load(response)
            row.update(http_success=True,usage=data.get('usage'),returned_model=data.get('model'))
            dest.with_suffix('.response.json').write_text(json.dumps(data,indent=2))
            plan=json.loads(data['choices'][0]['message']['content'])
            valid=isinstance(plan,dict) and set(plan)=={'composition','operations','rationale'}
            valid=valid and plan['composition'] in context['available_compositions'] and isinstance(plan['operations'],list)
            valid=valid and isinstance(plan['rationale'],str) and bool(plan['rationale'].strip())
            if valid:
                if plan['composition']=='memory-guided-program-library':
                    valid=len(plan['operations'])==1 and plan['operations'][0] in context['operation_program']['operations']
                else:valid=not plan['operations']
            row.update(plan=plan,contract_valid=valid,finish_reason=data['choices'][0].get('finish_reason'))
        except urllib.error.HTTPError as e:
            row.update(http_success=False,http_status=e.code,error_body=e.read().decode(errors='replace').replace(c['api_key'],'[REDACTED]')[:2000])
        except Exception as e:
            row.update(error_type=type(e).__name__,error=str(e).replace(c['api_key'],'[REDACTED]'),contract_valid=False)
        row['seconds']=time.monotonic()-tick
        dest.with_suffix('.json').write_text(json.dumps(row,indent=2));rows.append(row)
        t=OUT/'status.json.tmp';t.write_text(json.dumps(dict(completed=len(rows),planned=6,done=len(rows)==6,rows=rows),indent=2));t.replace(OUT/'status.json')
        print('PROBE',thinking,repeat,row.get('contract_valid'),row['seconds'],flush=True)
