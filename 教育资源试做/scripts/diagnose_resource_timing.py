"""Round 31: complete leave-one-province diagnostics and residual descriptions.

Uses existing 16 specifications, including all three sensitivity windows.
Does not run a naive CD test on time-FE residuals or change old results.
"""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
import numpy as np
from infer_resource_timing import read, save, within, covariance, t_pvalue, t_critical, holm, PROTECTED, ROOT, DATA


def fingerprint():
    checks=[]
    for rel, expected in PROTECTED.items():
        actual=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
        assert actual==expected, rel
        checks.append({'path':rel,'sha256':actual,'unchanged':True})
    return checks


def fit(x,y,gn,tn,full_covariance_check=False):
    n=len(y);groups=np.repeat(np.arange(gn),tn);times=np.tile(np.arange(tn),gn)
    wx,wy=within(x,gn,tn),within(y,gn,tn)
    beta=np.linalg.lstsq(wx,wy,rcond=None)[0];e=wy-wx@beta
    full=np.column_stack([np.ones(n),x,np.eye(gn)[groups,1:],np.eye(tn)[times,1:]])
    fb,_,rank,_=np.linalg.lstsq(full,y,rcond=None)
    assert rank==gn+tn+1==full.shape[1]
    assert np.linalg.matrix_rank(wx)==2
    fe=y-full@fb
    bdelta=float(np.max(abs(beta-fb[1:3])));edelta=float(np.max(abs(e-fe)))
    assert bdelta<1e-9 and edelta<1e-9
    factor=gn/(gn-1)*(n-1)/(n-rank)
    cov=covariance(wx,e,groups,factor)
    assert np.linalg.eigvalsh(cov).min()>0
    vdelta=''
    if full_covariance_check:
        vcov=covariance(full,fe,groups,factor)[1:3,1:3]
        vdelta=float(np.max(abs(cov-vcov)));assert vdelta<1e-9
    check={'n':n,'provinces':gn,'years':tn,'full_design_rank':int(rank),'cr1_factor':factor,
           'max_coefficient_path_difference':bdelta,'max_residual_path_difference':edelta,
           'max_covariance_path_difference':vdelta,'passed':True}
    return beta,cov,e,wx,check


def outputs(common,b,cov,critical):
    coefs=[]
    for i,term in enumerate(['current_students','previous_students']):
        se=math.sqrt(cov[i,i]);p=t_pvalue(b[i]/se,common['provinces']-1)
        assert abs(p-t_pvalue(b[i]/se,common['provinces']-1,128))<1e-12
        coefs.append({**common,'term':term,'coefficient':float(b[i]),'cluster_se':se,
                      'ci95_low':float(b[i]-critical*se),'ci95_high':float(b[i]+critical*se),
                      'p_two_sided':p,'p_holm_main8':''})
    c=np.array([-1.,1.]);d=float(c@b);se=math.sqrt(float(c@cov@c))
    contrast={**common,'contrast':'previous_minus_current','difference':d,'cluster_se':se,
              'ci95_low':d-critical*se,'ci95_high':d+critical*se,
              'p_two_sided':t_pvalue(d/se,common['provinces']-1),'p_holm_main4':''}
    f=float(b@np.linalg.solve(cov,b))/2;df=common['provinces']-1
    joint={**common,'null':'current=previous=0','f_stat':f,'p_joint_f':(df/(df+2*f))**(df/2),'p_holm_main4':''}
    return coefs,contrast,joint


def main():
    initial_protection=fingerprint()
    input_names=['education_resource_panel.csv','resource_timing_models.csv',
                 'resource_timing_cluster_coefficients.csv','resource_timing_cluster_contrasts.csv','resource_timing_cluster_joint_tests.csv']
    initial_hashes={name:hashlib.sha256((DATA/name).read_bytes()).hexdigest() for name in input_names}
    levels={(r['stage'],r['province'],int(r['year'])):r for r in read('education_resource_panel.csv')}
    provinces=sorted({p for _,p,_ in levels if p!='全国'})
    specs=read('resource_timing_models.csv');assert len(specs)==16 and len(provinces)==31
    old_coefs=read(input_names[2]);old_contrasts=read(input_names[3]);old_joints=read(input_names[4])
    old_b={(r['stage'],r['resource'],r['scenario'],r['term']):float(r['coefficient']) for r in old_coefs}
    old_d={(r['stage'],r['resource'],r['scenario']):float(r['difference']) for r in old_contrasts}
    rows_c,rows_d,rows_j,checks,residual_rows,pair_rows,residual_summary,leverage_rows=[],[],[],[],[],[],[],[]
    critical=t_critical(29)
    for model in specs:
        stage,resource,scenario=[model[k] for k in ['stage','resource','scenario']]
        years=list(range(int(model['first_year']),int(model['last_year'])+1));tn=len(years)
        x=[];y=[]
        for province in provinces:
            for year in years:
                now,prev,earlier=[levels[stage,province,year-d] for d in range(3)]
                x.append([100*math.log(float(now['students'])/float(prev['students'])),
                          100*math.log(float(prev['students'])/float(earlier['students']))])
                y.append(100*math.log(float(now[resource])/float(prev[resource])))
        x,y=np.array(x),np.array(y)
        base_b,base_cov,e,wx,baseline_check=fit(x,y,31,tn,True)
        key=(stage,resource,scenario)
        for i,term in enumerate(['current_students','previous_students']):
            assert abs(base_b[i]-old_b[(*key,term)])<1e-10
        common={'stage':stage,'resource':resource,'scenario':scenario,'first_year':years[0],'last_year':years[-1]}
        checks.append({**common,'omitted_province':'NONE',**baseline_check})
        matrix=e.reshape(31,tn)
        assert np.max(abs(matrix.sum(axis=0)))<1e-9
        assert np.max(abs(matrix.sum(axis=1)))<1e-9
        corr=np.corrcoef(matrix);assert np.all(np.isfinite(corr))
        assert np.max(abs(corr-corr.T))<1e-12
        pairs=[]
        for i,p in enumerate(provinces):
            for j in range(i+1,31):
                value=float(corr[i,j]);pairs.append(value)
                pair_rows.append({**common,'province_a':p,'province_b':provinces[j],'years':tn,'residual_correlation':value,'interpretation':'descriptive; estimated time-FE residuals; no independence p-value'})
        eig=np.linalg.eigvalsh(corr);rank=int(np.linalg.matrix_rank(corr,tol=1e-8))
        assert rank<=tn-1
        # Identity makes the effects of residual standardization inspectable.
        normalized=matrix/np.linalg.norm(matrix,axis=1,keepdims=True)
        identity=(float(np.sum(normalized,axis=0)@np.sum(normalized,axis=0))-31)/(31*30)
        assert abs(identity-np.mean(pairs))<1e-12
        residual_summary.append({**common,'provinces':31,'years':tn,'pairs':465,
            'mean_correlation':float(np.mean(pairs)),'median_absolute_correlation':float(np.median(abs(np.array(pairs)))),
            'p90_absolute_correlation':float(np.quantile(abs(np.array(pairs)),.9)),
            'minimum_correlation':min(pairs),'maximum_correlation':max(pairs),
            'correlation_matrix_rank':rank,'maximum_rank_from_time_demeaning':tn-1,
            'largest_eigenvalue_share':float(eig[-1]/31),'rank_based_minimum_largest_share':1/(tn-1),
            'max_year_residual_sum':float(np.max(abs(matrix.sum(axis=0)))),
            'mean_correlation_identity_difference':abs(identity-float(np.mean(pairs))),
            'independence_status':'not established; short T and time-FE constraints; no naive CD test'})
        bread=np.linalg.inv(wx.T@wx)
        for i,province in enumerate(provinces):
            sl=slice(i*tn,(i+1)*tn)
            leverage=float(np.trace(bread@(wx[sl].T@wx[sl])))
            score=bread@(wx[sl].T@e[sl])
            leverage_rows.append({**common,'province':province,'slope_design_trace':leverage,
                                  'current_slope_score_contribution':float(score[0]),
                                  'previous_slope_score_contribution':float(score[1]),
                                  'interpretation':'two-slope residualized design trace; not full cluster leverage'})
            for j,year in enumerate(years):
                residual_rows.append({**common,'province':province,'year':year,'residual_log_change_units':float(matrix[i,j])})
            keep=np.repeat(np.arange(31)!=i,tn)
            b,cov,_,_,check=fit(x[keep],y[keep],30,tn,scenario=='main_2015_2024')
            item={**common,'omitted_province':province,**check}
            checks.append(item)
            info={**common,'omitted_province':province,'n':len(y[keep]),'provinces':30,
                  'full_design_rank':check['full_design_rank'],'cluster_df':29,'cr1_factor':check['cr1_factor']}
            coefficients,contrast,joint=outputs(info,b,cov,critical)
            for row in coefficients:
                row['full_sample_coefficient']=old_b[(*key,row['term'])]
                row['change_from_full_sample']=row['coefficient']-row['full_sample_coefficient']
            contrast['full_sample_difference']=old_d[key]
            contrast['change_from_full_sample']=contrast['difference']-old_d[key]
            rows_c.extend(coefficients);rows_d.append(contrast);rows_j.append(joint)
        traces=[r['slope_design_trace'] for r in leverage_rows if (r['stage'],r['resource'],r['scenario'])==key]
        assert abs(sum(traces)-2)<1e-10
        print(stage,resource,scenario,'31 deletion fits passed',flush=True)
    for province in provinces:
        subset=[r for r in rows_c if r['omitted_province']==province and r['scenario']=='main_2015_2024'];assert len(subset)==8
        holm(subset,'p_two_sided','p_holm_main8')
        for rows,field in [(rows_d,'p_two_sided'),(rows_j,'p_joint_f')]:
            subset=[r for r in rows if r['omitted_province']==province and r['scenario']=='main_2015_2024'];assert len(subset)==4
            holm(subset,field,'p_holm_main4')
    summary=[]
    for collection,stat,term_key,pfield,holmfield in [(rows_c,'coefficient','term','p_two_sided','p_holm_main8'),(rows_d,'difference','contrast','p_two_sided','p_holm_main4')]:
        groups=defaultdict(list)
        for r in collection:groups[(r['stage'],r['resource'],r['scenario'],r[term_key])].append(r)
        for (stage,resource,scenario,term),rs in groups.items():
            lo=min(rs,key=lambda r:r[stat]);hi=max(rs,key=lambda r:r[stat]);influence=max(rs,key=lambda r:abs(r['change_from_full_sample']))
            summary.append({'stage':stage,'resource':resource,'scenario':scenario,'term':term,'deletions':31,
                'full_sample_estimate':rs[0]['full_sample_coefficient' if stat=='coefficient' else 'full_sample_difference'],
                'minimum_estimate':lo[stat],'minimum_when_omitted':lo['omitted_province'],
                'maximum_estimate':hi[stat],'maximum_when_omitted':hi['omitted_province'],
                'maximum_absolute_change':abs(influence['change_from_full_sample']),'most_influential_omission':influence['omitted_province'],
                'positive_estimates':sum(r[stat]>0 for r in rs),'negative_estimates':sum(r[stat]<0 for r in rs),
                'raw_p_min':min(r[pfield] for r in rs),'raw_p_max':max(r[pfield] for r in rs),
                'main_family_holm_p_min':min(r[holmfield] for r in rs) if scenario=='main_2015_2024' else '',
                'main_family_holm_p_max':max(r[holmfield] for r in rs) if scenario=='main_2015_2024' else '',
                'ci_contains_zero_count':sum(r['ci95_low']<=0<=r['ci95_high'] for r in rs),
                'interpretation':'complete deletion diagnostics; not 31 independent replications; no selection or across-deletion family correction'})
    assert len(rows_c)==992 and len(rows_d)==len(rows_j)==496 and len(summary)==48
    final_protection=fingerprint()
    for name,sha in initial_hashes.items():assert hashlib.sha256((DATA/name).read_bytes()).hexdigest()==sha
    for name,rows in [('coefficients',rows_c),('contrasts',rows_d),('joint_tests',rows_j),('summary',summary),('checks',checks),('residuals',residual_rows),('residual_pairs',pair_rows),('residual_summary',residual_summary),('slope_design',leverage_rows)]:
        save('resource_timing_diagnostics_'+name+'.csv',rows)
    audit={'date':'2026-10-08','round':31,'specifications':16,'leave_one_province_models':496,
           'coefficient_rows':992,'contrast_rows':496,'joint_rows':496,'residual_pairs':len(pair_rows),
           'checks':len(checks),'max_coefficient_path_difference':max(r['max_coefficient_path_difference'] for r in checks),
           'max_covariance_path_difference':max(r['max_covariance_path_difference'] for r in checks if r['max_covariance_path_difference']!=''),
           'cluster_inference':'CR1, full FE rank; 30 clusters and t(29)/F(2,29) in deletion fits',
           'multiplicity':'8 main slopes, 4 main differences, 4 main joint tests adjusted separately within each omitted-province setting; not across 31 settings',
           'residual_dependence':'descriptive only; no naive CD p-value, no certification of error independence',
           'exploratory':True,'preregistered':False,'causal':False,
           'protected_before':initial_protection,'protected_after':final_protection,'original_input_hashes_unchanged':initial_hashes,
           'technical_sources':['https://journals.sagepub.com/doi/10.1177/1536867X231212433','https://arxiv.org/abs/1810.03715',
                                'https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster.html']}
    (DATA/'resource_timing_diagnostics_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'models':496,'diagnostic_rows':len(summary),'checks':'passed'},ensure_ascii=False))


if __name__=='__main__':main()
