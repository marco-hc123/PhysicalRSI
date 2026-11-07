"""Verify received frozen resources; install verified official weight archives.

Runs on the target server. Does not start a policy, robot episode, or model API.
"""
from pathlib import Path
import argparse
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import time

R=Path('/mnt/data/physical-RSI')
O=R/'result/31_rgb_supplement_20261105/resource-verification'
O.mkdir(parents=True,exist_ok=True)

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()

def write(p,d):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2));tmp.replace(p)

def verify_weights(install=False,bind=False):
    started=time.monotonic();a=R/'models/official-v4'
    raw=(a/'assets.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='0eed83202427dc6b4c75cde613246f8f6e606cac6c8da3bd71ebc6798d6963d2'
    manifest=json.loads(raw)
    assets=[x for x in manifest['assets'] if x['name'] in ['pi05-weights','sparse-memory-weights']]
    part_rows=[]
    for asset in assets:
        for part in asset['parts']:
            p=a/'.downloads'/part['name']
            ok=p.is_file() and p.stat().st_size==part['size'] and sha(p)==part['sha256']
            part_rows.append(dict(name=part['name'],bytes=part['size'],match=ok))
    write(O/'weight-part-checks.json',dict(parts=part_rows,all_match=all(x['match'] for x in part_rows)))
    assert all(x['match'] for x in part_rows),'Incomplete or mismatched archive part; preserved for review'
    if install:
        path=R/'code/RoboDojo/XPolicyLab/policy/physicalRSI/download_assets.py'
        spec=importlib.util.spec_from_file_location('official_asset_installer',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        # All downloads must have been preverified above. Installation is offline.
        def deny_network(*args,**kwargs):raise RuntimeError('Unexpected installer network access')
        module.urllib.request.urlopen=deny_network
        for asset in assets:
            destination=a/asset['destination']
            if not destination.exists():module.install(asset,a)
    freeze=json.loads((R/'reference/result/14_protocol_freeze/23_protocol_freeze_20261029T132917Z/checkpoint-freeze.json').read_text())
    rows=[]
    for checkpoint in freeze['checkpoints']:
        for entry in checkpoint['files']:
            p=a/'checkpoints'/checkpoint['skill']/entry['relative_path']
            before=p.stat() if p.is_file() else None
            digest=sha(p) if before and before.st_size==entry['bytes'] else None
            after=p.stat() if before else None
            ok=bool(before and after and before.st_size==entry['bytes'] and digest==entry['sha256'] and before.st_mtime_ns==after.st_mtime_ns)
            rows.append(dict(skill=checkpoint['skill'],relative_path=entry['relative_path'],bytes=entry['bytes'],expected_sha256=entry['sha256'],actual_sha256=digest,match=ok))
    data=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),state='verified' if all(x['match'] for x in rows) else 'needs_review',
              files=rows,file_count=len(rows),matched=sum(x['match'] for x in rows),elapsed_s=time.monotonic()-started,
              bytes=sum(x['bytes'] for x in rows),api_calls=0,gpu_used=False)
    write(O/'weights.json',data)
    assert len(rows)==41 and all(x['match'] for x in rows),'Extracted checkpoints differ from frozen experiment'
    if bind:
        marker=json.loads((O/'checkpoint-relay-superseded.json').read_text())
        assert marker['relay_stopped'] is True
        target=R/'reference/models/recorded_policy_assets/skill-assets/checkpoints'
        desired=a/'checkpoints'
        if target.is_symlink():assert target.resolve()==desired.resolve()
        else:
            backup=target.with_name('checkpoints.relay-partial-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
            if target.exists():target.rename(backup)
            target.symlink_to(desired,target_is_directory=True)
            write(O/'weight-binding.json',dict(target=str(target),verified_source=str(desired),preserved_partial=str(backup),all_41_frozen_hashes_match=True))
    print(json.dumps({k:v for k,v in data.items() if k!='files'}),flush=True)

def verify_group(name,root_override=None,receipt_name=None):
    started=time.monotonic()
    source=json.loads((R/'result/31_rgb_supplement_20261105/resource-source-sha256.json').read_text())['groups'][name]
    root=root_override or {'scene_assets':R/'reference/data/simulation_assets/robodojo-complete-source',
          'implementations':R/'reference/models/recorded_policy_assets/skill-assets/implementations'}[name]
    cache={};rows=[]
    for entry in source['files']:
        p=root/entry['path'];before=p.stat() if p.is_file() else None
        digest=None
        if before and before.st_size==entry['bytes']:
            key=(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)
            if key not in cache:cache[key]=sha(p)
            digest=cache[key]
        after=p.stat() if before else None
        ok=bool(before and after and digest==entry['sha256'] and before.st_mtime_ns==after.st_mtime_ns)
        rows.append(dict(path=entry['path'],bytes=entry['bytes'],expected_sha256=entry['sha256'],actual_sha256=digest,match=ok))
    data=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),state='verified' if all(x['match'] for x in rows) else 'needs_review',
              files=rows,file_count=len(rows),matched=sum(x['match'] for x in rows),unique_files_hashed=len(cache),
              unique_bytes=source['unique_bytes'],elapsed_s=time.monotonic()-started,api_calls=0,gpu_used=False)
    data['verified_root']=str(root)
    write(O/((receipt_name or name)+'.json'),data)
    print(json.dumps({k:v for k,v in data.items() if k!='files'}),flush=True)
    assert all(x['match'] for x in rows),name+' mismatches preserved for review'

def stage_code_archive():
    a=R/'models/official-v4';raw=(a/'assets.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='0eed83202427dc6b4c75cde613246f8f6e606cac6c8da3bd71ebc6798d6963d2'
    asset=next(x for x in json.loads(raw)['assets'] if x['name']=='code-skills')
    for part in asset['parts']:
        p=a/'.downloads'/part['name']
        assert p.is_file() and p.stat().st_size==part['size'] and sha(p)==part['sha256'],part['name']
    path=R/'code/RoboDojo/XPolicyLab/policy/physicalRSI/download_assets.py'
    spec=importlib.util.spec_from_file_location('official_asset_installer',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    def deny_network(*args,**kwargs):raise RuntimeError('Unexpected installer network access')
    module.urllib.request.urlopen=deny_network
    if not (a/asset['destination']).exists():module.install(asset,a)
    openpi=a/'implementations/openpi'
    expected=R/'reference/models/recorded_policy_assets/skill-assets/implementations/openpi'
    if openpi.is_symlink():assert openpi.resolve()==expected.resolve()
    else:
        assert not openpi.exists()
        openpi.symlink_to(expected,target_is_directory=True)
    verify_group('implementations',a/'implementations','staged_implementations')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('group',choices=['weights','scene_assets','implementations','code_archive'])
    parser.add_argument('--install',action='store_true');parser.add_argument('--bind',action='store_true')
    args=parser.parse_args()
    lock=(O/(args.group+'.lock')).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if args.group=='weights':verify_weights(args.install,args.bind)
    elif args.group=='code_archive':stage_code_archive()
    else:verify_group(args.group)
