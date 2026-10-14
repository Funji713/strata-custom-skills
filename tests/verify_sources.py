"""Verify the exact source archive; does not claim a security or license audit."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'SOURCE_MANIFEST.json').read_text(encoding='utf-8-sig'))
expected = {f['path'] for f in manifest['files']}
actual = {p.relative_to(root).as_posix() for p in (root / 'skills').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
assert actual == expected, 'Source inventory differs from manifest'
for spec in manifest['files']:
    data = (root / spec['path']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == spec['sha256'], spec['path']
    assert len(data) == spec['bytes'], spec['path']
print(f'Verified {len(expected)} original source files byte-for-byte')
