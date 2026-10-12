"""Long-history regional descriptions and targeted cross-stage diagnostics."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import json,re,math,sys,hashlib
import pandas as pd
import numpy as np
from build_thirty_year_history import ROOT,OUT,STUDENTS,FIN,EVIDENCE
from exploratory_panel_stats import fe_fit,wild_t,point
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')

def main():
    st=pd.read_csv(STUDENTS,keep_default_na=False);students={(int(r.data_year),r.province,r.stage):float(r.adjudicated_value) for r in st.itertuples(index=False)}
    f=pd.read_csv(FIN,keep_default_na=False);evidence={e['evidence_id']:e for e in json.loads(EVIDENCE.read_text(encoding='utf8'))}
    f=f[(f.school_scope=='local_affiliation')&(f.province!='全国')&f.numeric_status.str.startswith('accepted')].copy()
    f=f[f.evidence_id.map(lambda i:bool(re.match(r'^4[-—_ ]',evidence[i]['table'].replace('\\','/').split('/')[-1])))]
    ix={(int(r.year),r.province,r.stage):r for r in f.itertuples(index=False)}
    supp=pd.read_csv(ROOT/'research/data/长期财政数据建设_20261010/supplement_original_candidates.csv',keep_default_na=False)
    cpi={(int(r.data_year),r.province):float(r.raw_value) for r in supp.itertuples(index=False) if r.metric=='CPI_yoy' and r.raw_value}
    rv=pd.read_csv(ROOT/'research/data/财政收入补核_20261010/R_province_year_numeric_panel_with_summaries.csv',keep_default_na=False)
    rev={(int(r.year),r.province):float(r.R_adjudicated_yi) for r in rv.itertuples(index=False) if r.R_adjudicated_yi}
    rows=[]
    for (y,p,stage),a in ix.items():
        b=ix.get((y-1,p,stage))
        if not b or y==2007 or (p=='四川' and y in [1997,1998]) or (y,p) not in cpi:continue
        key=(y,p,stage);prior=(y-1,p,stage);prior2=(y-2,p,stage)
        if key not in students or prior not in students:continue
        ds=math.log(students[key]/students[prior]);pi=math.log(cpi[(y,p)]/100)
        dp=math.log(float(a.P)/float(b.P))-pi;dc=math.log(float(a.C)/float(b.C))-pi
        z=max(0,-(math.log(rev[(y,p)]/rev[(y-1,p)])-pi)) if (y,p) in rev and (y-1,p) in rev else None
        label='1996_2006_old' if y<=2006 else '2008_2015_new' if y<=2015 else '2016_2023_new' if y<=2023 else '2024_terminal_pending'
        rows.append(dict(year=y,province=p,stage=stage,period=label,dS=ds,dP_real=dp,dC_real=dc,D=dc-dp,shrink2=ds<0 and prior2 in students and students[prior]<students[prior2] and not(p=='四川' and y in [1998,1999]),Z=z,finance_scope='local_affiliation',student_scope='regional_all_organizers_context; not certified funded-population match',model_scope_approved=False))
    regional=pd.DataFrame(rows).sort_values(['stage','province','year']);regional.to_csv(OUT/'segmented_local_finance_changes.csv',index=False,encoding='utf-8-sig')
    descriptive=[]
    for (period,stage),s in regional.groupby(['period','stage']):
        t=s[s.shrink2]
        descriptive.append(dict(period=period,stage=stage,all_valid_finance_edges=len(s),sustained_student_decline_edges=len(t),median_P_real_pct=100*np.expm1(t.dP_real).median(),median_C_real_pct=100*np.expm1(t.dC_real).median(),mean_D_logpoints=100*t.D.mean(),C_real_decline=int((t.dC_real<0).sum()),R_available=int(t.Z.notna().sum()),R_contraction=int((t.Z>0).sum()),interpretation='descriptive regional student context; same-affiliation finance within each segment'))
    pd.DataFrame(descriptive).to_csv(OUT/'segmented_local_finance_descriptions.csv',index=False,encoding='utf-8-sig')
    targets=[];family=[];frames={}
    for stage,folder in [('primary','小学探索分析_20261010'),('junior','初中探索分析_20261010')]:
        path=ROOT/'research/data'/folder
        data=pd.read_csv(path/f'{stage}_annual_changes.csv');frames[stage]=data
        data['Z_post']=data.Z*data.post;data['dS_post']=data.dS*data.post
        result=pd.read_csv(path/'exploratory_FE_results.csv')
        for h,contrast in [('H1','Z'),('H2','post_minus_pre')]:
            a=result[(result.specification=='main_two_year')&(result.hypothesis==h)&(result.contrast==contrast)].iloc[0]
            family.append(dict(stage=stage,hypothesis=h,n=int(a.n),coefficient=a.coefficient,wild_p=a.wild_restricted_p,CI_low=a.WCR_95_CI_low,CI_high=a.WCR_95_CI_high,CI_search_boundary=bool(a.WCR_search_boundary_accepted),pre_contractions=int(a.pre_positive_Z),post_contractions=int(a.post_positive_Z)))
        for label,sub in [('exclude_2015_R_reclassification',data[data.year!=2015]),('exclude_2013_2014_type_edges',data[~data.year.isin([2013,2014])])]:
            if stage=='primary' and label=='exclude_2013_2014_type_edges':continue
            sub=sub[sub.shrink2]
            for h,y,x,c in [('H1','D',['Z','dS'],[1,0]),('H2','dC_real',['Z','dS','Z_post','dS_post'],[0,0,1,0])]:
                fit=fe_fit(sub,y,x)
                targets.append(dict(stage=stage,specification=label,hypothesis=h,n=len(sub),**point(fit,c),interpretation='targeted sensitivity; point and CR1 SE only'))
        if stage=='junior':
            recpath=path/'analysis_receipt.json';rec=json.loads(recpath.read_text(encoding='utf8'));rec['stage']='junior';rec['H1_exploratory']=rec.pop('H1_primary_exploratory',rec.get('H1_exploratory',True));recpath.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf8')
    p=np.array([r['wild_p'] for r in family]);order=np.argsort(p);adjust=np.maximum.accumulate(np.array([min(1,(4-i)*p[j]) for i,j in enumerate(order)]))
    for i,j in enumerate(order):family[j]['Holm_four_exploratory_p']=float(adjust[i])
    pd.DataFrame(family).to_csv(OUT/'four_exploratory_hypotheses.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(targets).to_csv(OUT/'targeted_scope_sensitivities.csv',index=False,encoding='utf-8-sig')
    # Paired school-stage contrast on the identical province-year population.
    pair=frames['primary'].merge(frames['junior'],on=['year','province'],suffixes=('_primary','_junior'))
    pair=pair[pair.shrink2_primary & pair.shrink2_junior].copy()
    pair['D_difference']=pair.D_junior-pair.D_primary;pair['Z']=pair.Z_primary
    assert np.allclose(pair.Z_primary,pair.Z_junior)
    fit=fe_fit(pair,'D_difference',['Z','dS_primary','dS_junior'])
    stats=wild_t(fit,[1,0,0],B=9999,seed=20261041)
    pd.DataFrame([dict(specification='paired_both_stages_sustained_decline',n=len(pair),provinces=fit['G'],**stats)]).to_csv(OUT/'paired_stage_H1_difference.csv',index=False,encoding='utf-8-sig')
    pair.to_csv(OUT/'paired_stage_common_sample.csv',index=False,encoding='utf-8-sig')
    print(pd.DataFrame(descriptive).to_string(index=False));print(pd.DataFrame(family).to_string(index=False));print(pd.DataFrame(targets).to_string(index=False));print('PAIRED',len(pair),stats)

if __name__=='__main__':main()
