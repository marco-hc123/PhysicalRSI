"""Read a frozen research source by its indexed name; never executes archived code."""
from pathlib import Path
import argparse,csv,hashlib,json,sys,gzip
ROOT=Path(__file__).resolve().parents[1]
INDEX='provenance/research-source-index-20261102.csv'
def rows():
    with (ROOT/INDEX).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def digest(data):return hashlib.sha256(data).hexdigest()
def corpus():
    parts={};meta={}
    for f in sorted((ROOT/'experiments/evidence_archive').glob('records-*.jsonl*')):
        text=gzip.decompress(f.read_bytes()).decode('utf-8') if f.suffix=='.gz' else f.read_text(encoding='utf-8')
        for line in text.splitlines():
            r=json.loads(line);h=r['sha256'];p=parts.setdefault(h,{})
            assert r['part'] not in p,('duplicate object fragment',h,r['part'])
            p[r['part']]=r['utf8'];meta[h]=(r['parts'],r['bytes'])
    result={}
    for h,p in parts.items():
        count,size=meta[h];assert set(p)==set(range(1,count+1))
        data=''.join(p[i] for i in range(1,count+1)).encode('utf-8')
        assert len(data)==size and digest(data)==h,h
        result[h]=data
    return result
def read(row,objects=None):
    kind=row['publication_kind'];h=row['sha256']
    if kind=='external_only':raise ValueError('External archive only: '+row['reason'])
    if kind=='lossless_corpus_object':data=(corpus() if objects is None else objects)[h]
    elif kind=='lossless_jsonl_member':
        data=None
        for line in (ROOT/row['repository_path']).read_text(encoding='utf-8').splitlines():
            r=json.loads(line)
            if r['sha256']==h:data=r['utf8'].encode('utf-8');break
        assert data is not None,h
    else:data=(ROOT/row['repository_path']).read_bytes()
    assert len(data)==int(row['bytes']) and digest(data)==h,row['source_path']
    return data
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query',nargs='?');parser.add_argument('--search',action='store_true')
    parser.add_argument('--verify-objects',action='store_true')
    args=parser.parse_args()
    if args.verify_objects:
        objects=corpus();print(json.dumps({'unique_objects':len(objects),'original_bytes':sum(map(len,objects.values())),'status':'passed'}));return
    if not args.query:parser.error('Provide a source path or --search query or --verify-objects')
    matches=[r for r in rows() if (args.query in r['source_path'] if args.search else args.query==r['source_path'])]
    if args.search or len(matches)!=1:
        for r in matches:print(r['source_path']+'\t'+r['publication_kind']+'\t'+r['repository_path'])
        if not matches:raise SystemExit('No matching source')
        return
    try:data=read(matches[0])
    except ValueError as e:raise SystemExit(str(e))
    sys.stdout.buffer.write(data)
if __name__=='__main__':main()
