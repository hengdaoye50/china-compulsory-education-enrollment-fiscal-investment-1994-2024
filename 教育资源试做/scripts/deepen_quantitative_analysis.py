"""Exploratory FE extension, immutable inputs, directly tested category contrasts."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import sys, json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'教育资源试做/.tmp/mpl_deepening'))
sys.path.insert(0,str(ROOT/'教育资源试做/.tmp/figure_deps'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from exploratory_panel_stats import fe_fit, point, wild_t
OUT=ROOT/'教育资源试做/data/定量深化_20261011'
FIG=ROOT/'教育资源试做/定量深化图组_20261011'
OUT.mkdir(exist_ok=True);FIG.mkdir(exist_ok=True)
font=FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
plt.rcParams.update({'font.family':font.get_name(),'font.size':10,'axes.unicode_minus':False,'figure.facecolor':'white','axes.facecolor':'white','pdf.fonttype':42,'svg.fonttype':'none'})
PURPLE='#7E0C6E';GOLD='#B68A3A'
REGS=['dS','dR_real']
INPUTS={s:ROOT/f'教育资源试做/data/{f}/{s}_annual_changes.csv' for s,f in [('primary','小学探索分析_20261010'),('junior','初中探索分析_20261010')]}

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(df,name):df.to_csv(OUT/name,index=False,encoding='utf-8-sig')
def coeffs(fit,stage,spec,outcome):
    rows=[]
    for k,r in enumerate(fit['regressors']):
        c=np.eye(len(fit['regressors']))[k];v=point(fit,c)
        rows.append(dict(stage=stage,specification=spec,outcome=outcome,regressor=r,n=fit['n'],provinces=fit['G'],years=fit['years'],max_leverage=fit['max_leverage'],**v,CR1_normal_95_low=v['coefficient']-1.96*v['cluster_CR1_se'],CR1_normal_95_high=v['coefficient']+1.96*v['cluster_CR1_se']))
    return rows
def export(fig,name):
    for suffix in ['png','pdf','svg']:fig.savefig(FIG/f'{name}.{suffix}',dpi=600,facecolor='white')
    plt.close(fig)
def decorate(ax):
    ax.axvline(0,color='#777777',lw=.8);ax.grid(axis='x',color='#E4E4E4',lw=.6);ax.set_axisbelow(True)
    ax.spines[['top','right']].set_visible(False)

def main():
    before={str(p.relative_to(ROOT)):digest(p) for p in INPUTS.values()}
    frames={s:pd.read_csv(p) for s,p in INPUTS.items()}
    results=[];tests=[];sens=[];influence=[];diagnostics=[];checks=[]
    for si,(stage,data) in enumerate(frames.items()):
        assert not data.duplicated(['province','year']).any()
        assert data[REGS+['dP_real','dC_real','D']].notna().all().all()
        assert not data.model_scope_approved.any()
        data['stage']=stage
        save(data,f'{stage}_model_input.csv')
        fits={o:fe_fit(data,o,REGS) for o in ['dP_real','dC_real','D']}
        assert np.allclose(fits['D']['beta'],fits['dC_real']['beta']-fits['dP_real']['beta'],atol=1e-10)
        assert np.allclose(data.D,data.dC_real-data.dP_real,atol=1e-12)
        checks.append(dict(check=f'{stage}_direct_contrast_identity',passed=True))
        for o,f in fits.items():results.extend(coeffs(f,stage,'main_all_complete',o))
        for k,r in enumerate(REGS):
            infer=wild_t(fits['D'],np.eye(2)[k],B=9999,seed=20261101+si*2+k)
            tests.append(dict(stage=stage,regressor=r,n=len(data),provinces=fits['D']['G'],**infer))
            print('MAIN',stage,r,infer['coefficient'],infer['wild_restricted_p'],flush=True)
        diagnostics.append(dict(stage=stage,n=len(data),provinces=data.province.nunique(),student_decline=int((data.dS<0).sum()),revenue_decline=int((data.dR_real<0).sum()),double_decline=int(((data.dS<0)&(data.dR_real<0)).sum()),min_year=int(data.year.min()),max_year=int(data.year.max()),dS_min=data.dS.min(),dS_max=data.dS.max(),dR_min=data.dR_real.min(),dR_max=data.dR_real.max()))
        variants={
          'exclude_2015_2016':data[~data.year.isin([2015,2016])],
          'exclude_2020_2022':data[~data.year.isin([2020,2021,2022])],
          'exclude_municipalities':data[~data.province.isin(['北京','天津','上海','重庆'])],
          'fixed_28_regions':data[~data.province.isin(['四川','重庆','西藏'])],
          'exclude_2013_2014':data[~data.year.isin([2013,2014])],
        }
        for label,sub in variants.items():sens.extend(coeffs(fe_fit(sub,'D',REGS),stage,label,'D'))
        nominal=data.copy();nominal['dR_real']=nominal.dR_nominal
        sens.extend(coeffs(fe_fit(nominal,'D',REGS),stage,'nominal_R_check','D'))
        for unit in ['province','year']:
            for removed in sorted(data[unit].unique()):
                f=fe_fit(data[data[unit]!=removed],'D',REGS)
                for row in coeffs(f,stage,'leave_one_out','D'):influence.append(dict(unit=unit,omitted=removed,**row))
        asym=data.copy();asym['S_grow']=np.maximum(data.dS,0);asym['S_fall']=np.maximum(-data.dS,0)
        sens.extend(coeffs(fe_fit(asym,'D',['S_grow','S_fall','dR_real']),stage,'asymmetric_student_change','D'))
        lag=data[['province','year']+REGS].copy();lag['year']+=1;lag=lag.rename(columns={r:r+'_lag1' for r in REGS})
        lagged=data.merge(lag,on=['province','year'],how='inner');save(lagged,f'{stage}_lag_model_input.csv')
        f=fe_fit(lagged,'D',REGS+[r+'_lag1' for r in REGS]);sens.extend(coeffs(f,stage,'current_plus_lag1','D'))
        for k,r in enumerate(REGS):
            c=np.zeros(4);c[k]=c[k+2]=1;v=point(f,c)
            sens.append(dict(stage=stage,specification='current_plus_lag1_sum',outcome='D',regressor=r,n=f['n'],provinces=f['G'],years=f['years'],**v))
        # FWL diagnostic: component-wise partial residuals, no independent fit to the plot.
        f=fits['D']
        for k,r in enumerate(REGS):
            z=f['Xm'][:,1-k];x=f['Xm'][:,k];y=f['Y']-f['Q']@(f['Q'].T@f['Y'])
            xr=x-z*(z@x)/(z@z);yr=y-z*(z@y)/(z@z)
            save(pd.DataFrame({'province':data.province,'year':data.year,'partial_x':xr,'partial_D':yr}),f'{stage}_{r}_partial_residuals.csv')
            assert np.isclose(xr@yr/(xr@xr),f['beta'][k],atol=1e-10)
        checks.append(dict(check=f'{stage}_FWL_partial_slope',passed=True))
    test=pd.DataFrame(tests);order=np.argsort(test.wild_restricted_p.to_numpy());adjust=np.maximum.accumulate([(4-i)*test.iloc[j].wild_restricted_p for i,j in enumerate(order)])
    test['Holm_four_p']=np.nan
    for i,j in enumerate(order):test.loc[j,'Holm_four_p']=min(1,float(adjust[i]))
    save(pd.DataFrame(results),'all_main_coefficients.csv');save(test,'four_direct_contrast_tests.csv')
    save(pd.DataFrame(sens),'all_sensitivities.csv');save(pd.DataFrame(influence),'leave_one_out.csv');save(pd.DataFrame(diagnostics),'sample_diagnostics.csv')
    for p in INPUTS.values():assert digest(p)==before[str(p.relative_to(ROOT))]
    checks.append(dict(check='source_input_hashes_unchanged',passed=True))
    # Main confidence-set figure, using only closed single-band inversions.
    fig,axes=plt.subplots(1,2,figsize=(7.0,3.2),sharex=True,layout='constrained')
    for k,r in enumerate(REGS):
        ax=axes[k];sub=test[test.regressor==r]
        for j,row in enumerate(sub.itertuples(index=False)):
            if row.WCR_search_boundary_accepted or row.WCR_disjoint_bands!=1:raise ValueError('Main plot requires explicit open/disjoint confidence-set treatment')
            ax.errorbar(row.coefficient,j,xerr=[[row.coefficient-row.WCR_95_CI_low],[row.WCR_95_CI_high-row.coefficient]],fmt='o' if j==0 else 's',color=PURPLE if j==0 else GOLD,capsize=4,ms=6)
            ax.text(.03,.93-j*.13,f'{["小学","初中"][j]}：Holm p={row.Holm_four_p:.3f}',transform=ax.transAxes,fontsize=8)
        decorate(ax);ax.set_yticks([0,1],['小学','初中']);ax.set_ylim(-.6,1.7)
        ax.set_title(['A  区域学生变化','B  实际自身收入变化'][k],loc='left',fontsize=10)
        ax.set_xlabel('公用减个人的响应系数差')
    fig.suptitle('两类支出的响应是否不同？直接差异检验',fontsize=12)
    export(fig,'图Q1_直接差异与置信区间')
    # Decompose components, explicitly normal approximate intervals.
    rr=pd.DataFrame(results)
    fig,axes=plt.subplots(1,2,figsize=(7,3.9),sharex=True,layout='constrained')
    labels=['小学·个人','小学·公用','初中·个人','初中·公用']
    for k,r in enumerate(REGS):
        ax=axes[k]
        for j,(s,o) in enumerate([('primary','dP_real'),('primary','dC_real'),('junior','dP_real'),('junior','dC_real')]):
            row=rr[(rr.stage==s)&(rr.outcome==o)&(rr.regressor==r)].iloc[0]
            ax.errorbar(row.coefficient,j,xerr=1.96*row.cluster_CR1_se,fmt='o' if o=='dP_real' else 's',color=PURPLE if o=='dP_real' else GOLD,capsize=3)
        decorate(ax);ax.set_yticks(range(4),labels);ax.invert_yaxis();ax.set_title(['A  区域学生变化','B  实际自身收入变化'][k],loc='left',fontsize=10);ax.set_xlabel('条件响应系数（含正态近似95%区间）')
    fig.suptitle('个人与公用支出的分模型估计',fontsize=12);export(fig,'图Q2_支出分项响应')
    fig,axes=plt.subplots(2,2,figsize=(7,5.2),sharex='col',layout='constrained')
    for si,s in enumerate(['primary','junior']):
        for k,r in enumerate(REGS):
            ax=axes[si,k];points=pd.read_csv(OUT/f'{s}_{r}_partial_residuals.csv');row=test[(test.stage==s)&(test.regressor==r)].iloc[0]
            ax.scatter(points.partial_x*100,points.partial_D*100,s=9,color=PURPLE if si==0 else GOLD,alpha=.38,edgecolors='none')
            xx=np.array([points.partial_x.min(),points.partial_x.max()])*100;ax.plot(xx,row.coefficient*xx,color='#444444',lw=1)
            ax.axhline(0,color='#BBBBBB',lw=.6);ax.axvline(0,color='#BBBBBB',lw=.6);ax.spines[['top','right']].set_visible(False)
            ax.set_title(f'{["小学","初中"][si]} · {["学生变化","自身收入变化"][k]}',loc='left',fontsize=10)
            ax.set_ylabel('D的偏回归残差\n（对数百分点）')
            if si==1:ax.set_xlabel('解释变量偏回归残差（对数百分点）')
    fig.suptitle('回归关系的观测支持：全部省年，不作分箱',fontsize=12);export(fig,'图Q3_偏回归散点')
    (FIG/'图注与阅读说明.md').write_text('''# 定量深化图组

图Q1：2008—2023年完整省年，各学段不加权OLS，控制省份、年份效应及另一解释变量。纵向类别是学段；点为D=ΔlnC−ΔlnP模型系数，线为9999次省级约束野生聚类自助检验反演95%区间。Holm p对小学/初中×学生/收入共四项直接检验校正；区间为单项95%，非家族同时区间。零线表示两类支出响应相同。

图Q2：相同样本和解释变量，分别以个人、公用实际支出对数变化为因变量。误差线为省级聚类CR1标准误×1.96的正态近似95%区间，属于分模型展示，不用两个区间是否重叠替代图Q1直接差异检验。低学生响应不能单独解释为低效率。

图Q3：将因变量D和横轴解释变量均剔除省份效应、年份效应及另一个解释变量后，显示每条省年观测的偏回归残差。无分箱、无删极值；线的斜率等于主模型系数。散点不是新增独立样本，线不是因果关系。

P/C为全来源、全隶属个人/公用支出；R为地方自身财政收入；CPI调整只是购买力近似。学生与经费学校覆盖未完全桥接，学生只能作为区域生源背景。三图均为探索性条件关联，不能宣称政府预算行为或制度因果效应。小学和初中各472条省年、31个省级聚类；重复学段不增加独立财政聚类数。图像按178毫米左右宽度设计，纯白背景，600 dpi PNG，另有矢量PDF/SVG。图Q3各面板纵轴按观测范围独立绘制，散布大小不能据此作跨图幅度比较。
''',encoding='utf8')
    receipt=dict(inputs=before,checks=checks,versions={'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'matplotlib':matplotlib.__version__},main_family=4,bootstrap_draws=9999,scope='exploratory conditional association; full-affiliation all-source expense; student scope not certified',no_causal_claim=True)
    (OUT/'analysis_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(test.to_string(index=False),flush=True)

if __name__=='__main__':main()
