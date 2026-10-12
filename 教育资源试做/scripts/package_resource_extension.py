"""Package the resource extension without altering prior full-history releases."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'教育资源试做/data';OUT=ROOT/'资源解释拓展报告_20261011'
receipt=json.loads((DATA/'资源解释拓展_20261011/analysis_receipt.json').read_text(encoding='utf8'))
files=[]
for folder in [DATA/'资源解释拓展_20261011',ROOT/'教育资源试做/资源解释图组_20261011']:
    files.extend(p for p in folder.rglob('*') if p.is_file())
files.extend(p for p in OUT.iterdir() if p.is_file() and p.suffix in ['.docx','.pdf','.json','.md'])
files.extend(ROOT/p for p in receipt['input_hashes'])
files.extend(ROOT/p for p in receipt['raw_resource_hashes'])
files.append(DATA/'province_finance_next_protected_baseline.json')
for name in ['extend_resource_explanations.py','audit_resource_explanations.py','build_resource_extension_report.py','package_resource_extension.py','exploratory_panel_stats.py','infer_resource_timing.py','parse.py']:
    files.append(ROOT/'教育资源试做/scripts'/name)
files.append(ROOT/'研究接续_20261011_资源解释拓展.md')
files=sorted(set(files));manifest=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
target=OUT/'资源解释拓展复现增量包.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:z.write(p,p.relative_to(ROOT).as_posix())
    z.writestr('资源解释拓展增量清单.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    for row in manifest:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
print(len(files),'files; archive hashes verified;',target.stat().st_size,'bytes')
