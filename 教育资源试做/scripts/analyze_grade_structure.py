"""Grade contributions and incremental within-panel association; no charts."""
import csv,json,math,statistics,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'
def load(n):return list(csv.DictReader(open(DATA/n,encoding='utf-8-sig')))
def write(n,rs):
    with open(DATA/n,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rs for k in r)));w.writeheader();w.writerows(rs)
grades={(r['stage'],r['province'],int(r['year'])):r for r in load('grade_structure_panel.csv')}
levels={(r['stage'],r['province'],int(r['year'])):r for r in load('education_resource_panel.csv')}
contributions=[];detailed=[]
for key,r in sorted(grades.items()):
    stage,province,year=key
    if year==2013:continue
    prev=grades[stage,province,year-1]
    row={'stage':stage,'province':province,'year':year}
    for kind in ['students','classes']:
        total=float(r[kind+'_total']);base=float(prev[kind+'_total'])
        first=float(r[kind+'_grade1']);oldfirst=float(prev[kind+'_grade1'])
        row[kind+'_change_pct']=100*(total-base)/base
        row[kind+'_first_grade_contribution_pp']=100*(first-oldfirst)/base
        row[kind+'_remainder_contribution_pp']=100*((total-first)-(base-oldfirst))/base
        assert abs(row[kind+'_change_pct']-row[kind+'_first_grade_contribution_pp']-row[kind+'_remainder_contribution_pp'])<1e-10
        row[kind+'_first_grade_previous_share_pct']=100*oldfirst/base
        row[kind+'_source']=r[kind+'_source'];row[kind+'_previous_source']=prev[kind+'_source']
        count=6 if stage=='primary' else 4
        fields=[kind+'_grade'+str(i) for i in range(1,count+1)]
        if kind=='classes' and stage=='primary':fields.append('classes_multiple_grade')
        complete=all(r[f]!='' and prev[f]!='' for f in fields)
        for field in fields:
            missing=r[field]=='' or prev[field]==''
            detailed.append({'stage':stage,'province':province,'year':year,'metric':field,'current':r[field],
                             'previous':prev[field],'previous_total':base,'contribution_pp':None if missing else 100*(float(r[field])-float(prev[field]))/base,
                             'all_grade_fields_complete':complete,'source':r[kind+'_source'],'previous_source':prev[kind+'_source']})
        if complete:
            assert abs(sum(100*(float(r[f])-float(prev[f]))/base for f in fields)-row[kind+'_change_pct'])<1e-10
        row[kind+'_all_grades_complete']=complete
    a,b=levels[key],levels[stage,province,year-1]
    row['teachers_change_pct']=100*(float(a['teachers'])-float(b['teachers']))/float(b['teachers'])
    row['teachers_source']=a['teachers_source'];row['teachers_previous_source']=b['teachers_source']
    # Grade 1 students are not entrants; retain both and compare neither as proxy.
    row['entrants']=int(a['entrants']);row['students_grade1']=int(r['students_grade1'])
    contributions.append(row)
write('grade_contributions.csv',contributions);write('grade_detailed_contributions.csv',detailed)
look={(r['stage'],r['province'],r['year']):r for r in contributions}
inputs=[]
for r in contributions:
    if r['province']=='全国' or r['year']<2015:continue
    prev=look[r['stage'],r['province'],r['year']-1]
    inputs.append({**r,'students_lag_change_pct':prev['students_change_pct'],
                   'students_lag_first_grade_contribution_pp':prev['students_first_grade_contribution_pp']})
assert len(inputs)==620
write('grade_structure_model_inputs.csv',inputs)
features=['students_change_pct','students_lag_change_pct','students_first_grade_contribution_pp','students_lag_first_grade_contribution_pp']
def within(rs,field):
    overall=statistics.mean(r[field] for r in rs)
    pm={p:statistics.mean(r[field] for r in rs if r['province']==p) for p in {r['province'] for r in rs}}
    ym={t:statistics.mean(r[field] for r in rs if r['year']==t) for t in {r['year'] for r in rs}}
    return np.array([r[field]-pm[r['province']]-ym[r['year']]+overall for r in rs])
def fit(rs,target,scenario,extended):
    ps=sorted({r['province'] for r in rs});ys=sorted({r['year'] for r in rs})
    assert len(rs)==len(ps)*len(ys)
    used=features if extended else features[:2]
    x=np.column_stack([within(rs,f) for f in used]);y=within(rs,target+'_change_pct')
    beta,_,rank,singular=np.linalg.lstsq(x,y,rcond=None)
    assert rank==len(used)
    err=y-x@beta;sse=float(err@err);sst=float(y@y)
    fe_df=len(ps)+len(ys)-1;df=len(rs)-fe_df-len(used)
    # Adjustment is relative to the FE-only residual variance, not total levels.
    out={'stage':rs[0]['stage'],'resource':target,'scenario':scenario,'model':'first_grade_added' if extended else 'total_only',
         'n':len(rs),'provinces':len(ps),'first_year':min(ys),'last_year':max(ys),'feature_count':len(used),'residual_df':df,
         'within_r_squared':1-sse/sst,'within_adjusted_r_squared':1-(sse/df)/(sst/(len(rs)-fe_df)),
         'condition_number':float(singular[0]/singular[-1])}
    for i,f in enumerate(features):out['coef_'+f]=float(beta[i]) if f in used else None
    # Distinct calculation: raw features plus explicit FE dummies, no demeaning.
    fullx=np.array([[1]+[r[f] for f in used]+[int(r['province']==p) for p in ps[1:]]+[int(r['year']==t) for t in ys[1:]] for r in rs],dtype=float)
    fullbeta,_,fullrank,_=np.linalg.lstsq(fullx,np.array([r[target+'_change_pct'] for r in rs]),rcond=None)
    assert fullrank==fullx.shape[1]
    delta=float(max(abs(fullbeta[1:1+len(used)]-beta)));assert delta<1e-10
    out['explicit_dummy_max_coef_difference']=delta
    return out
models=[];influence=[]
for stage in ['primary','junior']:
    rs=[r for r in inputs if r['stage']==stage]
    for target in ['teachers','classes']:
        samples=[('main_2015_2024',rs),('exclude_2024',[r for r in rs if r['year']<2024]),
                 ('2015_2019',[r for r in rs if r['year']<2020]),('2020_2024',[r for r in rs if r['year']>=2020])]
        for scenario,rr in samples:
            for extended in [False,True]:models.append(fit(rr,target,scenario,extended))
        for p in sorted({r['province'] for r in rs}):
            for extended in [False,True]:influence.append(fit([r for r in rs if r['province']!=p],target,'drop_province:'+p,extended))
write('grade_structure_models.csv',models);write('grade_structure_model_influence.csv',influence)
increments=[]
for collection,output in [(models,'grade_structure_model_increment.csv'),(influence,'grade_structure_increment_influence.csv')]:
    lookup={(r['stage'],r['resource'],r['scenario'],r['model']):r for r in collection}
    for r in collection:
        if r['model']!='first_grade_added':continue
        base=lookup[r['stage'],r['resource'],r['scenario'],'total_only']
        increments.append({'collection':output,'stage':r['stage'],'resource':r['resource'],'scenario':r['scenario'],'n':r['n'],
                           'delta_within_r_squared':r['within_r_squared']-base['within_r_squared'],
                           'delta_within_adjusted_r_squared':r['within_adjusted_r_squared']-base['within_adjusted_r_squared'],
                           'coef_first_grade_current':r['coef_students_first_grade_contribution_pp'],
                           'coef_first_grade_previous':r['coef_students_lag_first_grade_contribution_pp']})
    write(output,[r for r in increments if r['collection']==output])
coverage=[]
for stage in ['primary','junior']:
    rr=[r for r in contributions if r['stage']==stage and r['province']!='全国']
    coverage.append({'stage':stage,'annual_observations':len(rr),'first_vs_remainder_complete':len(rr),
                     'student_all_grade_change_complete':sum(r['students_all_grades_complete'] for r in rr),
                     'class_all_grade_change_complete':sum(r['classes_all_grades_complete'] for r in rr)})
write('grade_structure_analysis_coverage.csv',coverage)
audit={'inputs':[{'name':f,'sha256':hashlib.sha256((DATA/f).read_bytes()).hexdigest()} for f in ['grade_structure_panel.csv','education_resource_panel.csv']],
       'year_change_rows_including_national':len(contributions),'provincial_model_inputs':len(inputs),'models':len(models),'province_deletion_models':len(influence),
       'max_explicit_dummy_coef_difference':max(r['explicit_dummy_max_coef_difference'] for r in models+influence),
       'coverage':coverage,'checks':['Grade-1 + total-minus-grade-1 changes reconcile to total changes for every row',
             'All-grade decomposition reconciles where all required source cells present','No source blank filled with zero',
             'Baseline and extended models use identical rows, outcomes, rates and fixed effects',
             'Balanced samples, rank and explicit-dummy coefficient cross-checks pass'],
       'limits':['Arithmetic contributions are not causes.','The remainder is an aggregate subtraction, not imputation of missing grade cells.',
                 'Primary remainder classes include multiple-grade classes; no grade-specific class-size estimate.',
                 'Within R-squared improvement is in-sample, not predictive validation or causal mechanism identification.',
                 'Grade 1 is not entrants or age-specific population.']}
(DATA/'grade_structure_analysis_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'national_2024':[r for r in contributions if r['province']=='全国' and r['year']==2024],
                  'increments':[r for r in increments if r['collection']=='grade_structure_model_increment.csv'],
                  'validation':audit},ensure_ascii=False,indent=2))
