"""Retrospective held-out cell validation and provincial influence attribution.

No future forecasting, causal identification, model selection or chart changes.
"""
import csv,json,math,statistics,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'
PROVINCES=['北京','天津','河北','山西','内蒙古','辽宁','吉林','黑龙江','上海','江苏','浙江','安徽','福建','江西','山东','河南','湖北','湖南','广东','广西','海南','重庆','四川','贵州','云南','西藏','陕西','甘肃','青海','宁夏','新疆']
def load(n):return list(csv.DictReader(open(DATA/n,encoding='utf-8-sig')))
def write(n,rs):
    with open(DATA/n,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rs for k in r)));w.writeheader();w.writerows(rs)
rows=load('full_grade_model_inputs.csv')
for r in rows:
    r['year']=int(r['year'])
    for k,v in r.items():
        if v and (k.endswith('_pct') or k.endswith('_pp')):r[k]=float(v)
def fields(stage,model):
    basic=['students_change_pct','students_lag_change_pct']
    if model=='total_only':return basic
    if model=='first_grade_added':return basic+['students_first_grade_contribution_pp','students_lag_first_grade_contribution_pp']
    count=6 if stage=='primary' else 4
    return basic+[period+'_grade'+str(i)+'_contribution_pp' for period in ['current','previous'] for i in range(1,count)]
def design(rr,ps,ys,fs):
    return np.array([[1]+[int(r['province']==p) for p in ps[1:]]+[int(r['year']==t) for t in ys[1:]]+[r[f] for f in fs] for r in rr],dtype=float)
predictions=[];fold_checks=[];summary=[];province_errors=[]
scenarios=[('primary','main'),('junior','main'),('primary','without_tibet_diagnostic')]
for stage,scenario in scenarios:
    rr=[r for r in rows if r['stage']==stage and (scenario=='main' or r['province']!='西藏')]
    ps=[p for p in PROVINCES if any(r['province']==p for r in rr)];ys=sorted({r['year'] for r in rr})
    # Two deterministic partitions, fixed in advance. Each province's 10-year
    # interval is split into adjacent two-year blocks. Offsets spread held-out
    # blocks across provinces so each training set contains all province/year FE.
    for offset in [0,2]:
        split='block_offset_'+str(offset)
        assignment={(r['province'],r['year']):(((r['year']-2015)//2)+PROVINCES.index(r['province'])+offset*(PROVINCES.index(r['province'])%3))%5 for r in rr}
        assert all(0<=f<5 for f in assignment.values())
        for fold in range(5):
            train=[r for r in rr if assignment[r['province'],r['year']]!=fold]
            test=[r for r in rr if assignment[r['province'],r['year']]==fold]
            assert len(train)+len(test)==len(rr)
            assert {(r['province'],r['year']) for r in train}.isdisjoint({(r['province'],r['year']) for r in test})
            assert set(ps)=={r['province'] for r in train} and set(ys)=={r['year'] for r in train}
            for target in ['teachers','classes']:
                for model in ['total_only','first_grade_added','full_grade_added']:
                    fs=fields(stage,model)
                    x=design(train,ps,ys,fs);y=np.array([r[target+'_change_pct'] for r in train])
                    beta,_,rank,_=np.linalg.lstsq(x,y,rcond=None)
                    assert rank==x.shape[1]
                    xtest=design(test,ps,ys,fs);pred=xtest@beta
                    assert max(abs(x.T@(y-x@beta)))<1e-7
                    fold_checks.append({'stage':stage,'scenario':scenario,'split':split,'fold':fold,'resource':target,'model':model,
                                        'train_n':len(train),'test_n':len(test),'rank':int(rank),'columns':x.shape[1],'pass':True})
                    for r,v in zip(test,pred):
                        actual=r[target+'_change_pct']
                        predictions.append({'stage':stage,'scenario':scenario,'split':split,'fold':fold,'province':r['province'],'year':r['year'],
                            'resource':target,'model':model,'actual_change_pct':actual,'predicted_change_pct':float(v),
                            'error_pp':actual-float(v),'source':r[target+'_source'],'previous_source':r[target+'_previous_source']})
        for target in ['teachers','classes']:
            for model in ['total_only','first_grade_added','full_grade_added']:
                pp=[p for p in predictions if p['stage']==stage and p['scenario']==scenario and p['split']==split and p['resource']==target and p['model']==model]
                assert len(pp)==len(rr) and len({(p['province'],p['year']) for p in pp})==len(rr)
                perprovince=[]
                for province in ps:
                    vals=[p['error_pp'] for p in pp if p['province']==province]
                    rmse=math.sqrt(statistics.mean(v*v for v in vals));mae=statistics.mean(abs(v) for v in vals)
                    perprovince.append(statistics.mean(v*v for v in vals))
                    province_errors.append({'stage':stage,'scenario':scenario,'split':split,'resource':target,'model':model,'province':province,
                                            'n':len(vals),'rmse_pp':rmse,'mae_pp':mae})
                errs=[p['error_pp'] for p in pp]
                summary.append({'stage':stage,'scenario':scenario,'split':split,'resource':target,'model':model,'n':len(pp),
                                 'rmse_pp':math.sqrt(statistics.mean(v*v for v in errs)),'mae_pp':statistics.mean(abs(v) for v in errs),
                                 'province_equal_rmse_pp':math.sqrt(statistics.mean(perprovince))})
write('grade_holdout_predictions.csv',predictions);write('grade_holdout_fold_checks.csv',fold_checks)
write('grade_holdout_summary.csv',summary);write('grade_holdout_province_errors.csv',province_errors)
increments=[]
for r in summary:
    if r['model']=='total_only':continue
    b=next(x for x in summary if all(x[k]==r[k] for k in ['stage','scenario','split','resource']) and x['model']=='total_only')
    increments.append({**r,'baseline_rmse_pp':b['rmse_pp'],'baseline_mae_pp':b['mae_pp'],
                       'rmse_improvement_pct':100*(b['rmse_pp']-r['rmse_pp'])/b['rmse_pp'],
                       'mae_improvement_pct':100*(b['mae_pp']-r['mae_pp'])/b['mae_pp']})
write('grade_holdout_increment.csv',increments)
# Locate provincial allocation of in-sample SSE improvement and high leverage.
influence=[];leverage=[]
for stage in ['primary','junior']:
    rr=[r for r in rows if r['stage']==stage]
    ps=[p for p in PROVINCES if any(r['province']==p for r in rr)];ys=sorted({r['year'] for r in rr})
    for target in ['teachers','classes']:
        errors={};residuals={}
        for model in ['total_only','full_grade_added']:
            x=design(rr,ps,ys,fields(stage,model));y=np.array([r[target+'_change_pct'] for r in rr])
            beta,_,rank,_=np.linalg.lstsq(x,y,rcond=None)
            e=y-x@beta;errors[model]=e*e;residuals[model]=e
            if model=='full_grade_added':
                u,_,_=np.linalg.svd(x,full_matrices=False);h=np.sum(u[:,:rank]**2,axis=1)
                mse=float(e@e)/(len(rr)-rank)
                for r,hi,ei in zip(rr,h,e):
                    leverage.append({'stage':stage,'resource':target,'province':r['province'],'year':r['year'],
                                     'leverage':float(hi),'residual_pp':float(ei),'cooks_distance':float(ei*ei/(rank*mse)*hi/(1-hi)**2),
                                     'actual_change_pct':r[target+'_change_pct'],'source':r[target+'_source'],'previous_source':r[target+'_previous_source']})
        total_gain=float(sum(errors['total_only']-errors['full_grade_added']))
        assert total_gain>0
        allocated=0
        for p in ps:
            ids=[i for i,r in enumerate(rr) if r['province']==p]
            gain=float(sum(errors['total_only'][ids]-errors['full_grade_added'][ids]));allocated+=gain
            influence.append({'stage':stage,'resource':target,'province':p,'n':len(ids),
                'baseline_sse':float(sum(errors['total_only'][ids])),'extended_sse':float(sum(errors['full_grade_added'][ids])),
                'sse_reduction':gain,'share_of_total_sse_reduction_pct':100*gain/total_gain})
        assert abs(allocated-total_gain)<1e-8
write('grade_in_sample_province_gain.csv',influence);write('grade_model_leverage.csv',leverage)
audit={'input_file':'full_grade_model_inputs.csv','input_sha256':hashlib.sha256((DATA/'full_grade_model_inputs.csv').read_bytes()).hexdigest(),
       'heldout_fits':len(fold_checks),'heldout_prediction_rows':len(predictions),'splits':[0,2],
       'checks':['Training/held-out province-year keys disjoint in every fold','All province/year levels remain represented in training',
                 'All training designs full rank and normal equations checked','Each selected row predicted exactly once in each partition/model/outcome',
                 'Province allocation of in-sample SSE reductions reconciles'],
       'limits':['Retrospective held-out outcomes with observed contemporaneous/lagged students, not future forecasting',
                 'Training can include later years and adjacent cohort-related inputs; fold observations are not independent',
                 'Two fixed partitions are sensitivity diagnostics, not confidence intervals or a hyperparameter search',
                 'Without Tibet is explicitly a diagnostic, not replacement of the main sample',
                 'Fit and error comparisons are conditional associations, not causal identification']}
(DATA/'grade_deep_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'heldout_fits':len(fold_checks),'increments':increments,
    'tibet_sse_allocation':[r for r in influence if r['province']=='西藏'],'top_leverage':sorted(leverage,key=lambda r:r['leverage'],reverse=True)[:5]},ensure_ascii=False,indent=2))
