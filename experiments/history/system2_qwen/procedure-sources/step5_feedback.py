"""Predeclared development-metric projection; raw evidence stays on the cloud."""
from copy import deepcopy
import hashlib
import json


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()


def project_feedback(rows):
    projected = []
    for row in rows:
        if row.get('split') != 'development' or row.get('state') != 'completed':
            raise ValueError('Only completed development evidence may reach proposal')
        if not row.get('natural_terminal') or not row.get('evidence'):
            raise ValueError('Native completion and retained evidence required')
        item = deepcopy(row)
        evidence = item.pop('evidence')
        item['evidence_receipt'] = dict(
            complete_row_sha256=hashlib.sha256(canonical(row)).hexdigest(),
            artifact_count=len(evidence),
            representation='Full verified artifact inventory retained in development-results.json; not pasted into model input')
        projected.append(item)
    return projected
