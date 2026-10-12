"""Extract and reconcile grade-level source fields before choosing analysis path."""
import json,csv,re,hashlib
from parse import ROOT,read,save_csv
PROVINCES=['北京','天津','河北','山西','内蒙古','辽宁','吉林','黑龙江','上海','江苏','浙江','安徽','福建','江西','山东','河南','湖北','湖南','广东','广西','海南','重庆','四川','贵州','云南','西藏','陕西','甘肃','青海','宁夏','新疆']
def region(s):
    s=re.sub(r'\s','',s)
    if s.startswith(('总计','全国','合计')):return '全国'
    return next((p for p in PROVINCES if s.startswith(p)),None)
def value(s):
    s=s.replace(',','').strip()
    return int(s) if re.fullmatch(r'\d+',s) else None
schema=json.loads((ROOT/'data/resource_schemas.json').read_text(encoding='utf-8'))
levels={(int(r['year']),r['stage'],r['province']):r for r in csv.DictReader(open(ROOT/'data/education_resource_panel.csv',encoding='utf-8-sig'))}
records={};cells=[];checks=[];notes=[]
for s in schema:
    if s['kind'] not in ['students','classes']:continue
    year,stage,kind=s['year'],s['stage'],s['kind']
    count=6 if stage=='primary' else 4
    start=s['columns']['grade1'] if kind=='students' else (4 if stage=='primary' else 6)
    parsed=read(ROOT/s['path']);seen=set()
    total_column=s['columns'][kind]
    def is_data(row):
        return bool(row and region(row[0]) and len(row)>total_column and value(row[total_column]) is not None)
    # Confirm grade labels exist, including Grade 4 for junior (do not truncate).
    header=' '.join(' '.join(row) for tab in parsed.tables for row in tab if not is_data(row))
    for i in range(1,count+1):
        if not re.search(r'Grade\s*'+str(i),header,re.I):
            raise ValueError((year,stage,kind,i,parsed.tables[0][:5]))
    for table in parsed.tables:
        for row in table:
            if not is_data(row):continue
            province=region(row[0])
            if province is None:continue
            assert province not in seen;seen.add(province)
            assert len(row)>start+count-1
            key=(year,stage,province)
            rec=records.setdefault(key,{'year':year,'stage':stage,'province':province})
            for i in range(count):
                field=f'{kind}_grade{i+1}'
                number=value(row[start+i]);rec[field]=number
                cells.append({'year':year,'stage':stage,'province':province,'metric':field,'value':number,'raw_value':row[start+i],'column_index':start+i,'source':s['source'],'path':s['path']})
            rec[kind+'_total']=int(levels[key][kind])
            rec[kind+'_source']=s['source']
            vals=[rec[f'{kind}_grade{i+1}'] for i in range(count)]
            if kind=='classes' and stage=='primary':
                rec['classes_multiple_grade']=value(row[start+count])
                cells.append({'year':year,'stage':stage,'province':province,'metric':'classes_multiple_grade','value':rec['classes_multiple_grade'],'raw_value':row[start+count],'column_index':start+count,'source':s['source'],'path':s['path']})
                vals.append(rec['classes_multiple_grade'])
            checks.append({'year':year,'stage':stage,'province':province,'kind':kind,'check':'grade_sum_vs_total',
                           'complete':all(v is not None for v in vals),'grade_sum':sum(v for v in vals if v is not None),
                           'total':rec[kind+'_total'],'difference':sum(v for v in vals if v is not None)-rec[kind+'_total'] if all(v is not None for v in vals) else None})
    assert seen==set(PROVINCES+['全国'])
    notes.append({'year':year,'stage':stage,'kind':kind,'first_grade_column':start,'grades':count,'source':s['source'],'path':s['path'],'sha256':hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),'note_text':parsed.text[-35:]})
for year in range(2013,2025):
    for stage in ['primary','junior']:
        count=6 if stage=='primary' else 4
        metrics=[f'{kind}_grade{i+1}' for kind in ['students','classes'] for i in range(count)]
        if stage=='primary':metrics.append('classes_multiple_grade')
        for field in metrics:
            vals=[records[year,stage,p][field] for p in PROVINCES]
            national=records[year,stage,'全国'][field]
            complete=all(v is not None for v in vals) and national is not None
            checks.append({'year':year,'stage':stage,'province':'全国','kind':field,'check':'province_sum_vs_national',
                           'complete':complete,'grade_sum':sum(v for v in vals if v is not None),'total':national,
                           'difference':sum(v for v in vals if v is not None)-national if complete else None})
bad=[c for c in checks if c['complete'] and c['difference']!=0]
assert len(records)==768
save_csv(ROOT/'data/grade_structure_panel.csv',[records[k] for k in sorted(records)])
save_csv(ROOT/'data/grade_structure_cells.csv',cells)
save_csv(ROOT/'data/grade_structure_checks.csv',checks)
(ROOT/'data/grade_structure_sources.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2),encoding='utf-8')
audit={'years':'2013-2024','stages':['primary','junior'],'provincial_rows':744,'national_rows':24,
       'student_grade_cells':sum(c['metric'].startswith('students_') for c in cells),
       'missing_student_grade_cells':sum(c['metric'].startswith('students_') and c['value'] is None for c in cells),
       'missing_class_grade_cells':sum(c['metric'].startswith('classes_grade') and c['value'] is None for c in cells),
       'missing_multiple_grade_cells':sum(c['metric']=='classes_multiple_grade' and c['value'] is None for c in cells),
       'complete_checks':sum(c['complete'] for c in checks),'incomplete_checks':sum(not c['complete'] for c in checks),'nonzero_checks':bad,
       'status':'reconciled' if not bad else 'requires_review',
       'analysis_status':'Availability and arithmetic checks only; no cohort model, migration estimate or causal analysis.',
       'caveats':['Junior Grade 4 retained; do not impose three-year structure.','Primary multiple-grade classes kept separate; missing remains missing, not zero.','Same grade across years is not necessarily the same cohort; grade progression is not a pure migration or retention measure.']}
(ROOT/'data/grade_structure_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
