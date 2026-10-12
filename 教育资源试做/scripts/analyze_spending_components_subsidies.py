"""Exploratory component and central-subsidy associations, with reproducible figures."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'教育资源试做/data';OUT=DATA/'支出细项与补助拓展_20261011';FIG=ROOT/'教育资源试做/支出细项与补助图组_20261011';FIG.mkdir(exist_ok=True)
os.environ['MPLCONFIGDIR']=str(ROOT/'教育资源试做/.tmp/mpl_deepening')
sys.path.insert(0,str(ROOT/'教育资源试做/.tmp/figure_deps'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from exploratory_panel_stats import fe_fit,point,wild_t
from infer_resource_timing import t_critical
FONT=FontProperties(fname='C:/Windows/Fonts/msyh.ttc');PURPLE='#7E0C6E';GOLD='#B68A3A'
plt.rcParams.update({'font.family':FONT.get_name(),'font.size':10,'axes.unicode_minus':False,'figure.facecolor':'white','axes.facecolor':'white','pdf.fonttype':42,'svg.fonttype':'none'})
def save(rows,name):pd.DataFrame(rows).to_csv(OUT/name,index=False,encoding='utf-8-sig')
def export(f,name):
    for ext in ['png','svg','pdf']:f.savefig(FIG/f'{name}.{ext}',dpi=600,facecolor='white')
    plt.close(f)
def clean(ax):ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color='#E5E5E5',lw=.6);ax.set_axisbelow(True)
def coef(f,s,spec,y):
    t=t_critical(f['G']-1);result=[]
    for k,r in enumerate(f['regressors']):
        z=point(f,np.eye(len(f['regressors']))[k]);b=z['coefficient'];se=z['cluster_CR1_se']
        result.append(dict(stage=s,specification=spec,outcome=y,regressor=r,n=f['n'],provinces=f['G'],years=f['years'],coefficient=b,cluster_CR1_se=se,low=b-t*se,high=b+t*se))
    return result
def holm(df):
    order=np.argsort(df.wild_restricted_p.values);p=df.wild_restricted_p.values[order];v=np.minimum(1,np.maximum.accumulate(p*(len(p)-np.arange(len(p)))));df.loc[df.index[order],'Holm_family_p']=v;return df
def main():
    protected=[DATA/'education_resource_panel.csv',DATA/'finance_long.csv',DATA/'panel.json',*[DATA/f'定量深化_20261011/{s}_model_input.csv' for s in ['primary','junior']]]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    lev=pd.read_csv(OUT/'component_levels.csv');prev=lev.copy();prev.year+=1;prev=prev.rename(columns={c:c+'_previous' for c in prev if c not in ['year','province','stage']});changes=lev.merge(prev,on=['year','province','stage'],validate='one_to_one')
    fiscal=pd.read_csv(OUT/'subsidy_levels_numeric.csv');fiscal['RplusB']=fiscal.R+fiscal.B;fp=fiscal[['year','province','R','B','RplusB']].copy();fp.year+=1;fp=fp.rename(columns={c:c+'_previous' for c in fp if c not in ['year','province']});fc=fiscal.merge(fp,on=['year','province'],validate='one_to_one')
    allcoef=[];main_tests=[];sub_tests=[];sensitivity=[];influence=[];exclusions=[];summary=[];allinputs=[];finputs=[]
    for si,s in enumerate(['primary','junior']):
        base=pd.read_csv(DATA/f'定量深化_20261011/{s}_model_input.csv');df=base.merge(changes[changes.stage==s].drop(columns='stage'),on=['year','province'],validate='one_to_one')
        for m in ['W','A','G','X']:
            valid=(df[m]>0)&(df[m+'_previous']>0);df['d'+m+'_real']=np.where(valid,np.log(df[m].where(valid)/df[m+'_previous'].where(valid))-np.log(df.CPI_yoy/100),np.nan)
            for r in df[~valid].itertuples():exclusions.append(dict(stage=s,year=r.year,province=r.province,part=m,reason='nonpositive_adjacent_component_no_log_or_pseudocount'))
        # CPI_yoy is the year-on-year index, previous year = 100.
        df['DGW']=df.dG_real-df.dW_real
        assert np.allclose(np.log(df.C/df.C_previous)-np.log(df.CPI_yoy/100),df.dC_real,atol=1e-10)
        for m in ['G','X']:df[m+'_contribution']=(df[m]/(df.CPI_yoy/100)-df[m+'_previous'])/df.C_previous
        df['C_real_growth']=df.C/(df.CPI_yoy/100)/df.C_previous-1
        df['contribution_rounding_residual']=df.G_contribution+df.X_contribution-df.C_real_growth
        df['contribution_rounding_tolerance']=1.5*(1+100/df.CPI_yoy)/df.C_previous+1e-12
        assert (df.contribution_rounding_residual.abs()<=df.contribution_rounding_tolerance).all()
        main=df.dropna(subset=['DGW']).copy();save(main,f'{s}_component_model_input.csv');allinputs.append(main)
        for y in ['dW_real','dA_real','dG_real','dX_real','D','DGW']:
            sample=main.dropna(subset=[y]);f=fe_fit(sample,y,['dS','dR_real']);allcoef.extend(coef(f,s,'components',y))
            if y=='DGW':
                for k in range(2):
                    z=wild_t(f,np.eye(2)[k],B=9999,seed=20261301+si*2+k);main_tests.append(dict(stage=s,outcome=y,regressor=['dS','dR_real'][k],n=f['n'],provinces=f['G'],**z));print('COMPONENT',s,k,z['coefficient'],z['wild_restricted_p'],flush=True)
                for name,excluded_years in [('without_2013_14',[2013,2014]),('without_2015_16',[2015,2016]),('without_2020_22',[2020,2021,2022])]:sensitivity.extend(coef(fe_fit(main[~main.year.isin(excluded_years)],y,['dS','dR_real']),s,name,y))
                for p in main.province.unique():influence.extend([dict(r,removed_province=p) for r in coef(fe_fit(main[main.province!=p],y,['dS','dR_real']),s,'leave_one_province',y)])
        fdf=main.merge(fc[['year','province','B','B_previous','R','R_previous','RplusB','RplusB_previous']],on=['year','province'],how='left',validate='one_to_one',indicator=True)
        for r in fdf[fdf._merge!='both'].itertuples():exclusions.append(dict(stage=s,year=r.year,province=r.province,part='subsidy',reason='no_adjacent_numeric_verified_subsidy'))
        fdf=fdf[fdf._merge=='both'].drop(columns='_merge').copy();fdf['dBsub_real']=np.log(fdf.B/fdf.B_previous)-np.log(fdf.CPI_yoy/100);fdf['dRplusB_real']=np.log(fdf.RplusB/fdf.RplusB_previous)-np.log(fdf.CPI_yoy/100)
        assert np.allclose(np.log(fdf.R/fdf.R_previous)-np.log(fdf.CPI_yoy/100),fdf.dR_real,atol=3e-5)
        save(fdf,f'{s}_subsidy_model_input.csv');finputs.append(fdf)
        for spec,regs in [('same_sample_own',['dS','dR_real']),('own_and_subsidy',['dS','dR_real','dBsub_real']),('own_plus_subsidy',['dS','dRplusB_real'])]:
            for y in ['dG_real','DGW','D']:
                f=fe_fit(fdf,y,regs);allcoef.extend(coef(f,s,spec,y))
                if spec=='own_and_subsidy' and y in ['dG_real','DGW']:
                    z=wild_t(f,[0,0,1],B=9999,seed=20261401+si*2+int(y=='DGW'));sub_tests.append(dict(stage=s,outcome=y,regressor='dBsub_real',n=f['n'],provinces=f['G'],**z));print('SUBSIDY',s,y,z['coefficient'],z['wild_restricted_p'],flush=True)
                    variants=[('fiscal_without_2015_16',~fdf.year.isin([2015,2016])),('fiscal_without_2020_22',~fdf.year.isin([2020,2021,2022])),('without_plan_listed_provinces',~fdf.province.isin(['辽宁','山东','浙江','福建','广东']))]
                    for name,mask in variants:sensitivity.extend(coef(fe_fit(fdf[mask],y,regs),s,name,y))
                    for p in fdf.province.unique():influence.extend([dict(r,removed_province=p) for r in coef(fe_fit(fdf[fdf.province!=p],y,regs),s,'leave_one_province_subsidy',y)])
        summary.append(dict(stage=s,component_n=len(main),subsidy_n=len(fdf),component_provinces=main.province.nunique(),subsidy_provinces=fdf.province.nunique(),own_real_decline=int((fdf.dR_real<0).sum()),decline_but_sum_nonnegative=int(((fdf.dR_real<0)&(fdf.dRplusB_real>=0)).sum())))
    tests=holm(pd.DataFrame(main_tests));sub=holm(pd.DataFrame(sub_tests));co=pd.DataFrame(allcoef);save(tests,'component_primary_tests.csv');save(sub,'subsidy_exploratory_tests.csv');save(co,'all_coefficients.csv');save(sensitivity,'sensitivity.csv');save(influence,'leave_province_out.csv');save(exclusions,'analysis_exclusions.csv');save(summary,'sample_summary.csv')
    combined=pd.concat(allinputs);fin=pd.concat(finputs);save(combined,'growth_contribution_plot_data.csv')
    shares=lev.groupby(['stage','year'])[['W','A','G','X','P','C']].sum().reset_index();shares['W_share']=shares.W/shares.P;shares['G_share']=shares.G/shares.C;save(shares,'composition_plot_data.csv')
    # Figure 1: two denominators are explicitly separated; start axis at zero.
    f,axs=plt.subplots(2,2,figsize=(9,6.3),sharex=True,sharey=True)
    for i,s in enumerate(['primary','junior']):
        d=shares[shares.stage==s]
        for j,(share,labs) in enumerate([('W_share',['工资福利','个人家庭补助']),('G_share',['商品服务','其他资本性'])]):
            ax=axs[i,j];ax.stackplot(d.year,d[share]*100,(1-d[share])*100,colors=[PURPLE,GOLD],labels=labs,alpha=.93);ax.set_ylim(0,100);ax.set_title(('小学' if i==0 else '初中')+'：'+('个人支出内部' if j==0 else '公用支出内部'));ax.set_ylabel('合计金额构成（%）');ax.set_xticks([2007,2011,2015,2019,2023]);clean(ax)
            if i==0:ax.legend(loc='lower left',frameon=True,fontsize=9)
            else:ax.set_xlabel('数据年度')
    f.subplots_adjust(left=.08,right=.98,top=.92,bottom=.1,hspace=.32,wspace=.2);export(f,'图F1_支出内部构成')
    # Figure 2: the arithmetic mean preserves the additive identity exactly.
    mean=combined.groupby(['stage','year'])[['G_contribution','X_contribution','C_real_growth']].mean().reset_index();save(mean,'annual_mean_contribution_plot_data.csv')
    f,axs=plt.subplots(2,1,figsize=(9,6.1),sharex=True)
    for i,s in enumerate(['primary','junior']):
        d=mean[mean.stage==s];ax=axs[i];ax.bar(d.year-.2,d.G_contribution*100,width=.38,color=PURPLE,label='商品服务贡献');ax.bar(d.year+.2,d.X_contribution*100,width=.38,color=GOLD,label='其他资本性贡献');ax.plot(d.year,d.C_real_growth*100,'o-',color='#333333',ms=3,lw=1,label='公用实际增长');ax.axhline(0,color='#777777',lw=.7);ax.set_title('小学' if i==0 else '初中');ax.set_ylabel('省年算术均值（百分点）');clean(ax)
    axs[0].legend(ncol=3,fontsize=9,frameon=False);axs[1].set_xticks(range(2008,2024,2));axs[1].set_xlabel('数据年度');f.subplots_adjust(left=.12,right=.98,top=.93,bottom=.1,hspace=.32);export(f,'图F2_公用增长贡献')
    # Figure 3: direct contrasts receive WCR inference, not auxiliary CR1 intervals.
    f,axs=plt.subplots(1,2,figsize=(9,4.2),sharex=True)
    for i,s in enumerate(['primary','junior']):
        ax=axs[i];d=tests[tests.stage==s]
        for k,r in enumerate(d.itertuples()):
            ax.errorbar(r.coefficient,1-k,xerr=[[r.coefficient-r.WCR_95_CI_low],[r.WCR_95_CI_high-r.coefficient]],fmt='o',color=PURPLE,capsize=4);ax.text(.02,.93-k*.55,f'校正 p = {r.Holm_family_p:.4f}',transform=ax.transAxes,fontsize=9)
        ax.set_yticks([1,0],['学生变化','自身收入变化']);ax.set_ylim(-.45,1.6);ax.axvline(0,color='#777777',lw=.8);ax.grid(axis='x',color='#E5E5E5');ax.spines[['top','right']].set_visible(False);ax.set_title('小学' if i==0 else '初中');ax.set_xlabel('商品服务减工资福利：响应系数差')
    f.subplots_adjust(left=.13,right=.98,top=.88,bottom=.18,wspace=.48);export(f,'图F3_商品服务与工资响应差')
    # Figure 4: four separately named component responses, common explanatory specification.
    f,axs=plt.subplots(1,2,figsize=(9,4.5),sharex=True)
    for i,s in enumerate(['primary','junior']):
        d=co[(co.stage==s)&(co.specification=='components')&(co.regressor=='dS')].set_index('outcome');ax=axs[i]
        for k,(y,label) in enumerate([('dW_real','工资福利'),('dA_real','个人家庭补助'),('dG_real','商品服务'),('dX_real','其他资本性')]):
            r=d.loc[y];ax.errorbar(r.coefficient,3-k,xerr=[[r.coefficient-r.low],[r.high-r.coefficient]],fmt='o',color=PURPLE if k in [0,2] else GOLD,capsize=3)
        ax.set_yticks(range(4),['其他资本性','商品服务','个人家庭补助','工资福利']);ax.axvline(0,color='#777777',lw=.8);ax.grid(axis='x',color='#E5E5E5');ax.spines[['top','right']].set_visible(False);ax.set_title('小学' if i==0 else '初中');ax.set_xlabel('学生变化响应系数（CR1近似95%区间）')
    f.subplots_adjust(left=.14,right=.98,top=.9,bottom=.16,wspace=.55);export(f,'图F4_支出细项响应')
    # Fiscal state plot: unique province-year, not double-counted school stages.
    fd=fin.drop_duplicates(['province','year']);save(fd[['province','year','dR_real','dRplusB_real','dBsub_real']],'fiscal_state_plot_data.csv')
    f,ax=plt.subplots(figsize=(7.5,5.4));highlight=(fd.dR_real<0)&(fd.dRplusB_real>=0)
    for mask,color,label in [(~highlight,PURPLE,'其他省年'),(highlight,GOLD,f'自身收入下降而合计未下降（{int(highlight.sum())}条）')]:ax.scatter(fd.loc[mask,'dR_real']*100,fd.loc[mask,'dRplusB_real']*100,s=22,color=color,alpha=.6 if color==GOLD else .4,edgecolor='none',label=label)
    ax.axhline(0,color='#777777',lw=.8);ax.axvline(0,color='#777777',lw=.8);lo=min(fd.dR_real.min(),fd.dRplusB_real.min())*100;hi=max(fd.dR_real.max(),fd.dRplusB_real.max())*100;ax.plot([lo,hi],[lo,hi],ls='--',color='#555555',lw=1,label='两指标增长相同');ax.set_xlabel('自身收入实际对数变化（×100）');ax.set_ylabel('自身收入与中央补助合计实际对数变化（×100）');ax.legend(frameon=False,fontsize=9,loc='upper left');clean(ax);f.subplots_adjust(left=.15,right=.97,top=.95,bottom=.15);export(f,'图F5_自身收入与补助合计变化')
    # Figure 6: direct subsidy association with WCR intervals.
    f,axs=plt.subplots(1,2,figsize=(9,4.3),sharex=True)
    for i,s in enumerate(['primary','junior']):
        ax=axs[i]
        for k,y in enumerate(['dG_real','DGW']):
            r=sub[(sub.stage==s)&(sub.outcome==y)].iloc[0];ax.errorbar(r.coefficient,1-k,xerr=[[r.coefficient-r.WCR_95_CI_low],[r.WCR_95_CI_high-r.coefficient]],fmt='o',color=GOLD,capsize=4);ax.text(.02,.93-k*.55,f'校正 p = {r.Holm_family_p:.4f}',transform=ax.transAxes,fontsize=9)
        ax.set_yticks([1,0],['商品服务','商品服务减工资福利']);ax.set_ylim(-.45,1.6);ax.axvline(0,color='#777777',lw=.8);ax.grid(axis='x',color='#E5E5E5');ax.spines[['top','right']].set_visible(False);ax.set_title('小学' if i==0 else '初中');ax.set_xlabel('中央补助实际变化响应系数')
    f.subplots_adjust(left=.2,right=.98,top=.88,bottom=.18,wspace=.9);export(f,'图F6_中央补助关联')
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    receipt=dict(protected_sha256=hashes,component_tests=tests.to_dict('records'),subsidy_tests=sub.to_dict('records'),samples=summary,figures=6,bootstrap_draws=9999,scope_approved=False,analysis_type='adaptive_exploratory_no_causal_identification')
    (OUT/'analysis_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print('DONE',summary,flush=True)
if __name__=='__main__':main()
