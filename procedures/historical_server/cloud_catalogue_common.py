"""Shared source integrity checks for the bounded cloud catalogue study."""
import hashlib
import json
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def verify_source_pins(suite):
    suite = Path(suite)
    pins = json.loads((suite / 'source-pins.json').read_text())
    assert pins['files'], 'Missing source pins'
    for path, expected in pins['files'].items():
        assert sha256(path) == expected, 'Frozen source changed: ' + path
    assert sha256(suite / 'protocol.json') == pins['protocol_sha256']
    for path,expected in pins.get('checkpoint_file_stats',{}).items():
        stat=Path(path).stat()
        assert stat.st_size==expected['bytes'] and stat.st_mtime_ns==expected['mtime_ns'], 'Checkpoint changed: '+path
    return True
