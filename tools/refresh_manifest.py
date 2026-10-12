"""Refresh the release manifest after intentional data/code repository maintenance."""
from pathlib import Path
import csv,gzip,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
manifest=ROOT/'provenance/file_manifest.csv'
prior={r['path']:r for r in csv.DictReader(manifest.open(encoding='utf-8-sig'))}
cleanup=list(csv.DictReader((ROOT/'provenance/repository_cleanup_20261012.csv').open(encoding='utf8')))
old_for_new={r['new_path']:r['old_path'] for r in cleanup if r['action']=='move'}
names=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode('utf8').split('\0')
paths=sorted({p for p in names if p and (ROOT/p).is_file()}-{'provenance/file_manifest.csv','provenance/release_receipt.json'})
rows=[]
for p in paths:
 data=(ROOT/p).read_bytes();compressed=p.endswith('.csv.gz')
 logical=gzip.decompress(data) if compressed else data
 digest=hashlib.sha256(logical).hexdigest()
 before=prior.get(p,prior.get(old_for_new.get(p,''),{}))
 if p.startswith('research/raw/') or p.startswith('research/converted/'):role='source_or_converted_material'
 elif p.endswith('.py'):role='analysis_or_validation_code'
 elif p.endswith(('.png','.svg','.pdf')):role='statistical_visualization'
 elif p.startswith('research/data/'):role='data_analysis_or_method_record'
 else:role='metadata_or_navigation'
 rows.append({'path':p,'logical_path':p[:-3] if compressed else p,'role':role,'compression':'gzip' if compressed else 'none','bytes':len(logical),'stored_bytes':len(data),'source_sha256':before.get('source_sha256',digest),'published_sha256':digest,'stored_sha256':hashlib.sha256(data).hexdigest()})
with manifest.open('w',encoding='utf8',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=['path','logical_path','role','compression','bytes','stored_bytes','source_sha256','published_sha256','stored_sha256']);writer.writeheader();writer.writerows(rows)
receipt={'scope':'data_analysis_and_visualizations_only','date':'2026-10-12','manifest_artifact_count':len(rows),'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'cleanup_removed_file_count':sum(r['action']=='remove' for r in cleanup),'retained_statistical_figures':True,'full_raw_to_analysis_pipeline_verified':False,'target_repository':'https://github.com/hengdaoye50/china-compulsory-education-enrollment-fiscal-investment-1994-2024'}
(ROOT/'provenance/release_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
