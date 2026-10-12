from pathlib import Path
import csv,gzip,hashlib
root=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((root/'provenance/file_manifest.csv').open(encoding='utf-8-sig')))
for r in rows:
 p=root/r['path'];b=p.read_bytes()
 assert hashlib.sha256(b).hexdigest()==r['stored_sha256'],r['path']
 if r['compression']=='gzip':b=gzip.decompress(b)
 assert hashlib.sha256(b).hexdigest()==r['published_sha256'],r['logical_path']
print(f'PASS: {len(rows)} research artifacts verified; stored and logical hashes match.')
