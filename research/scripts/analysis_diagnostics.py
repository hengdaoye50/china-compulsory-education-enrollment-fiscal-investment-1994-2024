"""Analysis only: pair composition/influence and balanced-panel timing diagnostics.

No charts, no financial-total reconstruction, no causal claims or significance tests.
"""
import csv,json,math,statistics,hashlib
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
def load(name):
    return list(csv.DictReader(open(DATA/name,encoding='utf-8-sig')))
def write(name,rs):
    with open(DATA/name,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def median(xs):return statistics.median(xs) if xs else None
raw=load('education_resource_panel.csv')
lookup={(r['stage'],r['province'],int(r['year'])):r for r in raw}
assert len(lookup)==len(raw)==768
obs=[]
for r in raw:
    year=int(r['year'])
    if r['province']=='全国' or year<2014:continue
    prev=lookup[r['stage'],r['province'],year-1]
    out={'stage':r['stage'],'province':r['province'],'year':year}
    for f in ['students','teachers','classes']:
        a,b=float(r[f]),float(prev[f]);assert a>0 and b>0
        out[f+'_pct']=100*(a-b)/b
        out[f+'_log_pct']=100*math.log(a/b)
        assert abs(out[f+'_pct']-float(r[f+'_growth_pct']))<1e-8
        out[f+'_source']=r[f+'_source']
        out[f+'_previous_source']=prev[f+'_source']
    obs.append(out)
bykey={(r['stage'],r['province'],r['year']):r for r in obs}
pairs=load('matched_pairs.csv')
for p in pairs:
    for k,v in p.items():
        if k.endswith('_pct') or k in ['growth_year','shrink_year','year_gap','magnitude_gap_pp']:p[k]=float(v)
    p['chronology']='growth_before_shrink' if p['growth_year']<p['shrink_year'] else 'shrink_before_growth'
    for f in ['students','teachers','classes']:
        # Equal-magnitude opposite movements have zero signed sum. This is a
        # descriptive statistic, not a time derivative or a causal effect.
        p[f+'_signed_sum_pp']=p['growth_'+f+'_pct']+p['shrink_'+f+'_pct']
        for phase in ['growth','shrink']:
            actual=bykey[p['stage'],p['province'],int(p[phase+'_year'])][f+'_pct']
            assert abs(actual-p[phase+'_'+f+'_pct'])<1e-8
def pair_summary(ps,stage,scenario):
    out=[]
    for f in ['students','teachers','classes']:
        vals=[p[f+'_signed_sum_pp'] for p in ps]
        grouped=defaultdict(list)
        for p in ps:grouped[p['province']].append(p[f+'_signed_sum_pp'])
        province_means=[statistics.mean(v) for v in grouped.values()]
        out.append({'stage':stage,'scenario':scenario,'resource':f,'pairs':len(ps),'provinces':len(grouped),
                    'growth_median_pct':median([p['growth_'+f+'_pct'] for p in ps]),
                    'shrink_median_pct':median([p['shrink_'+f+'_pct'] for p in ps]),
                    'pair_signed_sum_median_pp':median(vals),
                    'pair_signed_sum_mean_pp':statistics.mean(vals) if vals else None,
                    'province_equal_mean_signed_sum_pp':statistics.mean(province_means) if province_means else None,
                    'positive_pair_signed_sums':sum(v>0 for v in vals),
                    'negative_pair_signed_sums':sum(v<0 for v in vals)})
    return out
summary=[];influence=[];composition=[];coverage=[]
for stage in ['primary','junior']:
    ps=[p for p in pairs if p['stage']==stage]
    summary+=pair_summary(ps,stage,'main')
    for chronology in ['growth_before_shrink','shrink_before_growth']:
        summary+=pair_summary([p for p in ps if p['chronology']==chronology],stage,chronology)
    for province in sorted({p['province'] for p in ps}):
        influence+=pair_summary([p for p in ps if p['province']!=province],stage,'drop_province:'+province)
    for year in range(2014,2025):
        reduced=[p for p in ps if year not in [p['growth_year'],p['shrink_year']]]
        influence+=pair_summary(reduced,stage,'drop_year:'+str(year))
    selected={(p['province'],int(p[phase+'_year'])) for p in ps for phase in ['growth','shrink']}
    for phase,sign in [('growth',1),('shrink',-1)]:
        for year in range(2014,2025):
            eligible=[r for r in obs if r['stage']==stage and r['year']==year and sign*r['students_pct']>=1]
            matched=[r for r in eligible if (r['province'],r['year']) in selected]
            composition.append({'stage':stage,'phase':phase,'year':year,'eligible':len(eligible),'matched':len(matched)})
        eligible=[r for r in obs if r['stage']==stage and sign*r['students_pct']>=1]
        for subset,rr in [('eligible',eligible),('matched',[r for r in eligible if (r['province'],r['year']) in selected]),('unmatched',[r for r in eligible if (r['province'],r['year']) not in selected])]:
            coverage.append({'stage':stage,'phase':phase,'subset':subset,'n':len(rr),'provinces':len({r['province'] for r in rr}),
                             **{'median_'+f+'_pct':median([r[f+'_pct'] for r in rr]) for f in ['students','teachers','classes']}})
write('pair_diagnostics.csv',summary)
write('pair_influence.csv',influence)
write('pair_year_composition.csv',composition)
write('pair_selection_comparison.csv',coverage)
write('pair_signed_changes.csv',pairs)

# Balanced two-way demeaning is exact here: all 31 provinces share all years.
# y_it = province intercept + year intercept + b0*dlog(S_it)
#        + b1*dlog(S_i,t-1) + residual. Log changes measured in 100*ln units.
def demean(rs,field):
    grand=statistics.mean(r[field] for r in rs)
    pg=defaultdict(list);yg=defaultdict(list)
    for r in rs:pg[r['province']].append(r[field]);yg[r['year']].append(r[field])
    pm={k:statistics.mean(v) for k,v in pg.items()};ym={k:statistics.mean(v) for k,v in yg.items()}
    return [r[field]-pm[r['province']]-ym[r['year']]+grand for r in rs]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def fit(rs,resource,scenario):
    years={r['year'] for r in rs};provinces={r['province'] for r in rs}
    assert len(rs)==len(years)*len(provinces)
    assert len({(r['province'],r['year']) for r in rs})==len(rs)
    x=demean(rs,'students_log_pct');z=demean(rs,'students_lag_log_pct');y=demean(rs,resource+'_log_pct')
    xx,zz,xz=dot(x,x),dot(z,z),dot(x,z);det=xx*zz-xz*xz
    assert det>1e-9
    xy,zy=dot(x,y),dot(z,y)
    b0=(xy*zz-zy*xz)/det;b1=(zy*xx-xy*xz)/det
    e=[v-b0*a-b1*b for a,b,v in zip(x,z,y)]
    assert abs(dot(x,e))<1e-7 and abs(dot(z,e))<1e-7
    # Verify projection removes province and year means, and levels reconstruct.
    for v in [x,z,y]:
        for groupkey in ['province','year']:
            groups=defaultdict(list)
            for r,a in zip(rs,v):groups[r[groupkey]].append(a)
            assert max(abs(statistics.mean(a)) for a in groups.values())<1e-10
    return {'stage':rs[0]['stage'],'resource':resource,'scenario':scenario,'n':len(rs),'provinces':len(provinces),
            'first_year':min(years),'last_year':max(years),'current_student_coef':b0,'previous_student_coef':b1,
            'current_previous_student_correlation_after_FE':xz/math.sqrt(xx*zz),
            'within_r_squared':1-dot(e,e)/dot(y,y),'FE_normal_equation_max_error':max(abs(dot(x,e)),abs(dot(z,e)))}
timing=[]
for r in obs:
    if r['year']<2015:continue
    last=bykey[r['stage'],r['province'],r['year']-1]
    timing.append({**r,'students_lag_log_pct':last['students_log_pct'],'lag_students_source':last['students_source'],'lag_students_previous_source':last['students_previous_source']})
write('resource_timing_inputs.csv',timing)
models=[];model_influence=[]
for stage in ['primary','junior']:
    rs=[r for r in timing if r['stage']==stage]
    for resource in ['teachers','classes']:
        for scenario,rr in [('main_2015_2024',rs),('exclude_2024',[r for r in rs if r['year']<2024]),('before_2020',[r for r in rs if r['year']<2020]),('from_2020',[r for r in rs if r['year']>=2020])]:
            models.append(fit(rr,resource,scenario))
        for province in sorted({r['province'] for r in rs}):
            model_influence.append(fit([r for r in rs if r['province']!=province],resource,'drop_province:'+province))
write('resource_timing_models.csv',models)
write('resource_timing_influence.csv',model_influence)
# Direction transitions use one-period ahead resource observations, and disclose
# subsequent student changes rather than attributing those to the initial fall.
transitions=[]
for r in obs:
    if r['year']==2024 or abs(r['students_pct'])<1:continue
    nxt=bykey[r['stage'],r['province'],r['year']+1]
    transitions.append({'stage':r['stage'],'province':r['province'],'start_year':r['year'],
                        'initial_phase':'growth' if r['students_pct']>=1 else 'shrink',
                        'next_phase':'growth' if nxt['students_pct']>=1 else ('shrink' if nxt['students_pct']<=-1 else 'near_zero'),
                        **{'initial_'+f+'_pct':r[f+'_pct'] for f in ['students','teachers','classes']},
                        **{'next_'+f+'_pct':nxt[f+'_pct'] for f in ['students','teachers','classes']}})
write('resource_transitions.csv',transitions)
transition_summary=[]
for stage in ['primary','junior']:
    for initial in ['growth','shrink']:
        for nextphase in ['growth','shrink','near_zero']:
            rs=[r for r in transitions if r['stage']==stage and r['initial_phase']==initial and r['next_phase']==nextphase]
            transition_summary.append({'stage':stage,'initial_phase':initial,'next_phase':nextphase,'n':len(rs),
                **{prefix+f+'_median_pct':median([r[prefix+f+'_pct'] for r in rs]) for prefix in ['initial_','next_'] for f in ['students','teachers','classes']}})
write('resource_transition_summary.csv',transition_summary)
audit={'inputs':[{'name':n,'sha256':hashlib.sha256((DATA/n).read_bytes()).hexdigest()} for n in ['education_resource_panel.csv','matched_pairs.csv']],
       'observations':len(obs),'timing_observations':len(timing),'pairs':len(pairs),'influence_refits':len(model_influence),
       'checks':['No duplicate province-stage-year','All 682 annual growth values for each of 3 variables agree with stored panel',
                 'All pair values recomputed from original levels','All timing samples balanced',
                 'Demeaned province/year means zero and OLS normal equations verified for all fits'],
       'scope':'Descriptive diagnostics only. No causal effects, significance tests, chart updates or fiscal-total reconstruction.'}
(DATA/'analysis_diagnostics_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'observations':len(obs),'timing_observations':len(timing),'pairs':len(pairs),'models':len(models),'influence_refits':len(model_influence),'validation':'passed'},ensure_ascii=False))
