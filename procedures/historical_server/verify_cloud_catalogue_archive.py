"""Verify the cloud archive in place without downloading or extracting evidence."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path,PurePosixPath
import sys
import tarfile

suite=Path(sys.argv[1])
receipt=json.loads((suite.parent/(suite.name+'-archive-receipt.json')).read_text())
archive=suite.with_suffix('.tar.gz')
assert archive.stat().st_size==receipt['bytes']
digest=hashlib.sha256()
with archive.open('rb') as stream:
    for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
assert digest.hexdigest()==receipt['sha256']
manifest_bytes=(suite/'archive-manifest.json').read_bytes()
manifest=json.loads(manifest_bytes)
assert manifest['file_count']==receipt['file_count']
expected={r['path']:r for r in manifest['files']}
verified={}
manifest_verified=False
with tarfile.open(archive,'r|gz') as tar:
    for member in tar:
        path=PurePosixPath(member.name)
        assert not path.is_absolute() and '..' not in path.parts and path.parts[0]==suite.name
        assert not member.issym() and not member.isdev() and not member.isfifo()
        if member.isdir():continue
        relative=str(PurePosixPath(*path.parts[1:]))
        if relative=='archive-manifest.json':
            assert tar.extractfile(member).read()==manifest_bytes
            manifest_verified=True;continue
        assert relative in expected,relative
        row=expected[relative]
        assert relative not in verified
        if member.islnk():
            link=PurePosixPath(member.linkname)
            assert not link.is_absolute() and '..' not in link.parts and link.parts[0]==suite.name
            target=str(PurePosixPath(*link.parts[1:]))
            assert target in verified and verified[target]==dict(bytes=row['bytes'],sha256=row['sha256']),relative
            verified[relative]=dict(bytes=row['bytes'],sha256=row['sha256']);continue
        assert member.isfile() and member.size==row['bytes'],relative
        digest=hashlib.sha256()
        with tar.extractfile(member) as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
        assert digest.hexdigest()==row['sha256'],relative
        verified[relative]=dict(bytes=member.size,sha256=digest.hexdigest())
assert manifest_verified and set(verified)==set(expected)
assert verified['suite-report-v2.json']['sha256']==receipt['report_sha256']
result=dict(verified=True,utc=datetime.now(timezone.utc).isoformat(),archive=str(archive),
    archive_sha256=receipt['sha256'],verified_files=len(verified),manifest_verified=True,
    report_sha256=receipt['report_sha256'],storage='Cloud only; no local archive backup')
output=suite.parent/(suite.name+'-archive-verification.json')
output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
