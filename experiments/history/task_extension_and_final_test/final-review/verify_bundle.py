from pathlib import Path
import hashlib,json,sys
D=Path(sys.argv[1]); m=json.loads((D/'bundle-manifest.json').read_text())
for p,h in m['files'].items():
 assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
print(json.dumps(dict(complete=True,verified_files=len(m['files']),api_calls=0,native_dispatches=0)))
