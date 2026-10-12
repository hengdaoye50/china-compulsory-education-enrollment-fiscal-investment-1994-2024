from parse import *
import math,statistics
OUT=ROOT/'data';OUT.mkdir(exist_ok=True)
PROVINCES=['北京','天津','河北','山西','内蒙古','辽宁','吉林','黑龙江','上海','江苏','浙江','安徽','福建','江西','山东','河南','湖北','湖南','广东','广西','海南','重庆','四川','贵州','云南','西藏','陕西','甘肃','青海','宁夏','新疆']
def region(s):
    s=re.sub(r'\s','',s);s=re.sub(r'[A-Za-z\(\)\-]','',s)
    if s in ['总计','全国','合计']:return '全国'
    for p in PROVINCES:
        if s.startswith(p):return p
    return None
def number(s):
    s=s.replace(',','').replace(' ','')
    return float(s) if re.fullmatch(r'-?\d+(\.\d+)?',s) else None
def title(path):
    s=decode(path.read_bytes());m=re.search(r'<meta name="ArticleTitle" content="(.*?)"',s)
    return m[1] if m else ''
sources=[]
for f in ['selected_sources','legacy_tables','supplemental_tables']:
    if (ROOT/(f+'.json')).exists():sources+=json.loads((ROOT/(f+'.json')).read_text(encoding='utf-8'))
resources={}; resource_cells=[]; audit=[]; schemas=[]
for src in sources:
    if src['status']!='downloaded' or 'region' not in src['key']:continue
    path=ROOT/src['path'];t=title(path)
    if not any(x in t for x in ['小学','初中']):continue
    stage='primary' if '小学' in t else 'junior'; year=int(re.search(r'20\d{2}',src['key'])[0])
    if '学生数' in t:kind='students'
    elif '校数' in t:kind='classes'
    elif '专任教师' in t:kind='teachers'
    else:continue
    parsed=read(path);data=[row for tab in parsed.tables for row in tab if row and region(row[0])]
    if not data:continue
    columns={}
    if kind=='students':
        # Elementary preschool columns expanded from one aggregate to four from 2021.
        idx=7 if stage=='primary' and year>=2021 else (4 if stage=='primary' else 3)
        columns={'graduates':1,'entrants':2,'students':idx,'female_students':idx+1,'grade1':idx+2}
    elif kind=='teachers':columns={'teachers':1}
    else:columns={'schools':1,'classes':3 if stage=='primary' else 5};columns.update({'teaching_sites':2} if stage=='primary' else {})
    schemas.append(dict(year=year,stage=stage,kind=kind,title=t,columns=columns,headers=parsed.tables[0][:2],source=src['url'],path=src['path']))
    for row in data:
        p=region(row[0]);key=(year,p,stage); rec=resources.setdefault(key,dict(year=year,province=p,stage=stage))
        for metric,idx in columns.items():
            value=number(row[idx]);rec[metric]=int(value) if value is not None else None;rec[kind+'_source']=src['url']
            resource_cells.append(dict(year=year,province=p,stage=stage,metric=metric,value=rec[metric],source=src['url'],raw_file=src['path'],column_index=idx,raw_value=row[idx]))
    for metric in columns:
        national=resources.get((year,'全国',stage),{}).get(metric)
        vals=[resources.get((year,p,stage),{}).get(metric) for p in PROVINCES]
        observed=[v for v in vals if v is not None]
        audit.append(dict(year=year,stage=stage,metric=metric,provinces_present=len(observed),province_sum=sum(observed),national=national,difference=sum(observed)-national if national is not None else None))
finance=[];finance_cells=[]
for year in range(2010,2025):
    file=ROOT/'converted'/f'finance_{year}_36.html'
    if not file.exists():continue
    ts=read(file).tables; src=next(x for x in sources if x['key']==f'finance_{year}_36')
    stage_tables=[(i,t) for i,t in enumerate(ts) if t and '普通小学' in t[0]]
    # The 2017 attachment still contains only career and public per-student tables.
    # A terminology change to general public budget did not add a budget table.
    if year<=2017:metrics=['career_per_student','public_per_student']
    else:metrics=['budget_per_student','career_per_student','public_per_student']
    for metric,(i,table) in zip(metrics,stage_tables):
        header=table[0];stride=2 if year>=2021 else 3
        for st,label in [('primary','普通小学'),('junior','普通初中')]:
            start=1+(header.index(label)-1)*stride; idx=start if stride==2 else start+1;growth=idx+1
            for row in table[2:]:
                p=region(row[0])
                if not p:continue
                value=number(row[idx]);rate=number(row[growth]);finance.append(dict(year=year,province=p,stage=st,metric=metric,value=value,published_growth_pct=rate,source=src['url'],table_index=i,column_index=idx,scope_break=year==2021 and metric=='budget_per_student'))
                finance_cells.append(finance[-1])
    # Do not splice province spending into primary spending: this is all-stage regional context.
    for row in ts[0][1:]:
        p=region(row[0])
        if not p or year<2013:continue
        vals=[number(s) for s in row[1:]]
        if year>=2023:total,growth,share=vals[:3]
        else:total,share,growth=vals[:3]
        finance.append(dict(year=year,province=p,stage='all',metric='regional_budget_education_100m',value=total,published_growth_pct=growth,source=src['url'],table_index=0,column_index=1,scope_break=year==2021))
        finance.append(dict(year=year,province=p,stage='all',metric='education_budget_share_pct',value=share,source=src['url'],table_index=0,column_index=3 if year>=2023 else 2,scope_break=year==2021))
panel=[]
for key,r in sorted(resources.items()):
    for f in finance:
        if (f['year'],f['province'],f['stage'])==key:r[f['metric']]=f['value'];r[f['metric']+'_source']=f['source']
        if (f['year'],f['province'])==key[:2] and f['stage']=='all':r[f['metric']]=f['value'];r[f['metric']+'_source']=f['source']
    if r.get('students') and r.get('teachers'):
        r['pupils_per_teacher']=r['students']/r['teachers'];r['teachers_per_100_students']=100*r['teachers']/r['students']
    if r.get('students') and r.get('classes'):r['pupils_per_class']=r['students']/r['classes']
    previous=resources.get((r['year']-1,r['province'],r['stage']),{})
    for m in ['students','entrants','teachers','classes']:
        if r.get(m) and previous.get(m):r[m+'_growth_pct']=100*(r[m]/previous[m]-1)
    if r.get('students_growth_pct') is not None:
        r['demand_phase']='收缩' if r['students_growth_pct']<0 else '增长'
    panel.append(r)
save_csv(OUT/'education_resource_panel.csv',panel)
save_csv(OUT/'resource_cells.csv',resource_cells)
save_csv(OUT/'finance_long.csv',finance)
save_csv(OUT/'validation_totals.csv',audit)
(OUT/'resource_schemas.json').write_text(json.dumps(schemas,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'panel.json').write_text(json.dumps(panel,ensure_ascii=False,indent=2),encoding='utf-8')
print('resource panel',len(panel),'provincial',sum(r['province']!='全国' for r in panel),'finance',len(finance))
print('audit nonzero differences',[r for r in audit if r['difference'] not in [None,0]])
print('missing main',[(r['year'],r['province'],r['stage']) for r in panel if any(r.get(m) is None for m in ['students','entrants','teachers','classes'])])
