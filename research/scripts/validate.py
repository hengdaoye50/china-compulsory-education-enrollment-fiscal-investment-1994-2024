from parse import *
import collections,math,statistics,hashlib
panel=json.loads((ROOT/'data/panel.json').read_text(encoding='utf-8'))
assert len(panel)==768
assert len({(r['year'],r['province'],r['stage']) for r in panel})==len(panel)
f=list(csv.DictReader(open(ROOT/'data/finance_long.csv',encoding='utf-8-sig')))
lookup={(int(r['year']),r['province'],r['stage'],r['metric']):r for r in f}
checks=[]
for r in f:
    y=int(r['year']);prev=lookup.get((y-1,r['province'],r['stage'],r['metric']))
    if y<2022 or r['stage']=='all' or not prev or not r.get('published_growth_pct'):continue
    actual=100*(float(r['value'])/float(prev['value'])-1);published=float(r['published_growth_pct'])
    checks.append(dict(year=y,province=r['province'],stage=r['stage'],metric=r['metric'],recomputed_growth=actual,published_growth=published,difference=actual-published,status='一致（四舍五入容差）' if abs(actual-published)<=0.015 else '需核查'))
save_csv(ROOT/'data/validation_finance_growth.csv',checks)
print('finance checks',len(checks),'issues',[r for r in checks if r['status']=='需核查'])
assert all(r['status']!='需核查' for r in checks if r['year']==2023)
# A different official source: hand-read NBS2025 Table21-19 in its saved JPEG.
anchors={'全国':(105843743,6590072),'北京':(1169475,80461),'福建':(3628055,208484),'河南':(9159594,582390),'广东':(11042666,614829),'新疆':(2776161,159141)}
cross=[]
for p,(s,t) in anchors.items():
    r=next(r for r in panel if r['province']==p and r['year']==2024 and r['stage']=='primary')
    cross.append(dict(year=2024,province=p,moe_students=r['students'],nbs_students=s,moe_teachers=r['teachers'],nbs_teachers=t,status='一致' if r['students']==s and r['teachers']==t else '需核查',source='https://www.stats.gov.cn/sj/ndsj/2025/html/C21-19.jpg'))
assert all(r['status']=='一致' for r in cross)
save_csv(ROOT/'data/validation_cross_source.csv',cross)
# Sensitivity is descriptive; repeated province-years are not independent observations.
sensitivity=[]
for st in ['primary','junior']:
    for scope in ['全样本','剔除2024','学生变化绝对值至少1%']:
        for phase in ['收缩','增长']:
            rs=[r for r in panel if r['province']!='全国' and r['stage']==st and r.get('demand_phase')==phase and (scope!='剔除2024' or r['year']<2024) and (scope!='学生变化绝对值至少1%' or abs(r['students_growth_pct'])>=1)]
            sensitivity.append(dict(stage=st,scope=scope,phase=phase,n=len(rs),median_students=statistics.median(r['students_growth_pct'] for r in rs),median_teachers=statistics.median(r['teachers_growth_pct'] for r in rs),median_classes=statistics.median(r['classes_growth_pct'] for r in rs)))
save_csv(ROOT/'data/sensitivity_phase.csv',sensitivity)
print('sensitivity',sensitivity)
files=['catalogs','indexes','extra_indexes','selected_sources','legacy_pages','legacy_tables','supplemental_catalogs','supplemental_tables','further_sources','legacy_xls']
ledger=[]
for name in files:
    for r in json.loads((ROOT/(name+'.json')).read_text(encoding='utf-8')):
        saved=r.get('path');p=ROOT/saved if saved else None
        valid=p and p.exists();sha=hashlib.sha256(p.read_bytes()).hexdigest() if valid else None
        ledger.append(dict(key=r['key'],url=r['url'],download_status=r['status'],raw_file=saved,bytes=r.get('bytes'),sha256=r.get('sha256'),hash_check=(sha==r.get('sha256')) if valid else None,error=r.get('error'),parsed_scope='见resource_schemas或finance_long；下载不等于进入分析'))
save_csv(ROOT/'data/source_ledger.csv',ledger)
print('ledger',len(ledger),'saved',sum(r['download_status']=='downloaded' for r in ledger),'unique downloaded',len({r['url'] for r in ledger if r['download_status']=='downloaded'}),'hash failures',sum(r['hash_check'] is False for r in ledger))
