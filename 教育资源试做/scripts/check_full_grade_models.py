"""Check whether Grade-1 collapse hides grade contrasts, using complete cells only."""
import csv,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'
def load(n):return list(csv.DictReader(open(DATA/n,encoding='utf-8-sig')))
def write(n,rs):
    with open(DATA/n,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rs for k in r)));w.writeheader();w.writerows(rs)
inputs=load('grade_structure_model_inputs.csv');details=load('grade_detailed_contributions.csv')
lookup={(r['stage'],r['province'],int(r['year']),r['metric']):r for r in details}
complete=[];exclusions=[]
for r in inputs:
    stage,p,t=r['stage'],r['province'],int(r['year']);count=6 if stage=='primary' else 4
    missing=[(year,i) for year in [t,t-1] for i in range(1,count+1) if lookup[stage,p,year,'students_grade'+str(i)]['contribution_pp']=='']
    if missing:
        exclusions.append({'stage':stage,'province':p,'year':t,'missing_grade_contributions':json.dumps(missing)})
        continue
    out={**r}
    for key in ['students_change_pct','students_lag_change_pct','teachers_change_pct','classes_change_pct']:out[key]=float(out[key])
    out['year']=t
    for i in range(1,count+1):
        out['current_grade'+str(i)+'_contribution_pp']=float(lookup[stage,p,t,'students_grade'+str(i)]['contribution_pp'])
        out['previous_grade'+str(i)+'_contribution_pp']=float(lookup[stage,p,t-1,'students_grade'+str(i)]['contribution_pp'])
    assert abs(sum(out['current_grade'+str(i)+'_contribution_pp'] for i in range(1,count+1))-out['students_change_pct'])<1e-10
    complete.append(out)
write('full_grade_model_inputs.csv',complete);write('full_grade_model_exclusions.csv',exclusions)
models=[];increments=[]
for stage in ['primary','junior']:
    count=6 if stage=='primary' else 4
    stage_rows=[r for r in complete if r['stage']==stage]
    scenarios=[('main_2015_2024',stage_rows),('exclude_2024',[r for r in stage_rows if r['year']<=2023])]
    scenarios += [('drop_province:'+p,[r for r in stage_rows if r['province']!=p]) for p in sorted({r['province'] for r in stage_rows})]
    for scenario,rr in scenarios:
        ps=sorted({r['province'] for r in rr});ys=sorted({r['year'] for r in rr})
        fe=np.array([[1]+[int(r['province']==p) for p in ps[1:]]+[int(r['year']==t) for t in ys[1:]] for r in rr],dtype=float)
        basefields=['students_change_pct','students_lag_change_pct']
        # Omit final grade as reference: total change equals sum of grade contributions.
        allfields=basefields+[period+'_grade'+str(i)+'_contribution_pp' for period in ['current','previous'] for i in range(1,count)]
        for target in ['teachers','classes']:
            y=np.array([r[target+'_change_pct'] for r in rr])
            fe_coef,_,fe_rank,_=np.linalg.lstsq(fe,y,rcond=None)
            fe_err=y-fe@fe_coef;fe_sse=float(fe_err@fe_err)
            results=[]
            for name,fields in [('total_only',basefields),('full_grade_added',allfields)]:
                x=np.column_stack([fe,np.array([[r[f] for f in fields] for r in rr])])
                coef,_,rank,singular=np.linalg.lstsq(x,y,rcond=None)
                assert rank==x.shape[1]
                err=y-x@coef;sse=float(err@err);df=len(rr)-rank
                assert max(abs(x.T@err))<1e-7
                raw_features=np.array([[r[f] for f in fields] for r in rr])
                fe_projection=np.linalg.lstsq(fe,raw_features,rcond=None)[0]
                within_features=raw_features-fe@fe_projection
                corr=np.corrcoef(within_features,rowvar=False)
                upper=np.triu(np.abs(corr),k=1);i,j=np.unravel_index(np.argmax(upper),upper.shape)
                result={'stage':stage,'resource':target,'scenario':scenario,'model':name,'n':len(rr),'provinces':len(ps),
                        'first_year':min(ys),'last_year':max(ys),'residual_df':int(df),'feature_count':len(fields),
                        'within_r_squared':1-sse/fe_sse,'within_adjusted_r_squared':1-(sse/df)/(fe_sse/(len(rr)-fe_rank)),
                        'full_design_condition_number':float(singular[0]/singular[-1]),'reference_grade':count,
                        'max_feature_abs_correlation_after_FE':float(upper[i,j]),'most_correlated_features':fields[i]+' | '+fields[j],
                        'grade_coefficients_json':json.dumps({f:float(v) for f,v in zip(fields,coef[fe.shape[1]:])})}
                results.append(result);models.append(result)
            increments.append({'stage':stage,'resource':target,'scenario':scenario,'n':len(rr),'provinces':len(ps),
                               'delta_within_r_squared':results[1]['within_r_squared']-results[0]['within_r_squared'],
                               'delta_within_adjusted_r_squared':results[1]['within_adjusted_r_squared']-results[0]['within_adjusted_r_squared']})
write('full_grade_models.csv',[r for r in models if not r['scenario'].startswith('drop_province:')])
write('full_grade_model_increment.csv',[r for r in increments if not r['scenario'].startswith('drop_province:')])
write('full_grade_model_influence.csv',[r for r in models if r['scenario'].startswith('drop_province:')])
write('full_grade_increment_influence.csv',[r for r in increments if r['scenario'].startswith('drop_province:')])
(DATA/'full_grade_model_validation.json').write_text(json.dumps({'included_rows':len(complete),'excluded_rows':len(exclusions),'missing_cells_imputed':0,
  'models':len(models),'checks':['Current grade contributions sum to total student growth','Identical complete rows in baseline/extended models',
      'Explicit province/year dummies used for unbalanced sample, not balanced-panel shortcut','Full design rank and least-squares equations verified'],
  'limits':['Complete-cell sample selects province/years; not identical to main 31-province sample',
      'Extra in-sample fit is not out-of-sample prediction or causal effect','Last grade omitted as reference to avoid deterministic collinearity'],
  'main_increments':[r for r in increments if not r['scenario'].startswith('drop_province:')]},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'included':len(complete),'excluded':len(exclusions),'models':len(models),'increments':[r for r in increments if not r['scenario'].startswith('drop_province:')]},ensure_ascii=False,indent=2))
