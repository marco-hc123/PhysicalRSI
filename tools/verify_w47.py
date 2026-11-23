"""Recompute W47 results from the public native receipts, offline."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'experiments/task_transfer_20261122'


def check(condition, context):
    if not condition:
        raise ValueError(context)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def verify():
    manifest = json.loads((ROOT / 'provenance/w47-20261122.json').read_text())
    for name, entry in manifest['members'].items():
        check(digest((ROOT / name).read_bytes()) == entry['sha256'], name)
        if entry['format'] == 'original bytes':
            check(entry['source_sha256'] == entry['sha256'], name)

    counts = Counter()
    cases = {}
    paths = set()
    for line in (DATA / 'episodes.jsonl').read_text().splitlines():
        row = json.loads(line)
        raw = row['native_utf8']
        check(digest(raw.encode()) == row['receipt_sha256'], row['receipt'])
        details = json.loads(raw)['details']
        check(len(details) == 1, row['receipt'])
        detail = next(iter(details.values()))
        check(isinstance(detail['success'], bool) and detail['success'] == row['success'], row['receipt'])
        check(detail['score'] * 100 == row['score_100'], row['receipt'])
        key = row['batch'], row['variant'], row['split'], row['layout_one_based']
        check(key not in cases and row['receipt'] not in paths, key)
        paths.add(row['receipt'])
        cases[key] = row
        counts[row['batch']] += 1
    check(counts == {'M0': 23, 'M1': 3, 'Expansion': 110, 'Classify': 97}, counts)

    prior = read_csv(ROOT / 'experiments/pickup_transfer_20261119/formal-scores.csv')
    old = {r['layout_sha256']: float(r['old_score']) * 100 for r in prior}
    pickup = read_csv(DATA / 'pickup/formal-paired.csv')
    check({int(r['layout']) for r in pickup} == set(range(1, 21)) and len(pickup) == 20, 'pickup layouts')
    for r in pickup:
        layout = int(r['layout'])
        m0 = cases['M0', 'M0', 'formal', layout]
        check(m0['score_100'] == float(r['M0']) and old[m0['layout_sha256']] == float(r['original']), r)
        for v in ('V6', 'V7'):
            e = cases['Expansion', v, 'formal', layout]
            check(e['layout_sha256'] == m0['layout_sha256'] and e['score_100'] == float(r[v]), (v, layout))
            check((e['phase'] == 'phaseA') == (r['screened'] == 'True'), (v, layout))
    check(sum(float(r['original']) == 100 for r in pickup) == 1, 'historical control')
    for v in ('V6', 'V7'):
        check(sum(float(r[v]) == 100 for r in pickup) == 8, v)
        check(sum(float(r[v]) == 100 for r in pickup if r['screened'] == 'False') == 4, v)

    paired = read_csv(DATA / 'classify/closed_loop/formal-paired.csv')
    check(len(paired) == 20 and {int(r['index']) for r in paired} == set(range(20)), 'classification layouts')
    diffs = defaultdict(list)
    for r in paired:
        for v in ('C0', 'C7'):
            e = cases['Classify', v, 'formal', int(r['index']) + 1]
            check(e['layout_sha256'] == r['layout_sha256'] and e['score_100'] == float(r[v + '_score_100']), r)
            check(not e['success'] and r[v + '_success'] == 'False', r)
        diffs[r['split']].append(float(r['C7_score_100']) - float(r['C0_score_100']))
    check(sorted(diffs['screening']) == [0] * 4 + [15], 'classification screening')
    check(sorted(diffs['heldout']) == [0] * 13 + [15] * 2, 'classification heldout')
    print('233 unique terminal receipts. Pickup V6/V7: 8/20 each. Classification C0/C7: 0/20 full successes; mean change +2.25 (+2.00 heldout).')


if __name__ == '__main__':
    verify()
