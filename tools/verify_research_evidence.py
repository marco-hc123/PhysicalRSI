"""Offline checks for the 2026-11-02 research evidence addition. Standard library only."""
from pathlib import Path
from collections import defaultdict
from statistics import mean
import csv, hashlib, json, math, runpy

ROOT=Path(__file__).resolve().parents[1]
def csv_rows(path):
    with (ROOT/path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def j(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def digest(data):return hashlib.sha256(data).hexdigest()
def eq(a,b):return math.isclose(float(a),float(b),abs_tol=1e-7,rel_tol=1e-10)
def truth(x):return str(x).lower()=='true'
def containers(group,stem):
    result={}
    for path in sorted((ROOT/'experiments/fixed_input_api'/group).glob(stem+'*.jsonl')):
        for line in path.read_text(encoding='utf-8').splitlines():
            item=json.loads(line);name=item['path'];raw=item['utf8'].encode('utf-8')
            assert name not in result,('duplicate JSONL member',name)
            assert len(raw)==item['bytes'] and digest(raw)==item['sha256'],name
            result[name]={'data':json.loads(item['utf8']),'raw':raw,'sha256':item['sha256']}
    assert result,('no containers',group,stem)
    return result
def verify_manifest():
    rows=csv_rows('provenance/ADDITIONS_20261102.csv')
    assert len({r['path'] for r in rows})==len(rows)
    for r in rows:
        data=(ROOT/r['path']).read_bytes()
        assert len(data)==int(r['bytes']) and digest(data)==r['sha256'],r['path']
    return len(rows)
def verify_api():
    a=csv_rows('experiments/fixed_input_api/api80/all_calls.csv')
    b=csv_rows('experiments/fixed_input_api/api120/calls.csv')
    assert len(a)==80 and len(b)==120
    assert len({r['provider_id'] for r in a+b})==200
    for r in a+b:
        assert eq(float(r['input_tokens'])+float(r['output_tokens']),r['total_tokens'])
        assert 0<=float(r['cached_input_tokens'])<=float(r['input_tokens'])
    a_wrapped=containers('api80','responses')
    a_requests=containers('api80','requests')
    b_raw=containers('api120','raw_responses')
    b_wrapped=containers('api120','responses')
    b_requests=containers('api120','requests')
    assert (len(a_wrapped),len(a_requests),len(b_raw),len(b_wrapped),len(b_requests))==(80,40,120,120,40)
    by_provider={r['data']['provider_id']:r['data'] for r in a_wrapped.values()}
    for r in a:
        w=by_provider[r['provider_id']]
        for key in ['input_tokens','output_tokens','total_tokens','cached_input_tokens']:
            assert eq(w[key],r[key]),('API80 usage',r['sequence'],key)
        assert truth(w['contract_valid'])==truth(r['contract_valid'])
    for r in b:
        name=r['id']+'.json'
        raw=b_raw['raw_responses/'+name]
        wrapper=b_wrapped['responses/'+name]['data']
        request=b_requests['inputs/requests/'+r['scene_id']+'__'+r['condition']+'.json']
        assert raw['sha256']==r['response_sha256']
        # calls.csv stores the transport serialization hash, not the pretty JSON file hash.
        assert digest(json.dumps(request['data']).encode())==r['request_sha256']==wrapper['request_sha256']
        assert digest(json.dumps(request['data'],ensure_ascii=False,sort_keys=True).encode())==wrapper['request_canonical_sha256']
        assert raw['data']['id']==r['provider_id']==wrapper['provider_id']
        usage=raw['data']['usage']
        for k,field in [('prompt_tokens','input_tokens'),('completion_tokens','output_tokens'),('total_tokens','total_tokens')]:
            assert eq(usage[k],r[field]) and eq(wrapper[field],r[field])
        assert truth(r['contract_valid']) and truth(r['label_agreement']) and int(r['http_status'])==200
    groups={c:[r for r in b if r['condition']==c] for c in ['projected','unprojected']}
    assert all(len(rs)==60 and len({r['scene_id'] for r in rs})==20 for rs in groups.values())
    reduction={k:100*(1-mean(float(r[k]) for r in groups['projected'])/mean(float(r[k]) for r in groups['unprojected'])) for k in ['input_tokens','total_tokens','elapsed_seconds']}
    expected={'input_tokens':67.30983004887507,'total_tokens':66.866936202206,'elapsed_seconds':31.651866720364218}
    for k in expected:assert eq(reduction[k],expected[k]),k
    return {'api80_calls':80,'api120_calls':120,'new_calls_in_this_publication':0,
            'api120_independent_synthetic_inputs':20,'api120_repetitions_per_condition':3,
            'jsonl_members_verified':len(a_wrapped)+len(a_requests)+len(b_raw)+len(b_wrapped)+len(b_requests),
            'api120_reduction_percent':reduction,'robot_episodes':0}
def verify_catalogue():
    rs=csv_rows('experiments/history/catalogue_ablation/cases.csv')
    assert len(rs)==30
    groups={c:[r for r in rs if r['condition']==c] for c in ['projected','unprojected']}
    results={}
    for c,rows in groups.items():
        assert len(rows)==15
        results[c]={'attempts':15,'native_completed':sum(truth(r['native_completed']) for r in rows),
                    'successes':sum(truth(r['success']) for r in rows),'input':sum(int(r['input_tokens']) for r in rows),
                    'total':sum(int(r['total_tokens']) for r in rows)}
    assert (results['projected']['native_completed'],results['unprojected']['native_completed'])==(15,14)
    assert (results['projected']['successes'],results['unprojected']['successes'])==(5,6)
    assert (results['projected']['input'],results['unprojected']['input'])==(173262,875052)
    assert (results['projected']['total'],results['unprojected']['total'])==(186568,888970)
    return results
def verify_media():
    videos=j('reports/evidence/media/selected-videos.json')
    frames=j('reports/evidence/media/selected-frames.json')
    assert len(videos)==len(frames)==3
    for r in videos:
        data=(ROOT/r['repository_path']).read_bytes()
        assert digest(data)==r['sha256'] and len(data)==int(r['bytes'])
    for r in frames:
        assert digest((ROOT/r['repository_path']).read_bytes())==r['frame_png_sha256']
        assert eq(float(r['frame_index'])/25,r['video_time_seconds'])
    all_videos=j('reports/evidence/media/all-videos.json')
    assert len(all_videos)==13
    for r in all_videos:
        data=(ROOT/r['repository_path']).read_bytes()
        assert digest(data)==r['sha256'] and len(data)==int(r['bytes'])
    return {'original_videos':13,'featured_videos':3,'terminal_frames':3,'random_sample':False,'new_GPT_execution_videos':0}
def verify_archive():
    helper=runpy.run_path(str(ROOT/'tools/read_research_evidence.py'))
    objects=helper['corpus']()
    coverage=j('provenance/research-coverage-20261102.json')
    index=csv_rows('provenance/research-source-index-20261102.csv')
    assert len(index)==coverage['source_paths_indexed']
    assert len(objects)==coverage['additional_unique_text_objects']
    verified_new_files=0
    for r in index:
        if r['publication_kind']=='lossless_corpus_object':
            assert digest(objects[r['sha256']])==r['sha256'] and len(objects[r['sha256']])==int(r['bytes'])
        if r['publication_kind']=='new_exact_file':
            helper['read'](r,objects);verified_new_files+=1
    return {'source_paths_indexed':len(index),'unique_lossless_text_objects':len(objects),
            'original_text_bytes':sum(map(len,objects.values())),'new_exact_source_paths_checked':verified_new_files,
            'external_sources_explicitly_listed':sum(r['publication_kind']=='external_only' for r in index),
            'scope':'Collected source packages and research notes; not all server bytes or all raw binary observations.'}
def main():
    result={'status':'passed','manifest_files_verified':verify_manifest(),'fixed_input_api':verify_api(),
            'native_catalogue_ablation':verify_catalogue(),'media':verify_media(),'research_archive':verify_archive(),
            'new_model_calls':0,'new_native_experiments':0}
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
