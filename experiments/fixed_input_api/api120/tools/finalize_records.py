"""Audit completed records and make a checksum manifest; no model requests."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(root):
    manifest=read(root/'execution_manifest.json')
    schedule=read(root/'inputs/schedule.json')
    rows=sorted([read(p) for p in (root/'responses').glob('*.json')],key=lambda x:x['sequence'])
    events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
    started=Counter(x['id'] for x in events if x['event']=='started')
    completed=Counter(x['id'] for x in events if x['event']=='completed')
    assert set(started)==set(completed)=={x['id'] for x in schedule}
    assert set(started.values())==set(completed.values())=={1}
    assert len(rows)==120
    request_map=read(root/'inputs/request_manifest.json')
    for entry in manifest['input_files']:
        assert sha(root/'inputs'/entry['path'])==entry['sha256']
    assert sha(root/'tools/run_live.py')==manifest['runner_sha256']
    for row,item in zip(rows,schedule):
        for key,value in item.items():
            assert row[key]==value,(row['id'],key)
        body=read(root/'inputs'/request_map[item['request_id']]['path'])
        assert hashlib.sha256(json.dumps(body).encode()).hexdigest()==row['request_sha256']
        raw_path=root/'raw_responses'/(row['id']+'.json')
        assert sha(raw_path)==row['response_sha256']
        raw=read(raw_path)
        assert raw.get('usage')==row['raw_usage']
        assert row['input_tokens']+row['output_tokens']==row['total_tokens']
        assert row['elapsed_seconds']>0
    ids=[r['provider_id'] for r in rows if r.get('provider_id')]
    assert len(ids)==len(set(ids))==120
    preparations=Path(manifest['source_preparation'])
    assert sha(preparations/'file_manifest.json')==manifest['preparation_manifest_sha256']
    for entry in read(preparations/'file_manifest.json'):
        assert sha(preparations/entry['path'])==entry['sha256']
    original=root.parent/'03_api_experiments'
    original_manifest=read(original/'file_manifest.json')
    for entry in original_manifest:
        assert sha(original/entry['path'])==entry['sha256']
    matches=[]
    for path in root.rglob('*'):
        if path.is_file() and path.suffix in ('.json','.jsonl','.py','.txt','.csv'):
            if re.search(r'(?<![A-Za-z0-9_-])sk-(?:ws-)?[A-Za-z0-9_.-]{20,}',path.read_text()):
                matches.append(str(path.relative_to(root)))
    assert not matches,matches
    summary=read(root/'summary.json')
    assert summary['status']=='completed' and summary['recorded_responses']==120
    for field,metric in [('input_tokens_total','input_tokens'),('output_tokens_total','output_tokens'),('total_tokens','total_tokens')]:
        assert summary[field]==sum(r[metric] for r in rows)
    result=dict(status='verified',verified_at_utc=datetime.now(timezone.utc).isoformat(),
                scheduled_attempts=120,unique_started_ids=len(started),unique_completed_ids=len(completed),
                raw_responses_verified=120,provider_ids_unique=120,request_hashes_verified=120,
                preparation_files_unchanged=True,prior_80_call_files_verified=len(original_manifest),
                credential_pattern_findings=matches,monetary_ceiling=None,automatic_retries=0,
                detailed_analysis='Deferred at user request')
    (root/'completion_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    files=[dict(path=str(p.relative_to(root)),sha256=sha(p),bytes=p.stat().st_size)
           for p in sorted(root.rglob('*')) if p.is_file() and p.name!='file_manifest.json' and '__pycache__' not in p.parts]
    (root/'file_manifest.json').write_text(json.dumps(files,indent=2)+'\n')
    print(json.dumps(dict(**result,files=len(files),manifest_sha256=sha(root/'file_manifest.json'))))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    main(parser.parse_args().root.resolve())
