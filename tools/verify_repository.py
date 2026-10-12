"""Check repository navigation, Python syntax, indexed figures and release hygiene."""
from pathlib import Path
from urllib.parse import unquote
import csv,json,re

ROOT=Path(__file__).resolve().parents[1]
manifest=list(csv.DictReader((ROOT/'provenance/file_manifest.csv').open(encoding='utf-8-sig')))
paths={r['path'] for r in manifest}
files=[ROOT/p for p in sorted(paths)]
checks={}
checks['unique_manifest_paths']=len(paths)==len(manifest)
checks['all_manifest_files_exist']=all(p.is_file() for p in files)
checks['organized_roots']=all((ROOT/p).is_dir() for p in ['research/data','research/scripts','research/figures','research/notes','visualizations','provenance','tools'])
checks['legacy_trial_directory_removed']=not (ROOT/'教育资源试做').exists()
prohibited=re.compile(r'(^|/)(\.tmp|\.venv|__pycache__|\.ipynb_checkpoints|reports)(/|$)|(^|/)~\$|\.(pyc|tmp|bak|log|docx)$|/qa/(contact|view|final_fig).*\.png$|/qa/.*_grayscale\.png$|archive_before_early_reconstruction/')
checks['no_temporary_or_report_files_in_release']=not any(prohibited.search(p) for p in paths)
syntax=[]
for p in files:
 if p.suffix=='.py':compile(p.read_text(encoding='utf-8-sig'),str(p),'exec');syntax.append(p.relative_to(ROOT).as_posix())
checks['python_syntax']=True
links=[]
for relative in ['README.md','research/DATA_INDEX.md','provenance/README.md','visualizations/FIGURE_INDEX.md']:
 p=ROOT/relative
 for url in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
  if re.match(r'^(https?://|#)',url):continue
  target=(p.parent/unquote(url.split('#')[0])).resolve()
  assert target.is_relative_to(ROOT) and target.exists(),(relative,url)
  links.append((relative,url))
checks['navigation_links_exist']=True
figures=list(csv.DictReader((ROOT/'visualizations/figure_index.csv').open(encoding='utf-8-sig')))
checks['18_sequential_current_figures']=[int(r['figure_number']) for r in figures]==list(range(1,19))
for r in figures:
 for col in ['png_path','pdf_path','svg_path','data_path','generator_path']:
  assert (ROOT/r[col]).is_file(),(r['figure_number'],col,r[col])
checks['figure_data_and_generators_exist']=True
allowed=paths|{'provenance/file_manifest.csv','provenance/release_receipt.json'}|{r['logical_path'] for r in manifest if r['compression']=='gzip'}
extras=[]
for p in ROOT.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(ROOT).as_posix()
 if '.git' in p.relative_to(ROOT).parts or any(x in p.relative_to(ROOT).parts for x in ['.tmp','.venv','__pycache__','.ipynb_checkpoints']):continue
 if rel not in allowed:extras.append(rel)
checks['no_unlisted_payload_files']=not extras
result={'passed':all(checks.values()),'checks':checks,'python_files_checked':len(syntax),'navigation_links_checked':len(links),'figures_checked':len(figures),'unlisted_files':extras}
print(json.dumps(result,ensure_ascii=False,indent=2))
assert result['passed'],result
