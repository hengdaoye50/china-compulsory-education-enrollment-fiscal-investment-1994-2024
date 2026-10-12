from pathlib import Path
import csv,gzip,hashlib
root=Path(__file__).resolve().parents[1]
for r in csv.DictReader((root/'provenance/file_manifest.csv').open(encoding='utf-8-sig')):
 if r['compression']!='gzip':continue
 p=root/r['logical_path'];b=gzip.decompress((root/r['path']).read_bytes())
 assert hashlib.sha256(b).hexdigest()==r['published_sha256']
 if p.exists():assert p.read_bytes()==b,p
 else:p.write_bytes(b)
 print('Materialized:',r['logical_path'])
