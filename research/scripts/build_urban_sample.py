"""Extract national education-stage category totals; never substitute school staffing."""
import csv,json,re,hashlib
from parse import ROOT,read,save_csv

def number(value):
    value=re.sub(r'[\s,，]','',value)
    return int(value) if re.fullmatch(r'\d+',value) else None

def category(label):
    label=re.sub(r'\s','',label)
    for x in ['城区','镇区','乡村']:
        if label.startswith(x):return x
    if label.startswith(('总计','合计')):return '全国'
    return None

panel=list(csv.DictReader((ROOT/'data/education_resource_panel.csv').open(encoding='utf-8-sig')))
national={(int(r['year']),r['stage']):r for r in panel if r['province']=='全国'}
inventory=json.loads((ROOT/'data/structure_source_headers.json').read_text(encoding='utf-8'))
candidates=[];audit=[]
for source in inventory:
    if 'national' not in source['key']:continue
    title=source['title']
    stage='primary' if '小学' in title else 'junior' if '初中' in title else None
    if not stage or '教职工' in title:continue
    metric='teachers' if '专任教师' in title else 'students' if '学生' in title else 'classes' if '班' in title or '教学基本情况' in title else None
    if not metric:continue
    year=source['year'];expected=int(national[year,stage][metric])
    for ti,table in enumerate(read(ROOT/source['path']).tables):
        totals=[(i,row) for i,row in enumerate(table) if row and category(row[0])=='全国' and expected in [number(v) for v in row[1:]]]
        outer_rows=[(category(row[0]),i,row) for i,row in enumerate(table) if row and category(row[0]) in ['城区','镇区','乡村']]
        outer={c:(i,row) for c,i,row in outer_rows}
        assert len(outer_rows)==len(outer),(source['path'],'duplicate category rows')
        if not totals:continue
        for ni,nrow in totals:
            for col,value in enumerate(nrow):
                if number(value)!=expected:continue
                valid=len(outer)==3 and all(len(row)>col and number(row[col]) is not None for _,row in outer.values())
                delta=sum(number(row[col]) for _,row in outer.values())-expected if valid else None
                item={'year':year,'stage':stage,'metric':metric,'title':title,'source':source['source'],'path':source['path'],'sha256':source['sha256'],'table_index':ti,'column_index':col,'national_row_index':ni,'national_value':expected,'categories_complete':valid,'category_sum_difference':delta}
                audit.append(item)
                if valid and delta==0:
                    candidates.append((item,outer,nrow))

save_csv(ROOT/'data/urban_source_candidates.csv',audit)
cells=[];output=[];checks=[];missing=[]
for key,n in sorted(national.items()):
    year,stage=key
    rows={c:{'year':year,'stage':stage,'category':c} for c in ['全国','城区','镇区','乡村']}
    for metric in ['students','teachers','classes']:
        options=[v for v in candidates if (v[0]['year'],v[0]['stage'],v[0]['metric'])==(year,stage,metric)]
        if not options:
            missing.append({'year':year,'stage':stage,'metric':metric});continue
        # Prefer explicit urban student tables; teacher course/age tables are cross-checked.
        options.sort(key=lambda v:(0 if '城乡' in v[0]['title'] else 1,v[0]['path']))
        chosen,outer,nrow=options[0]
        for other,o,_ in options:
            differences={c:number(o[c][1][other['column_index']])-number(outer[c][1][chosen['column_index']]) for c in outer}
            checks.append({'year':year,'stage':stage,'metric':metric,'chosen':chosen['path'],'comparison':other['path'],'category_differences':json.dumps(differences,ensure_ascii=False),'match':all(v==0 for v in differences.values())})
        for c in rows:
            ri,row=(chosen['national_row_index'],nrow) if c=='全国' else outer[c]
            val=number(row[chosen['column_index']]);rows[c][metric]=val
            rows[c][metric+'_source']=chosen['source']
            cells.append({**chosen,'category':c,'raw_label':row[0],'row_index':ri,'raw_value':row[chosen['column_index']],'value':val,'current_digest_match':hashlib.sha256((ROOT/chosen['path']).read_bytes()).hexdigest()==chosen['sha256']})
    output.extend(rows.values())
save_csv(ROOT/'data/national_urban_rural_panel.csv',output)
save_csv(ROOT/'data/national_urban_rural_cells.csv',cells)
save_csv(ROOT/'data/urban_cross_source_checks.csv',checks)
validation={'panel_rows':len(output),'cells':len(cells),'missing':missing,'candidate_tables':len(candidates),'cross_source_checks':len(checks),'cross_source_mismatches':[c for c in checks if not c['match']],'digest_mismatches':sum(not c['current_digest_match'] for c in cells),'scope':'Published nationwide school-location categories; changing geographic membership cannot be held constant.'}
(ROOT/'data/urban_sample_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(validation,ensure_ascii=False))
