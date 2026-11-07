"""Observe current curl children finishing while download schedulers are stopped.

Never resumes a scheduler, starts another download, or renames download data.
"""
from pathlib import Path
import datetime
import hashlib
import json
import os
import time

R=Path('/mnt/data/physical-RSI')
O=R/'result/31_rgb_supplement_20261105'
record=json.loads((O/'PAUSED_NETWORK_CHANGE.json').read_text())
parents=set(record['paused_download_scheduler_pids'])

def active_children():
    rows=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:
            status=dict(x.split(':',1) for x in (proc/'status').read_text().splitlines() if ':' in x)
            if int(status['PPid'].strip()) in parents and status['Name'].strip()=='curl' and not status['State'].strip().startswith('Z'):
                rows.append(int(proc.name))
        except OSError:pass
    return rows

started=time.monotonic()
while True:
    active=active_children()
    row=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),watcher_pid=os.getpid(),
             state='finishing_current_parts_only' if active else 'paused_at_part_boundary',
             active_curl_pids=active,paused_scheduler_pids=sorted(parents),new_downloads_started=False,
             api_calls=0,robot_episodes=0)
    if not active:
        manifest=json.loads((R/'models/official-v4/assets.json').read_text())
        checks=[]
        for asset in manifest['assets']:
            if asset['name'] not in ['pi05-weights','sparse-memory-weights','code-skills']:continue
            for part in asset['parts']:
                canonical=R/'models/official-v4/.downloads'/part['name']
                partial=R/'models/official-v4/.transport-downloads'/(part['name']+'.partial')
                p=canonical if canonical.exists() else partial
                size=p.stat().st_size if p.exists() else 0
                digest=None
                if size==part['size']:
                    h=hashlib.sha256()
                    with p.open('rb') as f:
                        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
                    digest=h.hexdigest()
                checks.append(dict(name=part['name'],path=str(p),bytes=size,expected_bytes=part['size'],sha256=digest,
                                   expected_sha256=part['sha256'],complete_sha256_match=size==part['size'] and digest==part['sha256']))
        row['parts']=checks
        row['verified_complete_parts']=sum(x['complete_sha256_match'] for x in checks)
        row['complete_bytes']=sum(x['bytes'] for x in checks if x['complete_sha256_match'])
        row['note']='Full-size .partial files remain at original paths for suspended schedulers to finalize after explicit user resume.'
    p=O/'pause-boundary-status.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(row,indent=2));tmp.replace(p)
    if not active:break
    if time.monotonic()-started>1300:break
    time.sleep(10)
