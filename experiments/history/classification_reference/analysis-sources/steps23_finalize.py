"""Summarize retained native evidence and verify a cloud-only archive."""
from datetime import datetime,timezone
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile

SUITE=Path(sys.argv[1]); ONLY2='--step2-only' in sys.argv
ROOT=Path('/mnt/data/physical-RSI'); FREEZE=ROOT/'result/23_protocol_freeze_20261029T132917Z'
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
protocol=read(SUITE/'protocol.json');rows=[];truth_rows=[];memory_checks=[]
for job in protocol['jobs']:
    if ONLY2 and job['step']!=2:continue
    out=SUITE/job['name'];assert read(out/'status.json')['complete']
    native=lines(out/'native-events.jsonl');policy=lines(out/'policy-events.jsonl')
    result=read(out/'native-result.json') if (out/'native-result.json').exists() else {}
    metas=[read(p) for p in sorted((out/'api').glob('*metadata.json'))]
    for layout in job['layouts']:
        ev=[e for e in native if e['layout']==layout]
        reset=next(e for e in ev if e['kind']=='reset_start')
        terminal=[e for e in ev if e['kind'] in ['episode_end','episode_error','reset_error']];assert len(terminal)==1
        end=terminal[0];idx=end['episode_index']
        calls=[m for m in metas if m['episode_index']==idx]
        usage=[m.get('usage') for m in calls]
        known=all(u is not None for u in usage)
        tokens=sum(u['total_tokens'] for u in usage) if known else None
        details=[v for v in result.get('details',{}).values() if v['layout_id']==layout]
        detail=details[0] if details else {}
        row=dict(step=job['step'],job=job['name'],task=job['task'],route=job['route'],layout=layout,
            native_complete=end['kind']=='episode_end',success=bool(end.get('success',[False])[0]) if end['kind']=='episode_end' else False,
            partial_score=detail.get('score'),native_steps=end.get('steps',[0])[0],
            physical_seconds=end.get('steps',[0])[0]*0.04,
            reset_to_result_seconds=end['monotonic']-reset['monotonic'],
            logical_model_calls=sum(e['kind']=='logical_plan_start' and e['episode_index']==idx for e in policy),
            http_attempts=len(calls),total_tokens=tokens,
            input_tokens=sum(u.get('prompt_tokens',0) for u in usage) if known else None,
            output_tokens=sum(u.get('completion_tokens',0) for u in usage) if known else None,
            error_type=end.get('error_type'),purpose='infrastructure_diagnostics' if job['step']==2 else 'frozen_skill_execution')
        rows.append(row)
    if job['step']==2:
        truth=lines(out/'ground-truth.jsonl');assert not any('error' in t for t in truth)
        for terminal in [t for t in truth if t['phase']=='terminal']:
            objects=terminal['objects']; categories=sorted({o['category'] for o in objects})
            category_bins={c:[b for b in range(3) if all(o['in_basket'][b]>0.99 and o['below_basket_top'][b]>0.99 for o in objects if o['category']==c)] for c in categories}
            matching=all(c in category_bins[c] for c in categories)
            permutation=any(len({a,b,c})==3 for a in category_bins.get(0,[]) for b in category_bins.get(1,[]) for c in category_bins.get(2,[]))
            truth_rows.append(dict(job=job['name'],task=job['task'],layout=terminal['layout'],object_count=len(objects),
                objects_outside_all_baskets=sum(not any(v>.99 for v in o['in_basket']) for o in objects),
                category_bins=category_bins,language_matching=matching,category_permutation=permutation,
                home=terminal['home'],grippers_open=terminal['grippers_open'],
                observer_calls=sum(t['layout']==terminal['layout'] for t in truth),
                observer_seconds=sum(t['observer_seconds'] for t in truth if t['layout']==terminal['layout'])))
    memory_files=list((out/'runtime').glob('*/memory/*.json'))
    for path in memory_files:
        value=read(path)
        digest=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
        assert digest==path.stem, 'Memory content changed: '+str(path)
    resets=[e for e in policy if e['kind']=='runtime_reset_end']
    assert all(not e['sessions'] and not e['queue_sizes'] for e in resets)
    histories=[e for e in policy if e['kind']=='sparse_history_materialize']
    empty_starts=[e for e in histories if e['step']==0]
    assert all(all(v==0 for v in e['masks'].values()) for e in empty_starts)
    history_resets=[e for e in policy if e['kind']=='sparse_history_reset']
    assert all(not e['after'] for e in history_resets if e['session']=='None')
    memory_checks.append(dict(job=job['name'],verified_snapshots=len(memory_files),runtime_resets=len(resets),
        immutable_read_records=sum(e['kind']=='immutable_memory_read' for e in policy),
        sparse_materialize_records=len(histories),empty_history_episode_starts=len(empty_starts),
        sparse_history_has_real_past=any(any(v>0 for v in e['masks'].values()) for e in histories),
        sparse_resets=len(history_resets),passed=True))

write(SUITE/'step2-native-diagnosis.json',dict(complete=True,new_native_episodes=5,truth=truth_rows,
    conclusions=['Native truth logged on five fixed released-code diagnostic episodes.',
        'Category sorting permits category-to-basket permutation; language sorting requires the instructed mapping.',
        'Object poses and pure native predicates are diagnostics only; repeated samples are not independent trials.',
        'No causal repair or proof of numerical equivalence to the authors environment.']))
if ONLY2:
    print(json.dumps(dict(step2_complete=True,episodes=len(rows),successes=sum(r['success'] for r in rows))))
    sys.exit(0)
assert len(rows)==45
with (SUITE/'episode-metrics.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
write(SUITE/'memory-validation.json',dict(complete=True,checks=memory_checks,
    qualification='Runtime plumbing, immutable binding and causal-history lifecycle verified; no memory causal-performance claim.'))
groups=[]
for job in protocol['jobs']:
    batch=[r for r in rows if r['job']==job['name']]
    status=read(SUITE/job['name']/'status.json')
    groups.append(dict(job=job['name'],task=job['task'],route=job['route'],step=job['step'],
        episodes=len(batch),native_complete=sum(r['native_complete'] for r in batch),successes=sum(r['success'] for r in batch),
        http_attempts=sum(r['http_attempts'] for r in batch),logical_model_calls=sum(r['logical_model_calls'] for r in batch),
        total_tokens=sum(r['total_tokens'] for r in batch) if all(r['total_tokens'] is not None for r in batch) else None,
        group_wrapper_seconds=status['finished_monotonic']-status['started_monotonic']))
write(SUITE/'results-summary.json',dict(complete=True,utc=datetime.now(timezone.utc).isoformat(),groups=groups,
    episodes=45,diagnostic_episodes=5,reference_episodes=40,
    next_step=4,next_step_started=False,raw_retention='cloud_only'))
report=['第2、3步服务器实验结果','',
    '本轮保持第一步的源码、模型、权重、奖励与1100步上限。第2步5个诊断回合，第3步40个参考回合；普通失败均保留。',
    '诊断真值只写日志，未进入策略。参考场景为此前登记的两个任务各5–9号，不能再当System2新验证或最终测试。','',
    '任务 / 路线 / 原生执行 / 完整成功 / 逻辑模型调用 / HTTP / 总Token']
for g in groups:
    report.append(f"{g['job']} / {g['native_complete']}/{g['episodes']} / {g['successes']}/{g['episodes']} / {g['logical_model_calls']} / {g['http_attempts']} / {g['total_tokens']}")
report += ['', '记忆检查：不可变快照内容哈希、执行绑定、回合后队列/会话清空、稀疏历史首帧无虚构历史、后续真实历史与复位均单列。',
    '两种VLA的权重和架构不同，此对照不能独立归因于“有无记忆”。固定路线无高层API，不代表推理/训练成本为零。',
    '本轮计时含观察器开销，且每路线组内复用进程；不与此前冷启动数字混算，更不能推出跨项目速度倍率。',
    '项目A未公开的API次数和端到端时间仍未知。System2及步骤4以后未启动。']
(SUITE/'第二三步实验结果.txt').write_text('\n'.join(report)+'\n')
videos=[]
for p in sorted(SUITE.glob('*/videos/*.mp4')):
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=nb_read_frames','-of','json',str(p)],text=True))
    n=int(info['streams'][0]['nb_read_frames']);assert n>0
    videos.append(dict(path=str(p.relative_to(SUITE)),frames=n,bytes=p.stat().st_size))
write(SUITE/'video-verification.json',dict(complete=True,videos=videos,count=len(videos),frames=sum(v['frames'] for v in videos)))
for path,expected in protocol['source_hashes'].items():assert sha(Path(path))==expected
secret=read(Path.home()/'.config/physicalrsi/agent.json')['api_key'].encode()
for p in SUITE.rglob('*'):
    if p.is_file() and p.suffix in {'.json','.jsonl','.txt','.csv','.py','.log'}:
        assert secret not in p.read_bytes(),'Credential found: '+str(p)
write(SUITE/'final-verification.json',dict(complete=True,source_pins_match=True,credential_matches=0,
    memory_checks_pass=True,native_episodes=sum(r['native_complete'] for r in rows),
    counted_planner_failures=sum(not r['native_complete'] for r in rows),
    http_attempts=sum(r['http_attempts'] for r in rows),
    archive_local_download=False))
exclude={'controller-status.json','controller.log','controller.lock'}
files=[p for p in sorted(SUITE.rglob('*')) if p.is_file() and p.name not in exclude and not p.name.endswith('.tmp')]
manifest=[dict(path=str(p.relative_to(SUITE)),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
write(SUITE/'archive-manifest.json',manifest)
archive=SUITE.with_suffix('.tar.gz');assert not archive.exists()
with tarfile.open(archive,'w:gz') as t:
    for p in files+[SUITE/'archive-manifest.json']:t.add(p,arcname=str(p.relative_to(SUITE)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
    for row in manifest:
        h=hashlib.sha256();f=t.extractfile(row['path'])
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        assert h.hexdigest()==row['sha256']
write(SUITE.with_name(SUITE.name+'-archive-verification.json'),dict(complete=True,archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),manifest_files=len(manifest),local_download=False))
print(json.dumps(dict(complete=True,episodes=45,archive=str(archive),groups=groups)))
