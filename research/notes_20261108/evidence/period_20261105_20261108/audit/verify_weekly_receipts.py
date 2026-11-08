"""Read-only scientific recomputation; output only in this audit directory."""
import ast, collections, datetime, hashlib, json
from pathlib import Path

B = Path('/home/marco/workspace/PhysicalRSI/current/result/research_week_20261102_20261108')
R = B / 'evidence/result'
O = Path(__file__).resolve().parent
rows = json.loads((B/'derived/native_episodes_all.json').read_text())
counts = collections.Counter()
source_hashes = {}
identities = set()
for row in rows:
    name = row['source'].split('#')[0]
    p = R/name
    raw_bytes = p.read_bytes()
    d = json.loads(raw_bytes)
    sha = hashlib.sha256(raw_bytes).hexdigest()
    source_hashes[name] = sha
    if row['receipt_sha256']:
        assert sha == row['receipt_sha256'], name
    if row['batch'] == 24:
        detail = d['details'][str(row['layout_key'])]
        score, success = detail['score'], detail['success']
    elif row['receipt_sha256']:
        assert d['natural_terminal'] and d['native_exit_code'] == 0, name
        score, success = d['episode_score'], d['success']
    else:
        detail = next(v for v in d['details'].values()
                      if v['layout_id'] == row['source_layout_id'])
        score, success = detail['score'], detail['success']
    assert abs(100*float(score)-row['score_100']) < 1e-8, name
    assert success == row['success'], name
    ident = (row['batch'], row['phase'], row['task'], row['condition'], row['layout_key'])
    assert ident not in identities, ident
    identities.add(ident)
    counts[row['batch']] += 1

api_rows = json.loads((B/'derived/api_requests.json').read_text())
api_counts = collections.Counter()
api_tokens = collections.Counter()
api_cost = collections.Counter()
ledger43 = next(R.glob('43*/**/generation-snapshots/general_pickup/ledger.json'))
ledger_cache = {}
for row in api_rows:
    p = ledger43 if row['batch'] == 43 else R/row['source']
    if p not in ledger_cache:
        raw_bytes = p.read_bytes()
        source_hashes[str(p.relative_to(R))] = hashlib.sha256(raw_bytes).hexdigest()
        d = json.loads(raw_bytes)
        ledger_cache[p] = d['attempts'] if isinstance(d, dict) else d
    entry = next(x for x in ledger_cache[p]
                 if x.get('id', x.get('request_id')) == row['id'])
    usage = entry['usage']
    inp, out = usage['prompt_tokens'], usage['completion_tokens']
    details = usage.get('prompt_tokens_details') or {}
    cached, write = details.get('cached_tokens', 0), details.get('cache_write_tokens', 0)
    reasoning = (usage.get('completion_tokens_details') or {}).get('reasoning_tokens', 0)
    assert inp+out == usage['total_tokens'] == row['total_tokens']
    assert inp == row['input_tokens'] and out == row['output_tokens']
    assert cached == row['cached_input_subset'] and write == row['cache_write_input_subset']
    assert 0 <= cached+write <= inp and 0 <= reasoning <= out
    assert entry['http_status'] == row['http_status'] == 200
    cost = ((inp-cached-write)*2 + cached*.1 + write*2.5 + out*10)/1e6
    assert abs(cost-row['recomputed_estimate_usd']) < 1e-10
    api_counts[row['batch']] += 1
    api_tokens[row['batch']] += inp+out
    api_cost[row['batch']] += cost

terminal43 = next(R.glob('43*/**/FINAL_SUMMARY.json'))
final43 = json.loads(terminal43.read_text())
assert final43['actual_native_episodes'] == counts[43] == 89
assert final43['formal_native_episodes'] == 88
interruptions = final43['runtime_interruptions']
assert len(interruptions) == 2
assert all(x['score'] is None and x['success'] is None and not x['natural_terminal']
           for x in interruptions)
assert {x['native_action_count'] for x in interruptions} == {214, 31}
def metric(batch, phase, condition, task=None):
    chosen = [x for x in rows if x['batch']==batch and x['phase']==phase
              and x['condition']==condition and (task is None or x['task']==task)]
    assert chosen
    return sum(x['success'] for x in chosen), sum(x['score_100'] for x in chosen)/len(chosen)

root42 = next(R.glob('42*/20261107_v1/native-validation'))
admit42 = json.loads((root42/'admission-contract-audit.json').read_text())['candidate_rows']
assert len(admit42)==8
for item in admit42:
    p=root42/'candidates'/item['candidate']/'candidate.py'
    data=p.read_bytes();sha=hashlib.sha256(data).hexdigest()
    assert sha==item['source_sha256']
    source_hashes[str(p.relative_to(R))]=sha
    has_nonlocal=any(isinstance(x, ast.Nonlocal) for x in ast.walk(ast.parse(data)))
    assert item['admitted']==(not has_nonlocal)
    executed=[x for x in rows if x['batch']==42 and x['condition']==item['candidate']]
    assert len(executed)==(5 if item['admitted'] else 0)
selection42=json.loads((root42/'selection-final.json').read_text())
parent42=metric(42,'parent','fixed_parent')
assert parent42==(0,3.0)
for budget in (1,5):
    assert all(metric(42,'sampling',f'sample_{i:02}')<=parent42 for i in range(1,budget+1))
    assert selection42['round1_selection'][f'budget{budget}']['selected']=='fixed_parent'
assert metric(42,'round2','round2_01')==parent42
assert selection42['round2_selection']['selected']=='fixed_parent'
assert not selection42['heldout_seen'] and len(selection42['unique_entries'])==3

root43=terminal43.parent
selection_results=[]
for task in ('classify_objects','general_pickup'):
    admission=json.loads((root43/(task+'-candidates')/'native-preparation/candidate-audit.json').read_text())
    assert len(admission)==6
    for item in admission:
        assert item['admitted'] and item['native_admission']['accepted']
        p=root43/'candidates'/item['name']/'candidate.py'
        data=p.read_bytes();sha=hashlib.sha256(data).hexdigest()
        source_hashes[str(p.relative_to(R))]=sha
        assert sha==item['source_sha256']
        ledger=next(x for x in ledger_cache[ledger43] if x['id']==item['name'])
        assert ledger['source_sha256']==sha
        executed=[x for x in rows if x['batch']==43 and x['condition']==item['name']]
        assert len(executed)==5
        for x in executed:
            receipt=json.loads((R/x['source']).read_text())
            assert receipt['revision']==sha
    selection=json.loads((root43/'selection'/f'{task}.json').read_text())
    assert not selection['heldout_seen'] and len(selection['unique_entries'])==1
    parent=metric(43,task+'-parent','parent',task)
    for condition in ('basic','execution_feedback'):
        ms=[metric(43,task+'-candidates',f'{task}-{condition}-{i}',task) for i in range(1,4)]
        assert not any(m[1]>parent[1] and m[0]>=parent[0] for m in ms)
        assert selection['selected_views'][condition]=='parent'
    overlap=json.loads((root43/'layouts'/task/'heldout/overlap-audit.json').read_text())
    assert overlap['state']=='passed' and not overlap['missing_prior_references']
    fresh=set(overlap['new_geometry_sha256']);prior={x['geometry_sha256'] for x in overlap['sources']}
    assert len(fresh)==5 and fresh.isdisjoint(prior)
    selection_results.append(dict(task=task,parent_successes=parent[0],parent_mean_score_100=parent[1],
                                  retained_parent_in_both_conditions=True,
                                  heldout_scored=4,heldout_planned=5))
result = dict(state='passed', observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              source_scope='Existing verified local weekly package; freshness to be checked by primary agent on lab server',
              terminal_scored_executions_verified=len(rows), terminal_counts_by_batch=dict(sorted(counts.items())),
              nov6_through8_terminal_scored_executions=sum(v for k,v in counts.items() if k>=32),
              paid_requests_verified=len(api_rows), paid_requests_by_batch=dict(sorted(api_counts.items())),
              tokens_by_batch=dict(sorted(api_tokens.items())), historical_usage_estimate_by_batch=dict(sorted(api_cost.items())),
              tokens_total=sum(api_tokens.values()), historical_usage_estimate_total=sum(api_cost.values()),
              novel_nov6_through8_requests=sum(v for k,v in api_counts.items() if k>=32),
              nov8_scored_formal_executions=88, nov8_scored_preparation_smoke=1,
              nov8_unscored_interrupted_attempts=interruptions,
              unique_source_files_checked=len(source_hashes), source_hashes=source_hashes,
              batch42_generated_candidates=8,batch42_admitted_candidates=6,
              batch42_nonlocal_rejected_without_scores=2,
              batch42_search_choices_retain_parent=True,
              batch43_admitted_candidates=12,batch43_selection_recomputed=selection_results,
              limitations=['Counts are an execution ledger, not a pooled benchmark success rate.',
                           'No new model calls, policy execution, media decoding or remote source audit performed here.',
                           'Estimated fees use the recorded historical formula, not current pricing or provider invoices.'])
(O/'independent-recomputation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('source_hashes','nov8_unscored_interrupted_attempts')}, ensure_ascii=False))
