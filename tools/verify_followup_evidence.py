"""Independent offline reconciliation of archived requests, receipts and native results."""
from collections import defaultdict,Counter
from statistics import mean
import ast,hashlib,json,math
from read_followup_evidence import Evidence

def verify():
    e=Evidence();objects=e.corpus();source_checks={};api=[];campaigns=[];all_receipts=set()
    def read(p):
        data=e.read(p);source_checks[p]=hashlib.sha256(data).hexdigest();return data
    def j(p):return json.loads(read(p))
    def table(p):read(p);return e.table(p)
    for prefix,expected in [('result/29_system2_feedback_api/20261104_v1/',64674)]:
        group=[]
        for p in sorted(k for k in e.index if k.startswith(prefix+'responses/') and k.endswith('.json')):
            response=j(p);body=response['body'];u=body['usage'];assert u['prompt_tokens']+u['completion_tokens']==u['total_tokens']
            candidate=p.removeprefix(prefix+'responses/').removesuffix('.json')
            proposal=json.loads(body['choices'][0]['message']['content']);ast.parse(proposal['source'])
            source=read(prefix+'candidates/'+candidate+'/candidate.py').decode();assert source==proposal['source'] or source==proposal['source'].rstrip()+'\n'
            details=u.get('prompt_tokens_details',{});cached=details.get('cached_tokens',0);written=details.get('cache_write_tokens',0);assert 0<=cached+written<=u['prompt_tokens']
            cost=((u['prompt_tokens']-cached-written)*2+cached*.1+written*2.5+u['completion_tokens']*10)/1e6
            group.append({'candidate':candidate,'response_id':body['id'],'input':u['prompt_tokens'],'output':u['completion_tokens'],'total':u['total_tokens'],'historical_usage_estimate_usd':cost})
        assert len(group)==6 and len({r['response_id'] for r in group})==6
        assert sum(r['total'] for r in group)==expected
        api.append({'source_root':prefix,'calls':len(group),'input':sum(r['input'] for r in group),'output':sum(r['output'] for r in group),'total':sum(r['total'] for r in group),'historical_estimated_usd':sum(r['historical_usage_estimate_usd'] for r in group),'rows':group})
    bases=[('rgb35','result/31_system2_rgb_validation/20261105_v1/',35)]
    layout_hashes={};native_rows=[]
    for name,base,n in bases:
        rows=table(base+'analysis/episode-results.csv');assert len(rows)==n
        groups=defaultdict(list)
        for row in rows:
            rp=base+row['receipt'];assert rp not in all_receipts;all_receipts.add(rp)
            receipt=j(rp);raw=j(base+row['result_file']);idx=row['layout_id'];result=raw['details'][idx]
            assert receipt['state']=='completed' and receipt['natural_terminal'] and receipt['native_exit_code']==0
            assert receipt['episode_score']==result['score']==float(row['normalized_score'])
            assert receipt['success']==result['success']==(row['success']=='True') is False
            assert int(row['native_action_count'])==receipt['diagnostics']['action_count']==1100
            assert receipt['layout_sha256']==row['layout_sha256'];layout_hashes.setdefault(idx,receipt['layout_sha256']);assert layout_hashes[idx]==receipt['layout_sha256']
            assert int(row['paid_api_calls'])==0
            score=100*receipt['episode_score'];groups[row['condition']].append((int(idx),score))
            native_rows.append({'campaign':name,'condition':row['condition'],'layout':int(idx),'score_100':score,'success':False,'receipt':rp})
        cohorts=[]
        for name2,values in groups.items():
            values.sort();assert [i for i,s in values]==list(range(5))
            cohorts.append({'condition':name2,'n':5,'successes':0,'scores_100':[s for i,s in values],'mean_score_100':mean(s for i,s in values)})
        campaigns.append({'campaign':name,'n':n,'cohorts':cohorts})
    assert len(all_receipts)==35 and len(layout_hashes)==5
    assert sum(r['score_100']>0 for r in native_rows)==2
    assert {r['layout'] for r in native_rows if r['score_100']>0}=={4}

    base='result/31_system2_rgb_validation/20261105_v1/'
    protocol=j(base+'protocol/diagnostic-matrix-v1.json')
    for candidate in protocol['matrix']['saved_candidates']:
        data=read('result/29_system2_feedback_api/20261104_v1/candidates/'+candidate['name']+'/candidate.py')
        assert hashlib.sha256(data).hexdigest()==candidate['source_sha256']
    totals=defaultdict(Counter)
    for row in table(base+'analysis/actor-diagnostics.csv'):
        actor=j(base+row['process_record']);calls=sorted(actor['calls'],key=lambda x:x['request']['id']);approaches=[c for c in calls if c['request']['method']=='approach']
        def rejected(c):return bool((c.get('response') or {}).get('value',{}).get('primitive_error'))
        accepted=sum(bool(c.get('response')) and not rejected(c) for c in approaches);failed=sum(rejected(c) for c in approaches);incomplete=sum(not c.get('response') for c in approaches)
        assert accepted==int(row['accepted_approach_calls']) and failed==int(row['rejected_approach_calls']) and incomplete==int(row['incomplete_approach_calls'])
        first=bool(approaches and rejected(approaches[0]));assert first==(row['first_approach_rejected']=='True')
        totals[row['condition'].split('_')[0]].update(cases=1,accepted=accepted,rejected=failed,incomplete=incomplete,first_rejected=int(first))
    assert totals['baseline']['first_rejected']==12 and totals['augmented']['first_rejected']==0
    assert totals['baseline']['accepted']==9 and totals['augmented']['accepted']==50
    return {'state':'passed','scientific_cutoff':'2026-11-05T23:59:59+08:00','unique_raw_objects':len(objects),'source_paths_verified':len(source_checks),'source_sha256':source_checks,'api':api,'campaigns':campaigns,'native_cases':35,'native_successes':0,'partial_score_cases':2,'unique_exposed_layouts':5,'distinct_layouts_with_partial_score':1,'actor_totals':{k:dict(v) for k,v in totals.items()},'new_experiments_from_verification':0,'new_model_requests_from_verification':0}
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
