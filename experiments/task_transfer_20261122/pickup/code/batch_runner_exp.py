import csv,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
from batch_remaining_v2 import launcher
from formal_queue import D,read,save
from batch_device import assert_owned
SCREEN=[('development',i) for i in range(3)]+[('formal',i) for i in [7,3,13,18,0]]
EXTRA=[('formal',i) for i in range(20) if ('formal',i) not in SCREEN]
variants=read(D/'variants.json')
manifest=read(D/'verified-case-manifest.json')
python=D.parents[1]/'envs/policy/bin/python'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen_files(script):
    paths=[*D.glob('*.py'),*D.glob('*.txt'),*D.glob('*.md'),D/'variants.json',D/'verified-case-manifest.json',D/'asset-manifest-v2.json',D/'phase0/f8-review.json',D/'phase0/unseen_manifest.json',script,*script.parent.glob('*.txt'),script.parent/'simulator_v5.py']
    paths += [Path(r['path']) for bucket in ('development','formal') for r in manifest[bucket]]
    return {str(p):digest(p) for p in paths if p.name!='扩展探索汇总.md'}
def csvout(name,rows):
    if not rows:return
    with (D/name).open('w') as h:
        w=csv.DictWriter(h,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
def rank(rows,v):
    valid=[r for r in rows if r['v']==v['id'] and 'success' in r]
    return [sum(r['success'] for r in valid),sum(r['auto_held'] for r in valid),sum(r['closed'] for r in valid),sum(r['tcp_rise_cm']>=10 for r in valid),-v['complexity']]
def run(g,status):
    assert read(D/'phase0/gpu-qualification.json')['layouts']==23
    assert not read(D/'phase0/unseen_manifest.json')['qualified']
    script=launcher(g)
    freeze=frozen_files(script)
    save('freeze.json',dict(files=freeze,retry='R1b',reason='frozen bridge supplies RGB-D at step zero only',gpu_preparation_approved=True,selection=['native success','auto held','closed','tcp rise >=10cm','lower complexity']))
    logs=D/'logs';logs.mkdir(exist_ok=True)
    rows=[];stage_a=[];deadline=float(os.environ['BATCH_DEADLINE'])
    def episode(phase,v,split,i):
        vid=v['id']
        row=dict(phase=phase,v=vid,split=split,layout=i+1)
        prior=D/'runs'/phase/vid/split/str(i)
        first=1+max([int(p.name) for p in prior.glob('*') if p.name.isdigit()],default=0)
        for attempt in (first,first+1):
            assert freeze==frozen_files(script),'frozen file changed'
            assert_owned()
            label=f'{phase}/{vid}/{split}/{i}/{attempt}'
            dest=D/'runs'/label
            limit=min(600 if vid=='V7' else 420,int(deadline-time.time()))
            if limit<=0:raise TimeoutError('batch deadline reached')
            status('native_simulation',current=label,completed=len(rows),log=str(logs))
            env={**os.environ,'PICKUP_PHASE':phase,'PICKUP_VARIANT':vid,'PICKUP_RUN_SUBDIR':label,'PICKUP_TIME_LIMIT':str(limit)}
            began=time.time()
            with (logs/(label.replace('/','-')+'.log')).open('x') as log:
                result=subprocess.run([sys.executable,'-B',str(script),split,str(i),str(attempt)],env=env,stdout=log,stderr=subprocess.STDOUT)
            if result.returncode==0:
                row.update(json.loads(subprocess.check_output([str(python),'-B',str(D/'measures.py'),str(dest),manifest[split][i]['sha256']],text=True)),seconds=time.time()-began)
                if not rows:
                    for name in ('target.json','grasp_plan.json','preclose.json','holding-windows.json'):
                        assert (dest/name).is_file(),name
                    for n in ('cam_head','cam_left_wrist','cam_right_wrist'):
                        for tag in ('before','before-close','before-lift','after'):
                            assert (dest/(tag+'-'+n+'.png')).is_file(),(tag,n)
                break
            progress=read(dest/'episode_progress.json') if (dest/'episode_progress.json').exists() else {}
            if progress.get('step') not in ('reset','construct') or (dest/'obs-0.json').exists():
                raise RuntimeError('inspect technical failure '+label)
            if attempt==first+1:row.update(status='technical_missing',run=str(dest))
        rows.append(row);save('episode-index.json',rows)
        if len(rows)==1 and 'success' not in row:raise RuntimeError('first case lacks a verified native receipt')
        if sum(r.get('status')=='technical_missing' for r in rows)>=5:raise RuntimeError('five technical misses')
    for v in variants:
        for split,i in SCREEN:episode('phaseA',v,split,i)
    stage_a=list(rows);csvout('screening-scores.csv',stage_a)
    ordered=sorted(variants,key=lambda v:rank(stage_a,v),reverse=True)
    winners=ordered[:2]
    save('selection.json',dict(ranking=[(v['id'],rank(stage_a,v)) for v in ordered],top2=[v['id'] for v in winners]))
    old=read(D.parent/'48_pickup_step2_m1_20261120/development-paired.json')
    repro=[dict(layout=r['layout'],current=r.get('stop'),previous=old[r['layout']-1]['stop']) for r in stage_a if r['v']=='V0' and r['split']=='development']
    save('reproducibility_check.json',repro)
    for v in winners:
        for split,i in EXTRA:
            if deadline-time.time()<(600 if v['id']=='V7' else 420):break
            episode('phaseB',v,split,i)
    formal=[r for r in rows if r['split']=='formal' and r['v'] in {v['id'] for v in winners}]
    top=max(winners,key=lambda v:rank(formal,v))
    paired=[]
    for i,case in enumerate(manifest['formal']):
        p=dict(layout=i+1,screened=('formal',i) in SCREEN,original=100*case['original_score'])
        base=D.parent/'47_pickup_three_module_20261119/runs/formal'/str(i)
        ref,=[read(f) for f in base.glob('*/stage2.json') if read(f).get('status')=='passed']
        p['M0']=100*ref['native']['score']
        for v in winners:
            p[v['id']]=next((r.get('score_100') for r in formal if r['layout']==i+1 and r['v']==v['id']),None)
        paired.append(p)
    csvout('formal-paired.csv',paired)
    for idx in read(D/'phase0/f8-review.json')['accepted']:
        if top['perception']=='sam3' and deadline-time.time()>=600:episode('phaseC1',top,'formal',idx-1)
    report=['# 抓取扩展实验汇总','',f'有效终局 {sum("success" in r for r in rows)} 个。缺失成绩留空。V7 使用首帧 R1b。','', '## 筛选成绩（原生分换算为百分制）','','|变体|'+'|'.join(f'{s}/{i+1}' for s,i in SCREEN)+'|','|---|'+'---|'*len(SCREEN)]
    for v in variants:
        report.append('|'+v['id']+'|'+'|'.join(str(r.get('score_100','缺失')) for r in stage_a if r['v']==v['id'])+'|')
    report+=['','## 逐布局配对','','|比较|胜|平|负|有效配对|','|---|---|---|---|---|']
    for a,b in [(1,0),(2,1),(3,1),(4,2),(5,4),(6,5),(7,6),(8,2),(9,0)]:
        diffs=[]
        for s,i in SCREEN:
            lookup={r['v']:r['score_100'] for r in stage_a if r['split']==s and r['layout']==i+1 and 'success' in r}
            if {f'V{a}',f'V{b}'}<=lookup.keys():diffs.append(lookup[f'V{a}']-lookup[f'V{b}'])
        report.append(f'|V{a} 比 V{b}|{sum(x>0 for x in diffs)}|{diffs.count(0)}|{sum(x<0 for x in diffs)}|{len(diffs)}|')
    report+=['','## 正式布局','','|编号|参与筛选|原策略|M0|'+'|'.join(v['id'] for v in winners)+'|','|---|---|---|---|---|---|']+['|'+'|'.join('未执行' if x is None else str(x) for x in p.values())+'|' for p in paired]
    report+=['','## 专项','','|专项|结果|','|---|---|',f'|F8|{[(r["layout"],r.get("score_100")) for r in rows if r["phase"]=="phaseC1"]}；第一名 {top["id"]}|','|未见布局|0 个核实可用，跳过|','','20 个正式布局均已用于历史诊断。开度为辅助指标。']
    if any(r['current']!=r['previous'] for r in repro):report.insert(2,'V0 停止阶段与历史记录不完全一致。')
    (D/'扩展探索汇总.md').write_text('\n'.join(report)+'\n')
    hashes={}
    for r in rows:
        if 'receipt' not in r:continue
        folder=Path(r['run'])
        for f in [Path(r['receipt']),folder/'stage2.json',folder/'target.json',folder/'holding-windows.json',*folder.glob('*.png'),*folder.glob('preclose*.json')]:hashes[str(f.relative_to(D))]=digest(f)
    save('native-evidence-sha256.json',hashes)
