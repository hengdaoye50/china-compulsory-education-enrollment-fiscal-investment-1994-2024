"""Cross-check closed-form two-way demeaning with explicit-dummy least squares."""
import csv,json,math,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'
raw=list(csv.DictReader(open(DATA/'education_resource_panel.csv',encoding='utf-8-sig')))
levels={(r['stage'],r['province'],int(r['year'])):r for r in raw}
models=list(csv.DictReader(open(DATA/'resource_timing_models.csv',encoding='utf-8-sig')))
checks=[]
for model in models:
    stage,resource=model['stage'],model['resource']
    years=list(range(int(model['first_year']),int(model['last_year'])+1))
    provinces=sorted({r['province'] for r in raw if r['province']!='全国'})
    x=[];y=[]
    # Recompute directly from the saved levels; do not use diagnostic input rows
    # or the diagnostic model's transformation/solver.
    for province in provinces:
        for year in years:
            current=levels[stage,province,year];previous=levels[stage,province,year-1];earlier=levels[stage,province,year-2]
            row=[1.,100*(math.log(float(current['students']))-math.log(float(previous['students']))),
                 100*(math.log(float(previous['students']))-math.log(float(earlier['students'])))]
            row += [float(province==p) for p in provinces[1:]]
            row += [float(year==t) for t in years[1:]]
            x.append(row)
            y.append(100*(math.log(float(current[resource]))-math.log(float(previous[resource]))))
    x=np.asarray(x);y=np.asarray(y)
    coef,_,rank,_=np.linalg.lstsq(x,y,rcond=None)
    assert rank==x.shape[1]
    delta=max(abs(coef[1]-float(model['current_student_coef'])),abs(coef[2]-float(model['previous_student_coef'])))
    assert delta<1e-10
    checks.append({'stage':stage,'resource':resource,'scenario':model['scenario'],'n':len(y),'design_columns':x.shape[1],
                   'matrix_rank':int(rank),'max_coefficient_difference':delta,'pass':True})
audit=json.loads((DATA/'analysis_diagnostics_validation.json').read_text(encoding='utf-8'))
audit['independent_calculation_check']={'method':'NumPy explicit province/year dummies least squares; inputs recalculated directly from raw levels','model_count':len(checks),'max_coefficient_difference':max(c['max_coefficient_difference'] for c in checks),'checks':checks}
# Report-layout checks belong to the separate local report workflow.
(DATA/'analysis_diagnostics_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'{len(checks)} explicit-dummy model checks passed; max difference {audit["independent_calculation_check"]["max_coefficient_difference"]:.3g}.')
