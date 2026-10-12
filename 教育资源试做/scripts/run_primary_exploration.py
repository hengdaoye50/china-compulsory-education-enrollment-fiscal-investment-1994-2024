"""Authorized exploratory primary-school analysis; original approvals remain False."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import csv,json,math,hashlib,sys
from pathlib import Path
import numpy as np
import pandas as pd
from exploratory_panel_stats import fe_fit,wild_t,point
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'教育资源试做/data/小学探索分析_20261010'
INPUT=ROOT/'教育资源试做/data/经费共同样本核查_20261010/SPCR_numeric_availability.csv'
SUPP=ROOT/'教育资源试做/data/长期财政数据建设_20261010/supplement_original_candidates.csv'

def main(stage='primary',output=None):
    OUT=Path(output) if output is not None else globals()['OUT']
    OUT.mkdir(exist_ok=True)
    df=pd.read_csv(INPUT,encoding='utf-8-sig',keep_default_na=False)
    df=df[df.stage==stage].copy()
    ix={(int(r.year),r.province):r for r in df.itertuples(index=False)}
    supp=pd.read_csv(SUPP,encoding='utf-8-sig',keep_default_na=False)
    cpi={(int(r.data_year),r.province):float(r.raw_value) for r in supp.itertuples(index=False) if r.metric=='CPI_yoy' and r.raw_value}
    rows=[]; exclusions=[]
    fields=['S_numeric','P_thousand_yuan','C_thousand_yuan','R_yi_yuan']
    for y in range(2008,2024):
        for p in sorted(df.province.unique()):
            a=ix[(y,p)]; prev=ix[(y-1,p)]
            missing=[f for f in fields if not getattr(a,f) or not getattr(prev,f)]
            cp=cpi.get((y,p))
            if missing or cp is None or cp<=0:
                exclusions.append(dict(year=y,province=p,reason='missing_adjacent_'+('|'.join(missing) or 'CPI')));continue
            d={f:math.log(float(getattr(a,f))/float(getattr(prev,f))) for f in fields}
            pi=math.log(cp/100); ds=d['S_numeric']; pnom=d['P_thousand_yuan']; cnom=d['C_thousand_yuan']; rnom=d['R_yi_yuan']
            two=ds<0 and float(ix[(y-1,p)].S_numeric)<float(ix[(y-2,p)].S_numeric)
            three=two and float(ix[(y-2,p)].S_numeric)<float(ix[(y-3,p)].S_numeric)
            rows.append(dict(year=y,province=p,dS=ds,dP_nominal=pnom,dC_nominal=cnom,dR_nominal=rnom,CPI_yoy=cp,dP_real=pnom-pi,dC_real=cnom-pi,dR_real=rnom-pi,D=cnom-pnom,Z=max(0,-(rnom-pi)),Z_nominal=max(0,-rnom),post=int(y>=2016),shrink1=ds<0,shrink2=two,shrink3=three,current_finance_sources=a.finance_source_ids,previous_finance_sources=prev.finance_source_ids,current_R_sources=a.R_source_ids,previous_R_sources=prev.R_source_ids,exploratory_analysis=True,model_scope_approved=False))
    data=pd.DataFrame(rows);data['Z_post']=data.Z*data.post;data['dS_post']=data.dS*data.post
    data.to_csv(OUT/f'{stage}_annual_changes.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(exclusions).to_csv(OUT/'excluded_adjacent_changes.csv',index=False,encoding='utf-8-sig')
    diagnostics=[]
    for rule in ['shrink1','shrink2','shrink3']:
        for post in [0,1]:
            s=data[data[rule] & (data.post==post)]; pos=s[s.Z>0]
            diagnostics.append(dict(rule=rule,period='2016_2023' if post else '2008_2015',n=len(s),provinces=s.province.nunique(),positive_Z_records=len(pos),positive_Z_provinces=pos.province.nunique(),positive_Z_years='|'.join(map(str,sorted(pos.year.unique()))),positive_Z_cases='|'.join(f'{r.year}:{r.province}' for r in pos.itertuples(index=False))))
    pd.DataFrame(diagnostics).to_csv(OUT/'identification_support.csv',index=False,encoding='utf-8-sig')
    desc=[]
    for rule in ['all','shrink1','shrink2','shrink3']:
        s=data if rule=='all' else data[data[rule]]
        for period in ['all','pre','post']:
            t=s if period=='all' else s[s.post==(period=='post')]
            for pressure in ['all','Z_positive','Z_zero']:
                u=t if pressure=='all' else t[t.Z>0] if pressure=='Z_positive' else t[t.Z==0]
                if not len(u):continue
                desc.append(dict(rule=rule,period=period,pressure=pressure,n=len(u),provinces=u.province.nunique(),mean_dS_logpoints=100*u.dS.mean(),median_P_real_pct=100*np.expm1(u.dP_real).median(),median_C_real_pct=100*np.expm1(u.dC_real).median(),mean_D_logpoints=100*u.D.mean(),C_real_decline=int((u.dC_real<0).sum()),P_real_decline=int((u.dP_real<0).sum()),C_relative_slower=int((u.D<0).sum())))
    pd.DataFrame(desc).to_csv(OUT/'descriptive_results.csv',index=False,encoding='utf-8-sig')
    main=data[data.shrink2].copy()
    models=[]; influence=[]; fits={}
    specifications=[('main_two_year',main),('one_year',data[data.shrink1]),('three_year',data[data.shrink3]),('exclude_2022',main[main.year!=2022]),('exclude_2020_2022',main[~main.year.isin([2020,2021,2022])]),('exclude_municipalities',main[~main.province.isin(['北京','天津','上海','重庆'])]),('exclude_Sichuan_Chongqing',main[~main.province.isin(['四川','重庆'])]),('start_2010',main[main.year>=2010]),('post_from_2017',main.copy()),('nominal_price_check',main.copy())]
    for spec,s in specifications:
        s=s.copy()
        if spec=='post_from_2017':s['post']=(s.year>=2017).astype(int);s['Z_post']=s.Z*s.post;s['dS_post']=s.dS*s.post
        nominal=spec=='nominal_price_check'
        if nominal:s['Z']=s.Z_nominal;s['Z_post']=s.Z*s.post
        for hypothesis,outcome,regs,contrasts in [('H1','D',['Z','dS'],{'Z':[1,0]}),('H2','dC_nominal' if nominal else 'dC_real',['Z','dS','Z_post','dS_post'],{'pre_Z':[1,0,0,0],'post_Z':[1,0,1,0],'post_minus_pre':[0,0,1,0]})]:
            try:
                fit=fe_fit(s,outcome,regs)
                if spec=='main_two_year':fits[hypothesis]=(s,fit)
                for name,c in contrasts.items():
                    inference=wild_t(fit,c,B=9999,seed=20261010+len(models)) if spec=='main_two_year' else point(fit,c)
                    record=dict(specification=spec,hypothesis=hypothesis,contrast=name,outcome=outcome,n=fit['n'],provinces=fit['G'],years=fit['years'],design_rank=fit['rank'],max_leverage=fit['max_leverage'],positive_Z_records=int((s.Z>0).sum()),pre_positive_Z=int(((s.Z>0)&(s.post==0)).sum()),post_positive_Z=int(((s.Z>0)&(s.post==1)).sum()),**inference)
                    record['effect_for_10pct_R_fall_logpoints']=record['coefficient']*(-math.log(.9))*100
                    record['interpretation']='exploratory_sparse_pre_period_H2_not_confirmatory' if hypothesis=='H2' else 'exploratory_scope_pending_not_confirmatory'
                    models.append(record)
                print('FIT',spec,hypothesis,len(s),flush=True)
            except ValueError as err:
                models.append(dict(specification=spec,hypothesis=hypothesis,contrast='not_identified',n=len(s),error=str(err)))
    # Province-by-province omission diagnoses influence, without selecting a preferred result.
    for hypothesis,(s,fit) in fits.items():
        regs=fit['regressors']; outcome='D' if hypothesis=='H1' else 'dC_real'
        c=[1,0] if hypothesis=='H1' else [0,0,1,0]
        for p in sorted(s.province.unique()):
            t=s[s.province!=p]
            try:
                f=fe_fit(t,outcome,regs);pt=point(f,c)
                influence.append(dict(hypothesis=hypothesis,omitted_province=p,n=len(t),**pt,error=''))
            except ValueError as err:influence.append(dict(hypothesis=hypothesis,omitted_province=p,n=len(t),coefficient='',cluster_CR1_se='',error=str(err)))
    pd.DataFrame(models).to_csv(OUT/'exploratory_FE_results.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(influence).to_csv(OUT/'leave_one_province_out.csv',index=False,encoding='utf-8-sig')
    # H2 requires evidence of actual income contractions in both phases. Report scarcity explicitly.
    pre=main[(main.post==0)&(main.Z>0)]
    receipt=dict(window_changes='2008_2023; 2007 baseline; no 2006_to_2007 spending change',adjacent_changes=len(data),excluded_adjacent_changes=len(exclusions),shrink1=int(data.shrink1.sum()),shrink2=int(data.shrink2.sum()),shrink3=int(data.shrink3.sum()),main_provinces=main.province.nunique(),H1_exploratory=True,stage=stage,H2_confirmatory_support=False,H2_reason=f'pre-period contractions only {len(pre)} observations in {pre.province.nunique()} provinces',per_student_computed=False,causal_effect_claimed=False,model_scope_approved=False,inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [INPUT,SUPP]},method='unweighted OLS; province and year FE; student-change control; H2 allows stage-specific student slope; province CR1; restricted wild-t p; 95 percent confidence set from inversion of same test over +/-20 CR1 SE grid with boundary flags; unrestricted percentile-t CI retained only as alternate diagnostic; 9999 draws',method_source='https://www.nber.org/papers/t0344',no_primary_junior_four_test_confirmation=True)
    (OUT/'analysis_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(receipt,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
