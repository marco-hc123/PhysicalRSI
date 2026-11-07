"""Read/hash-check frozen Nov4-5 research evidence. Never executes archived programs."""
from pathlib import Path
import argparse,csv,gzip,hashlib,io,json,sys
ROOT=Path(__file__).resolve().parents[1]
INDEX='provenance/followup-source-index-20261107.csv.gz'
COVERAGE='provenance/followup-coverage-20261107.json'
def digest(data):return hashlib.sha256(data).hexdigest()
def safe_path(name):
    p=(ROOT/name).resolve()
    if not p.is_relative_to(ROOT):raise ValueError('Path outside repository')
    return p
class Evidence:
    def __init__(self):
        with gzip.open(ROOT/INDEX,'rt',encoding='utf8',newline='') as f:self.rows=list(csv.DictReader(f))
        self.index={r['source_path']:r for r in self.rows}
        if len(self.index)!=len(self.rows):raise ValueError('Duplicate indexed source path')
        self.coverage=json.loads((ROOT/COVERAGE).read_text());self.objects=None
    def corpus(self):
        if self.objects is not None:return self.objects
        parts={};meta={}
        for s in self.coverage['shards']:
            data=safe_path(s['path']).read_bytes();assert digest(data)==s['sha256'] and len(data)==s['bytes']
            raw=gzip.decompress(data);assert len(raw)==s['decoded_bytes']
            for line in raw.splitlines():
                r=json.loads(line);h=r['sha256'];p=parts.setdefault(h,{})
                assert r['part'] not in p,(h,r['part'])
                assert h not in meta or meta[h]==(r['parts'],r['bytes'])
                p[r['part']]=r['utf8'];meta[h]=(r['parts'],r['bytes'])
        self.objects={}
        for h,p in parts.items():
            count,size=meta[h];assert set(p)==set(range(1,count+1))
            data=''.join(p[i] for i in range(1,count+1)).encode();assert len(data)==size and digest(data)==h
            self.objects[h]=data
        assert len(self.objects)==self.coverage['new_raw_text_objects']
        return self.objects
    def read(self,path):
        r=self.index[path];k=r['publication_kind']
        if k=='exact_file':data=safe_path(r['repository_path']).read_bytes()
        elif k=='lossless_text_object':data=self.corpus()[r['sha256']]
        else:raise ValueError('Not distributed as bytes: '+k+'; '+r['reason'])
        assert len(data)==int(r['bytes']) and digest(data)==r['sha256'],path
        return data
    def json(self,path):return json.loads(self.read(path))
    def table(self,path):return list(csv.DictReader(io.StringIO(self.read(path).decode('utf-8-sig'))))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('query',nargs='?');p.add_argument('--search',action='store_true');p.add_argument('--verify-objects',action='store_true');a=p.parse_args();e=Evidence()
    if a.verify_objects:
        o=e.corpus();print(json.dumps({'state':'passed','objects':len(o),'original_bytes':sum(map(len,o.values()))}));return
    if not a.query:p.error('Supply a source path, --search query or --verify-objects')
    if a.search:
        for r in e.rows:
            if a.query in r['source_path']:print(r['source_path']+'\t'+r['publication_kind']+'\t'+r['repository_path'])
    else:
        try:sys.stdout.buffer.write(e.read(a.query))
        except (KeyError,ValueError) as ex:raise SystemExit(str(ex))
if __name__=='__main__':main()
