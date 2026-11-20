"""Verify the public November evidence without running a model or simulator."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
PLANNING = ROOT / 'experiments/planning_feedback_20261115'
TRANSFER = ROOT / 'experiments/pickup_transfer_20261119'


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def verify():
    manifest = json.loads((ROOT / 'provenance/november-evidence-20261120.json').read_text())
    for entry in manifest:
        require(digest(ROOT / entry['file']) == entry['sha256'], entry['file'])
        if entry['transformation'] == 'byte-for-byte':
            require(entry['source_sha256'] == entry['sha256'], entry['file'])

    groups = defaultdict(dict)
    for row in read_rows(PLANNING / 'holdout.csv'):
        series = groups[row['task'], row['group']]
        layout = row['layout_sha256']
        require(layout not in series and row['status'] == 'verified', layout)
        series[layout] = row
    expected = {
        ('classify_objects', 'P=A'): ('classification/parent.py', 0, 4.25),
        ('classify_objects', 'B'): ('classification/pilot_B_c2.py', 0, 2.25),
        ('general_pickup', 'P=A=B'): ('pickup/parent.py', 1, 5),
    }
    require(groups.keys() == expected.keys(), 'Unexpected holdout groups')
    for key, (source, successes, average) in expected.items():
        rows = groups[key].values()
        identity = digest(PLANNING / source)
        require(len(rows) == 20 and all(r['source_sha256'] == r['loaded_revision'] == identity for r in rows), source)
        require(sum(r['success'] == 'True' for r in rows) == successes, str(key))
        require(mean(100 * float(r['score']) for r in rows) == average, str(key))
        print(f'{key[0]} {key[1]}: {successes}/20, mean {average:g}')

    parent = groups['classify_objects', 'P=A']
    candidate = groups['classify_objects', 'B']
    require(parent.keys() == candidate.keys(), 'Classification layout mismatch')
    differences = [float(candidate[k]['score']) - float(parent[k]['score']) for k in parent]
    require(Counter((v > 0) - (v < 0) for v in differences) == {1: 1, 0: 16, -1: 3}, 'Paired scores')

    pickup = groups['general_pickup', 'P=A=B']
    for split, count, prior in [('development', 3, 2), ('formal', 20, 1)]:
        rows = read_rows(TRANSFER / f'{split}-scores.csv')
        layouts = {r['layout_sha256'] for r in rows}
        require(len(rows) == len(layouts) == count, split)
        require(sum(r['old_success'] == 'True' for r in rows) == prior, split)
        require(all(r['new_success'] == 'False' and float(r['new_score']) == 0 for r in rows), split)
        if split == 'formal':
            require(layouts == pickup.keys(), 'Transfer layout mismatch')
            for r in rows:
                ref = pickup[r['layout_sha256']]
                require(ref['success'] == r['old_success'] and float(ref['score']) == float(r['old_score']), 'Historical comparator')
        print(f'Three-module {split}: {prior}/{count} -> 0/{count}')
    print(f'{len(manifest)} evidence files verified.')


if __name__ == '__main__':
    verify()
