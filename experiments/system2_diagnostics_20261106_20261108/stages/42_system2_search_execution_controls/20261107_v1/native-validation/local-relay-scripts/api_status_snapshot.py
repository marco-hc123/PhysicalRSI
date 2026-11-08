"""Read only status and usage metadata, never credentials or response text."""
from remote_ops import L,LAB,call
print(call(LAB,f'''import json
from pathlib import Path
r=Path({L!r});s=json.loads((r/'generation-status.json').read_text());a=json.loads((r/'ledger.json').read_text())
print(json.dumps(dict(status=s,requests_reserved=len(a),responses_received=sum(x.get('state')=='received' for x in a),parsed_candidates=sum(bool(x.get('syntax_valid')) for x in a),estimated_usd=sum(x.get('estimated_standard_usd',0) for x in a),round2=[{{k:x.get(k) for k in ['id','state','seconds','http_status','syntax_valid','estimated_standard_usd']}} for x in a if x['batch']=='round2'])))
'''))
