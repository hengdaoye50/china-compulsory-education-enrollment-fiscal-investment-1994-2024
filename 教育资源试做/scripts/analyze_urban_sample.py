"""Descriptive category changes and exact arithmetic decompositions; no causal models."""
import csv,json,math
from parse import ROOT,read,save_csv

def load(name):return list(csv.DictReader((ROOT/'data'/name).open(encoding='utf-8-sig')))
rows=load('national_urban_rural_panel.csv')
for r in rows:
    r['year']=int(r['year'])
    for m in ['students','teachers','classes']:r[m]=int(r[m]) if r[m] else None
lookup={(r['year'],r['stage'],r['category']):r for r in rows}
grades={(int(r['year']),r['stage']):r for r in load('grade_structure_panel.csv') if r['province']=='全国'}
extra=[];extra_checks=[]
for cell in load('national_urban_rural_cells.csv'):
    if cell['category']!='全国' or cell['metric'] not in ['students','classes']:continue
    year=int(cell['year']);stage=cell['stage'];metric=cell['metric']
    expected=int(grades[year,stage][metric+'_grade1'])
    table=read(ROOT/cell['path']).tables[int(cell['table_index'])]
    nr=table[int(cell['row_index'])]
    columns=[i for i,v in enumerate(nr) if v.strip().replace(',','')==str(expected)]
    if not columns:continue # 2013 national class table lacks grade columns.
    assert len(columns)==1,(year,stage,metric,columns)
    col=columns[0]
    for category in ['全国','城区','镇区','乡村']:
        raw=[nr] if category=='全国' else [r for r in table if r and ''.join(r[0].split()).startswith(category) and len(r)>col and r[col].strip().replace(',','').isdigit()]
        assert len(raw)==1,(year,stage,metric,category)
        value=int(raw[0][col].replace(',',''))
        lookup[year,stage,category][metric+'_grade1']=value
        extra.append({'year':year,'stage':stage,'category':category,'metric':metric+'_grade1','value':value,'column_index':col,'raw_value':raw[0][col],'source':cell['source'],'path':cell['path']})
    diff=sum(lookup[year,stage,c][metric+'_grade1'] for c in ['城区','镇区','乡村'])-expected
    extra_checks.append({'year':year,'stage':stage,'metric':metric+'_grade1','difference':diff})
    assert diff==0
annual=[];grade_changes=[];decomp=[];endpoints=[]
categories=['城区','镇区','乡村']
for r in rows:
    y,s,c=r['year'],r['stage'],r['category'];n=lookup[y,s,'全国']
    for m in ['students','teachers','classes']:
        r[m+'_share_pct']=100*r[m]/n[m] if r[m] is not None and n[m] else None
    if r['teachers']:r['teachers_per_100_students']=100*r['teachers']/r['students']
    r['classes_per_100_students']=100*r['classes']/r['students']
    r['students_per_class']=r['students']/r['classes']
    if y==2013:continue
    p=lookup[y-1,s,c];pn=lookup[y-1,s,'全国']
    a={'year':y,'stage':s,'category':c}
    for m in ['students','teachers','classes']:
        if r[m] is None or p[m] is None:continue
        a[m+'_change']=r[m]-p[m]
        a[m+'_growth_pct']=100*(r[m]/p[m]-1)
        a[m+'_contribution_pp']=100*(r[m]-p[m])/pn[m]
        a[m+'_share_change_pp']=100*r[m]/n[m]-100*p[m]/pn[m]
    annual.append(a)
    for m in ['students','classes']:
        f=m+'_grade1'
        if f not in r or f not in p:continue
        grade_changes.append({'year':y,'stage':s,'category':c,'metric':m,'total_growth_pct':100*(r[m]/p[m]-1),'grade1_growth_pct':100*(r[f]/p[f]-1),'grade1_contribution_pp':100*(r[f]-p[f])/p[m],'remainder_growth_pct':100*((r[m]-r[f])/(p[m]-p[f])-1),'remainder_contribution_pp':100*((r[m]-r[f])-(p[m]-p[f]))/p[m]})
for s in ['primary','junior']:
    for end in range(2014,2025):
        begin=end-1
        for metric in ['teachers','classes']:
            if any(lookup[y,s,c][metric] is None for y in [begin,end] for c in categories):continue
            within=between=0
            for c in categories:
                a,b=lookup[begin,s,c],lookup[end,s,c];na,nb=lookup[begin,s,'全国'],lookup[end,s,'全国']
                wa,wb=a['students']/na['students'],b['students']/nb['students']
                ra,rb=100*a[metric]/a['students'],100*b[metric]/b['students']
                w=(wa+wb)/2*(rb-ra);t=(ra+rb)/2*(wb-wa)
                within+=w;between+=t
                decomp.append({'year':end,'stage':s,'metric':metric,'category':c,'within_category_component':w,'student_share_component':t,'combined_component':w+t,'units':metric+' per 100 students'})
            a,b=lookup[begin,s,'全国'],lookup[end,s,'全国']
            delta=100*b[metric]/b['students']-100*a[metric]/a['students']
            assert abs(delta-within-between)<1e-12
            decomp.append({'year':end,'stage':s,'metric':metric,'category':'全国','within_category_component':within,'student_share_component':between,'combined_component':delta,'units':metric+' per 100 students'})
    for begin,end in [(2013,2024),(2018,2024),(2018,2023),(2023,2024)]:
        for c in ['全国']+categories:
            a,b=lookup[begin,s,c],lookup[end,s,c]
            for m in ['students','teachers','classes']:
                if a[m] is None or b[m] is None:continue
                endpoints.append({'begin':begin,'end':end,'stage':s,'category':c,'metric':m,'begin_value':a[m],'end_value':b[m],'change':b[m]-a[m],'growth_pct':100*(b[m]/a[m]-1),'begin_share_pct':100*a[m]/lookup[begin,s,'全国'][m],'end_share_pct':100*b[m]/lookup[end,s,'全国'][m]})
contribution_checks=[]
for y in range(2014,2025):
    for s in ['primary','junior']:
        for m in ['students','teachers','classes']:
            selected=[r for r in annual if r['year']==y and r['stage']==s and r['category'] in categories]
            if any(m+'_contribution_pp' not in r for r in selected):continue
            n=next(r for r in annual if r['year']==y and r['stage']==s and r['category']=='全国')
            err=sum(r[m+'_contribution_pp'] for r in selected)-n[m+'_growth_pct']
            contribution_checks.append({'year':y,'stage':s,'metric':m,'difference_pp':err})
            assert abs(err)<1e-12
save_csv(ROOT/'data/national_urban_rural_enriched.csv',rows)
save_csv(ROOT/'data/urban_grade1_cells.csv',extra)
save_csv(ROOT/'data/urban_grade1_checks.csv',extra_checks)
save_csv(ROOT/'data/urban_annual_changes.csv',annual)
save_csv(ROOT/'data/urban_grade_contributions.csv',grade_changes)
save_csv(ROOT/'data/urban_ratio_decomposition.csv',decomp)
save_csv(ROOT/'data/urban_endpoint_changes.csv',endpoints)
save_csv(ROOT/'data/urban_contribution_checks.csv',contribution_checks)
summary={'latest':[r for r in annual if r['year']==2024],'latest_grade':[r for r in grade_changes if r['year']==2024],'latest_ratio':[r for r in decomp if r['year']==2024 and r['category']=='全国'],'grade_checks':len(extra_checks),'contribution_checks':len(contribution_checks),'maximum_contribution_error_pp':max(abs(r['difference_pp']) for r in contribution_checks),'status':'Descriptive arithmetic only; no causal adjustment, migration, efficiency or financing inference.'}
(ROOT/'data/urban_analysis_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
