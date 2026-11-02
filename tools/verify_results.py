"""Offline archive verification. No network, model requests, or simulation."""
from pathlib import Path
from collections import defaultdict
from statistics import mean
import csv, hashlib, json, math

ROOT=Path(__file__).resolve().parents[1]
def read_csv(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def read_json(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def close(a,b):return math.isclose(float(a),float(b),rel_tol=1e-9,abs_tol=1e-6)
def true(value):return str(value).lower()=='true'

def verify_sources():
    rows=read_csv('provenance/SOURCES.csv')
    assert rows and len({r['path'] for r in rows})==len(rows)
    for row in rows:
        p=ROOT/row['path'];data=p.read_bytes()
        assert hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
        assert len(data)==int(row['bytes']),row['path']
    return len(rows)

def verify_system1():
    root='experiments/system1_gpt/'
    episodes=read_csv(root+'episode-results.csv')
    summary=read_csv(root+'group-results.csv')
    groups=defaultdict(list)
    for r in episodes:
        groups[r['condition'],r['task']].append(r)
        assert close(float(r['input_tokens'])+float(r['output_tokens']),r['total_tokens'])
        assert close(float(r['input_tokens'])-float(r['cached_input_tokens'])+float(r['output_tokens']),r['uncached_metric'])
        assert float(r['cached_input_tokens'])<=float(r['input_tokens'])
    assert len(groups)==4 and len(episodes)==20
    fields={'score':'score','mean_input':'input_tokens','mean_output':'output_tokens',
            'mean_total':'total_tokens','mean_cached_input':'cached_input_tokens',
            'mean_uncached_metric':'uncached_metric'}
    for r in summary:
        rows=groups[r['condition'],r['task']]
        assert len(rows)==int(r['episodes'])==5
        assert sum(true(x['success']) for x in rows)==int(r['successes'])
        for aggregate,detail in fields.items():
            assert close(mean(float(x[detail]) for x in rows),r[aggregate]),(r['task'],aggregate)
        assert sum(int(x['actual_http_attempts']) for x in rows)==int(r['total_http_attempts'])
    for task in {t for _,t in groups}:
        q={r['layout']:r for r in groups['qwen_reference',task]}
        g={r['layout']:r for r in groups['gpt61sol',task]}
        assert set(q)==set(g)=={'5','6','7','8','9'}
        for layout in q:
            assert q[layout]['composition']==g[layout]['composition']
            assert json.loads(q[layout]['operations'])==json.loads(g[layout]['operations'])
    gpt=[r for r in episodes if r['condition']=='gpt61sol']
    assert sum(int(r['actual_http_attempts']) for r in gpt)==10
    return {'episodes_including_historical_reference':len(episodes),'new_gpt_episodes':len(gpt),'new_formal_http_requests':10,'matched_skill_selections':10}

def verify_system2():
    root='experiments/system2_gpt/'
    all_rows=read_csv(root+'episode-results.csv');groups=defaultdict(list)
    rows=[r for r in all_rows if r['state']=='completed']
    interrupted=[r for r in all_rows if r['state']=='interrupted_power_loss']
    assert len(all_rows)==11 and len(rows)==10 and len(interrupted)==1
    assert interrupted[0]['score']=='' and interrupted[0]['success']==''
    for r in rows:groups[r['condition']].append(r)
    assert set(groups)=={'parent','gpt_candidate'}
    for condition,rs in groups.items():
        assert len(rs)==5
        assert all(r['state']=='completed' for r in rs)
        assert not any(true(r['success']) for r in rs)
        assert close(mean(float(r['score']) for r in rs),0)
    parent={r['layout_sha256'] for r in groups['parent']}
    candidate={r['layout_sha256'] for r in groups['gpt_candidate']}
    assert len(parent)==5 and parent==candidate
    selection=read_json(root+'round/selection.json')['output']
    assert selection['decision']=='retain_parent' and selection['survivor_id']=='initial'
    usage=read_json(root+'proposal-api/call-0001/response.json')['usage']
    assert int(usage['prompt_tokens'])+int(usage['completion_tokens'])==int(usage['total_tokens'])==5476
    receipts=ROOT/root/'native-receipts'
    for r in rows:
        # The portable archive uses batch-N; source SHA remains independently checked.
        matches=[p for p in receipts.glob('batch-*/*.json') if hashlib.sha256(p.read_bytes()).hexdigest()==r['receipt_sha256']]
        assert len(matches)==1,('native receipt',r['index'],r['condition'])
    return {'completed_parent':5,'completed_candidate':5,'infrastructure_interruptions_unknown_score':1,'successes':0,'mean_score':0,'selection':'retain_parent','candidate_generation_total_tokens':5476}

def main():
    result={'source_files_verified':verify_sources(),'system1':verify_system1(),'system2':verify_system2(),
            'new_model_calls':0,'new_native_episodes':0,'status':'passed'}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
