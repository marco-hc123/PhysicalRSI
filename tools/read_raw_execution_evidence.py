"""Read/verify frozen evidence bytes. Does not execute evidence or call APIs."""
from pathlib import Path
import argparse,csv,gzip,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
INDEXES=['provenance/raw-execution-source-index-20261102.csv.gz',
         'provenance/lab-readonly-source-index-20261102.csv',
         'provenance/auxiliary-evidence-index-20261102.csv']
def rows():
    for name in INDEXES:
        opener=gzip.open if name.endswith('.gz') else open
        with opener(ROOT/name,'rt',encoding='utf-8-sig',newline='') as f:
            yield from csv.DictReader(f)
def fragments():
    base=ROOT/'experiments/raw_execution_archive'
    for p in sorted(base.glob('*records-*.jsonl.gz')):
        with gzip.open(p,'rt',encoding='utf-8') as f:
            for line in f:yield json.loads(line)
def objects():
    current=None;parts=[];count=0;size=0
    for r in fragments():
        if r['sha256']!=current:
            if current is not None:
                assert len(parts)==count
                data=''.join(parts).encode('utf-8')
                assert len(data)==size and hashlib.sha256(data).hexdigest()==current
                yield current,data
            current=r['sha256'];parts=[];count=r['parts'];size=r['bytes']
        assert r['part']==len(parts)+1 and r['parts']==count and r['bytes']==size
        parts.append(r['utf8'])
    if current is not None:
        assert len(parts)==count
        data=''.join(parts).encode('utf-8')
        assert len(data)==size and hashlib.sha256(data).hexdigest()==current
        yield current,data
def verify():
    restored={}
    for h,d in objects():
        assert h not in restored,h
        restored[h]=len(d)
    aliases=0;aux={};kinds={}
    for r in rows():
        kind=r['publication_kind'];kinds[kind]=kinds.get(kind,0)+1
        if kind=='raw_text_object':assert restored[r['sha256']]==int(r['bytes']);aliases+=1
        elif kind=='exact_auxiliary_file':
            p=ROOT/r['repository_path'];d=p.read_bytes()
            assert len(d)==int(r['bytes']) and hashlib.sha256(d).hexdigest()==r['sha256']
            aux[r['sha256']]=len(d)
    return {'status':'passed','unique_new_raw_text_objects':len(restored),
            'restored_original_bytes':sum(restored.values()),'raw_text_source_aliases':aliases,
            'auxiliary_unique_objects':len(aux),'source_kinds':kinds,
            'qualification':'Aliases/objects are evidence units, not experiment or API counts; existing derivatives are not claimed to be original bytes.'}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('query',nargs='?');p.add_argument('--search',action='store_true')
    p.add_argument('--verify',action='store_true');p.add_argument('--limit',type=int,default=30)
    args=p.parse_args()
    if args.verify:print(json.dumps(verify(),ensure_ascii=False));return
    if not args.query:p.error('Provide an exact source_path, --search query or --verify')
    matches=[r for r in rows() if (args.query in r['source_path'] if args.search else args.query==r['source_path'])]
    if args.search or len(matches)!=1:
        for r in matches[:args.limit]:print(r['source_path']+'\t'+r['publication_kind']+'\t'+r['repository_path'])
        print('matches='+str(len(matches))+'; aliases are not episodes',file=sys.stderr)
        if not matches:raise SystemExit(1)
        return
    r=matches[0];kind=r['publication_kind'];data=None
    if kind=='existing_redacted_derivative':
        raise SystemExit('Published redacted derivative: '+r['repository_path']+'; original is intentionally not restored.')
    if kind=='raw_text_object':
        for h,d in objects():
            if h==r['sha256']:data=d;break
    elif kind in ['exact_auxiliary_file','existing_exact_file']:data=(ROOT/r['repository_path']).read_bytes()
    elif kind=='existing_archived_object':
        import read_research_evidence
        data=read_research_evidence.corpus().get(r['sha256'])
        if data is None:
            for old in read_research_evidence.rows():
                if old['sha256']==r['sha256'] and old['publication_kind']!='external_only':
                    data=read_research_evidence.read(old);break
    if data is None:raise SystemExit('Source is indexed but no restorable payload was found')
    assert len(data)==int(r['bytes']) and hashlib.sha256(data).hexdigest()==r['sha256']
    sys.stdout.buffer.write(data)
if __name__=='__main__':main()
