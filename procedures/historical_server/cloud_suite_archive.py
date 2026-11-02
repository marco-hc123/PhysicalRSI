"""Package experiment evidence after auditing it, without private credentials."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tarfile

root = Path('/mnt/data/physical-RSI/result')
suite = Path(json.loads((root/'CURRENT_EXPERIMENT_SUITE.json').read_text())['directory'])
audit = json.loads((suite/'audit.json').read_text())
assert audit['evaluated_cases_verified'] == 59
assert json.loads((suite/'video-audit.json').read_text())['passed']
secret = json.loads((Path.home()/'.config/physicalrsi/agent.json').read_text())['api_key'].encode()
files = []
for path in sorted(suite.rglob('*')):
    if not path.is_file() or path.name in ('archive-manifest.json', 'controller.lock'):
        continue
    assert not path.is_symlink(), f'Unexpected symlink in evidence: {path.name}'
    data = path.read_bytes()
    assert secret not in data, f'Credential detected in evidence: {path.name}'
    files.append(dict(path=str(path.relative_to(suite)), bytes=len(data),
                      sha256=hashlib.sha256(data).hexdigest()))
manifest = dict(utc=datetime.now(timezone.utc).isoformat(), file_count=len(files),
                bytes=sum(f['bytes'] for f in files), exact_api_key_matches=0,
                files=files)
(suite/'archive-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
archive = root/(suite.name+'.tar.gz')
with tarfile.open(archive, 'w:gz', compresslevel=3) as tar:
    for row in files:
        tar.add(suite/row['path'], arcname=suite.name+'/'+row['path'], recursive=False)
    tar.add(suite/'archive-manifest.json', arcname=suite.name+'/archive-manifest.json')
receipt = dict(archive=str(archive), bytes=archive.stat().st_size,
               sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
               file_count=len(files), exact_api_key_matches=0)
(root/(suite.name+'-archive-receipt.json')).write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
