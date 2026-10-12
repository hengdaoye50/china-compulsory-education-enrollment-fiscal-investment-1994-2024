"""Reviewed Fujian census snapshot; no projection, age splitting, or panel merge."""
from pathlib import Path
import csv, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
URL = 'https://tjj.fujian.gov.cn/tongjinianjian/rk2020/html/a0301.jpg'
NOTE_URL = 'https://tjj.fujian.gov.cn/tongjinianjian/rk2020/html/note.jpg'
# Direct transcription, visually reviewed from original table 3-1, first part (all data).
cells = [
 (380993,206764,174229),(444284,240740,203544),(500514,270953,229561),
 (625966,337895,288071),(597587,324405,273182),(610100,332369,277731),
 (630412,344261,286151),(593771,321486,272285),(626379,340214,286165),
 (533208,289590,243618),(499618,271535,228083),(522636,283628,239008),
 (516680,279596,237084),(487688,263413,224275),(455389,244492,210897),
 (428675,230351,198324),(419130,225807,193323),(391848,211593,180255),
 (375620,202642,172978),(396823,210738,186085),
]
def save(name, rows):
 with (DATA / name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

rows=[dict(province='福建',year=2020,reference_time='2020-11-01 00:00',age_completed=a,
 total=t,male=m,female=f,unit='人',count_type='census resident population; all-data part',
 table='3-1',url=URL,source_path='raw/population_fujian2020_a0301.jpg',
 excludes='active servicemen; Kinmen and Matsu islands; short-term overseas visitors',
 annual_panel_eligible=False,school_enrollment_denominator_certified=False)
 for a,(t,m,f) in enumerate(cells)]
checks=[]
for r in rows:
 gap=r['total']-r['male']-r['female'];assert gap==0
 checks.append(dict(check='single-age sex sum',age_or_window=str(r['age_completed']),gap=gap))
groups=[(0,4,(2549344,1380757,1168587)),(5,9,(2993870,1627920,1365950)),
 (10,14,(2482011,1342664,1139347)),(15,19,(2012096,1081131,930965))]
for lo,hi,expected in groups:
 for col,j in [('total',0),('male',1),('female',2)]:
  gap=sum(r[col] for r in rows[lo:hi+1])-expected[j];assert gap==0
  checks.append(dict(check='single ages versus original five-year group '+col,age_or_window=f'{lo}-{hi}',gap=gap))
# Official bulletin first release: total and sex counts agree; age 0-14/0-15 provide independent grouping checks.
for lo,hi,expected in [(0,14,8025225),(0,15,8453900)]:
 gap=sum(r['total'] for r in rows[lo:hi+1])-expected;assert gap==0
 checks.append(dict(check='single ages versus official bulletin',age_or_window=f'{lo}-{hi}',gap=gap))
assert 21466757+20073329==41540086
windows=[]
for lo,hi in [(0,4),(5,9),(10,14),(15,19),(6,11),(12,14),(6,10),(11,14)]:
 window=rows[lo:hi+1]
 windows.append(dict(province='福建',year=2020,age_window=f'{lo}-{hi}',
 total=sum(r['total'] for r in window),male=sum(r['male'] for r in window),
 female=sum(r['female'] for r in window),age_count=hi-lo+1,
 interpretation='observed age-window population; not actual enrollment or certified school-age denominator',url=URL))
save('population_province2020_single_age.csv',rows)
save('population_province2020_age_windows.csv',windows)
save('population_province2020_checks.csv',checks)
sources=[]
for fn,url in [('population_fujian2020_a0301.jpg',URL),('population_fujian2020_note.jpg',NOTE_URL),
 ('population_fujian2020_index.html','https://tjj.fujian.gov.cn/tongjinianjian/rk2020/indexch.htm'),
 ('population_fujian2020_left.htm','https://tjj.fujian.gov.cn/tongjinianjian/rk2020/left.htm'),
 ('population_fujian_catalog.html','https://tjj.fujian.gov.cn/xxgk/ndsj/'),
 ('population_fujian2020_bulletin.html','https://tjj.fujian.gov.cn/xxgk/tjgb/202105/t20210520_5598797.htm')]:
 p=ROOT/'raw'/fn;b=p.read_bytes();sources.append(dict(url=url,path='raw/'+fn,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
save('population_province2020_sources.csv',sources)
coverage=[dict(province='福建',year=2020,status='original age table and note inspected',resolution='single completed ages',
 extracted_ages='0-19',annual_panel_eligible=False,url=URL,reason='one census snapshot; annual series and schooling scope bridge not certified'),
 dict(province='黑龙江',year=2020,status='catalog located; original image inaccessible',resolution='not certified',
 extracted_ages='',annual_panel_eligible=False,url='https://tjj.hlj.gov.cn/tjjnianjian/2020rkpc/zk/html/A0301.jpg',reason='HTTP 403 in public download; web fetch timeout; no transcription')]
save('population_province2020_coverage.csv',coverage)
protected=json.loads((DATA/'province_finance_next_protected_baseline.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
audit=dict(province_snapshots_extracted=1,age_rows=20,transcribed_count_cells=60,
 arithmetic_checks=len(checks),checks_passed=True,source_files_hashed=len(sources),
 original_note_visually_reviewed=True,annual_panel_merged=False,protected_files_unchanged=True,
 limit='pilot source validation, not a national coverage audit or annual population reconstruction')
(DATA/'population_province2020_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False));print(json.dumps(windows,ensure_ascii=False))
