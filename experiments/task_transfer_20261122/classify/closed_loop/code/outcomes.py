import csv
from collections import Counter
from pathlib import Path
from statistics import mean
from scene_setup import load,save

def metrics(w):
    funnel=load(w/'turn_funnel.json')
    turns=funnel['turns']
    retreats=[t['retreat'] for t in turns if t.get('retreat')]
    scenes=sorted(w.glob('scene-*.json'),key=lambda p:int(p.stem.split('-')[1]))
    categories={c for p in w.glob('assignments-*.json') for c in load(p)['added']}
    def held(t):
        after=t.get('ee_after_lift',0)
        return (after>=.05 and after>=.5*t.get('ee_before_lift',0)) or (t['category']=='pen' and after>=.015)
    return dict(attempted_items=len(turns),held_after_lift_items=sum(held(t) for t in turns),
        vetoed_empty_transports=sum(t['vetoed'] for t in turns),deposited_items=sum(t['deposited'] for t in turns),
        retained_at_basket_items=sum(t['deposited'] and t.get('ee_at_basket',0)>=.015 for t in turns),
        retained_at_020=sum(t['deposited'] and t.get('ee_at_basket',0)>=.020 for t in turns),
        retreat_attempted_count=len(retreats),retreat_ok_count=sum(r['ok'] for r in retreats),
        final_visible_baskets=sum(k.startswith('basket_') for k in load(scenes[-1])['objects']) if scenes else None,
        dynamic_assigned_categories=len(categories))

def summarize(rows):
    valid=[x for x in rows if x['status']=='valid']
    return dict(valid=len(valid),mean_score_100=mean(x['score_100'] for x in valid) if valid else 0,
        native_success_count=sum(x['success'] for x in valid),positive_score_count=sum(x['positive'] for x in valid),
        **{k:sum(x[k] for x in valid) for k in ('attempted_items','held_after_lift_items','vetoed_empty_transports','deposited_items','retained_at_basket_items','retained_at_020','retreat_ok_count','retreat_attempted_count','dynamic_assigned_categories')})

def selection(rows):
    ranking=[]
    for v,cost in [('C6',1),('C7',2)]:
        st=summarize([r for r in rows if r['phase']=='A' and r['variant']==v])
        key=[st['mean_score_100'],st['native_success_count'],st['positive_score_count'],st['retained_at_basket_items'],st['held_after_lift_items'],st['retreat_ok_count'],-cost]
        ranking.append(dict(variant=v,key=key,summary=st))
    ranking.sort(key=lambda r:r['key'],reverse=True)
    return dict(winner=ranking[0]['variant'],ranking=ranking)

def write_csv(path,rows):
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)

def publish(root,rows,selected,final=False):
    screen=[r for r in rows if r['phase']=='A']
    assert len(screen)==32
    write_csv(root/'screening-comparison.csv',screen)
    if not final:
        return
    winner=selected['winner']
    pairs=[]
    for index in range(20):
        row={'index':index,'split':'screening' if index<5 else 'heldout'}
        for v in ('C0',winner):
            case,=[r for r in rows if r['split']=='formal' and r['index']==index and r['variant']==v]
            row['layout_sha256']=case['layout_sha256']
            for k in ('status','score_100','positive','success','retained_at_basket_items','retreat_ok_count','native_receipt'):
                row[v+'_'+k]=case.get(k)
        a,b=row[winner+'_score_100'],row['C0_score_100']
        row['difference']=None if None in (a,b) else a-b
        pairs.append(row)
    write_csv(root/'formal-20-paired.csv',pairs)
    lines=['# classify_objects 闭环控制实验','',
           '| 筛选变体 | 有效布局 | 平均原生分 | 正分 | 完整成功 | 起抬持物 / 尝试 | 空爪拦截 | 到筐放爪 | 到筐开度 ≥0.015 / ≥0.020 | 成功退臂 / 尝试 |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for v in ('C0','C3','C6','C7'):
        s=summarize([r for r in screen if r['variant']==v])
        lines.append(f"| {v} | {s['valid']} | {s['mean_score_100']:.2f} | {s['positive_score_count']} | {s['native_success_count']} | {s['held_after_lift_items']}/{s['attempted_items']} | {s['vetoed_empty_transports']} | {s['deposited_items']} | {s['retained_at_basket_items']}/{s['retained_at_020']} | {s['retreat_ok_count']}/{s['retreat_attempted_count']} |")
    lines.extend(['',f'{winner} 按预设的七项排序晋级。',''])
    for label,group in [('筛选正式布局',pairs[:5]),('留出布局',pairs[5:]),('全部正式布局',pairs)]:
        valid=[r for r in group if r['difference'] is not None]
        if valid:
            diffs=[r['difference'] for r in valid]
            lines.append(f"{label}共 {len(valid)}/{len(group)} 对有效。C0 平均 {mean(r['C0_score_100'] for r in valid):.2f} 分，{winner} 平均 {mean(r[winner+'_score_100'] for r in valid):.2f} 分，差 {mean(diffs):+.2f} 分。逐布局提升 / 持平 / 降低为 {sum(x>0 for x in diffs)}/{sum(x==0 for x in diffs)}/{sum(x<0 for x in diffs)}。")
    lines+=['','每个变体每布局一次。漏斗使用公开夹爪开度作为持物代理，终局成绩以原生评分器为准。两组策略差异各包含多项预设修改，各项修改的独立贡献无法由这组对照拆分。']
    (root/'跨任务迁移实验汇总.md').write_text('\n'.join(lines)+'\n')
