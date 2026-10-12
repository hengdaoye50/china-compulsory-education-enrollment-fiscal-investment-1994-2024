"""Exploratory spending/resource associations; never a mediation estimate."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import sys,json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'教育资源试做/data'
OUT=DATA/'资源解释拓展_20261011';FIG=ROOT/'教育资源试做/资源解释图组_20261011'
OUT.mkdir(exist_ok=True);FIG.mkdir(exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'教育资源试做/.tmp/mpl_deepening'))
sys.path.insert(0,str(ROOT/'教育资源试做/.tmp/figure_deps'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from exploratory_panel_stats import fe_fit,point,wild_t
from infer_resource_timing import t_critical
from parse import read as read_html
FONT=FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
plt.rcParams.update({'font.family':FONT.get_name(),'font.size':10,'axes.unicode_minus':False,'figure.facecolor':'white','axes.facecolor':'white','pdf.fonttype':42,'svg.fonttype':'none'})
PURPLE='#7E0C6E';GOLD='#B68A3A'
REGS=['dS','dR_real','dT','dB']
paths=[DATA/'education_resource_panel.csv',DATA/'resource_schemas.json',*[DATA/f'定量深化_20261011/{s}_model_input.csv' for s in ['primary','junior']]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(rows,name):pd.DataFrame(rows).to_csv(OUT/name,index=False,encoding='utf-8-sig')
def coef(fit,stage,spec,outcome):
    rows=[];crit=t_critical(fit['G']-1)
    for k,r in enumerate(fit['regressors']):
        v=point(fit,np.eye(len(fit['regressors']))[k]);rows.append(dict(stage=stage,specification=spec,outcome=outcome,regressor=r,n=fit['n'],provinces=fit['G'],years=fit['years'],coefficient=v['coefficient'],cluster_CR1_se=v['cluster_CR1_se'],CR1_t_95_low=v['coefficient']-crit*v['cluster_CR1_se'],CR1_t_95_high=v['coefficient']+crit*v['cluster_CR1_se']))
    return rows
def export(fig,name):
    for ext in ['png','svg','pdf']:fig.savefig(FIG/f'{name}.{ext}',dpi=600,facecolor='white')
    plt.close(fig)
def deco(ax):
    ax.axvline(0,color='#777777',lw=.8);ax.grid(axis='x',color='#E4E4E4',lw=.6);ax.set_axisbelow(True);ax.spines[['top','right']].set_visible(False)

def main():
    hashes={str(p.relative_to(ROOT)):sha(p) for p in paths}
    res=pd.read_csv(paths[0]);res=res[res.year.between(2013,2023)].copy();ix=res.set_index(['year','province','stage'])
    sourcechecks=[];sourcehashes={};tablecount=0
    schemas=json.loads(paths[1].read_text(encoding='utf8'))
    for s in schemas:
        if not 2013<=s['year']<=2023 or s['kind'] not in ['students','teachers','classes']:continue
        tablecount+=1;path=ROOT/'教育资源试做'/s['path'];h=sha(path);sourcehashes[str(path.relative_to(ROOT))]=h
        wanted=[k for k in ['students','teachers','classes','schools'] if k in s['columns']]
        found=set()
        for raw in [r for table in read_html(path).tables for r in table]:
            if not raw:continue
            p=re.sub(r'[\sA-Za-z()\-]','',raw[0]);p='全国' if p in ['总计','合计','全国'] else p
            key=(s['year'],p,s['stage'])
            if key not in ix.index:continue
            for metric in wanted:
                col=s['columns'][metric]
                if len(raw)<=col:continue
                txt=re.sub(r'[,\s]','',raw[col])
                if not re.fullmatch(r'\d+',txt):continue
                value=int(txt);expected=int(ix.loc[key,metric]);assert value==expected,(key,metric,value,expected)
                assert (p,metric) not in found,(key,metric,'duplicate_numeric_row')
                found.add((p,metric));sourcechecks.append(dict(year=s['year'],province=p,stage=s['stage'],metric=metric,value=value,source_url=s['source'],raw_file=str(path.relative_to(ROOT)),column_index=col,source_sha256=h,pass_exact=True))
        assert len(found)==32*len(wanted),(s['year'],s['stage'],s['kind'],len(found))
    assert tablecount==66
    save(sourcechecks,'resource_source_rereads.csv')
    level=res[res.province!='全国'][['province','stage','year','students','teachers','classes','schools','students_source','teachers_source','classes_source']].copy()
    level['schools_source']=level.classes_source
    prev=level.copy();prev['year']+=1;prev=prev.rename(columns={c:c+'_previous' for c in prev if c not in ['year','province','stage']})
    changes=level.merge(prev,on=['year','province','stage'],how='inner')
    for metric,col in [('students','dS_resource'),('teachers','dT'),('classes','dB'),('schools','dH')]:
        assert (changes[[metric,metric+'_previous']]>0).all().all()
        changes[col]=np.log(changes[metric]/changes[metric+'_previous'])
    save(changes,'resource_changes_2014_2023.csv')
    assert len(changes)==620
    allcoef=[];tests=[];influence=[];diagnostics=[];excluded=[];mismatch=[];desc=[]
    for si,stage in enumerate(['primary','junior']):
        base=pd.read_csv(DATA/f'定量深化_20261011/{stage}_model_input.csv');src=changes[changes.stage==stage].copy()
        merged=src.merge(base.drop(columns=['stage']),on=['province','year'],how='left',indicator=True)
        for row in merged[merged._merge!='both'].itertuples(index=False):excluded.append(dict(stage=stage,province=row.province,year=row.year,reason='no_complete_adjacent_finance_R_in_existing_model'))
        df=merged[merged._merge=='both'].drop(columns='_merge').copy()
        df['student_change_matches_resource']=np.isclose(df.dS,df.dS_resource,atol=1e-10,rtol=1e-10)
        for row in df[~df.student_change_matches_resource].itertuples(index=False):mismatch.append(dict(stage=stage,province=row.province,year=row.year,dS_existing=row.dS,dS_resource=row.dS_resource,difference=row.dS-row.dS_resource))
        save(df,f'{stage}_model_input.csv')
        assert not df.duplicated(['province','year']).any()
        fits={}
        specs={'same_sample_baseline':['dS','dR_real'],'teacher_only':['dS','dR_real','dT'],'class_only':['dS','dR_real','dB'],'joint_resources':REGS}
        full=fe_fit(base,'D',['dS','dR_real']);allcoef.extend(coef(full,stage,'previous_full_window','D'))
        for spec,regs in specs.items():
            for o in ['dP_real','dC_real','D']:
                f=fe_fit(df,o,regs);fits[(spec,o)]=f;allcoef.extend(coef(f,stage,spec,o))
            assert np.allclose(fits[(spec,'D')]['beta'],fits[(spec,'dC_real')]['beta']-fits[(spec,'dP_real')]['beta'],atol=1e-10)
        joint=fits[('joint_resources','D')]
        std=joint['Xm']/np.sqrt((joint['Xm']**2).sum(axis=0))
        vif=np.diag(np.linalg.inv(std.T@std))
        for k,r in enumerate(REGS):diagnostics.append(dict(stage=stage,regressor=r,within_FE_VIF=float(vif[k]),standardized_design_condition=float(np.linalg.cond(std)),max_leverage=joint['max_leverage'],n=len(df),provinces=df.province.nunique()))
        for k,r in [(2,'dT'),(3,'dB')]:
            result=wild_t(joint,np.eye(4)[k],B=9999,seed=20261201+si*2+k-2)
            tests.append(dict(stage=stage,regressor=r,n=len(df),provinces=joint['G'],**result));print('MAIN',stage,r,result['coefficient'],result['wild_restricted_p'],flush=True)
        for unit in ['province','year']:
            for removed in sorted(df[unit].unique()):
                f=fe_fit(df[df[unit]!=removed],'D',REGS)
                for row in coef(f,stage,'leave_one_out','D'):
                    if row['regressor'] in ['dT','dB']:influence.append(dict(unit=unit,omitted=removed,**row))
        sensitivity={
          'exclude_2014':df[df.year!=2014],
          'exclude_2015_2016':df[~df.year.isin([2015,2016])],
          'exclude_2020_2022':df[~df.year.isin([2020,2021,2022])],
          'exclude_municipalities':df[~df.province.isin(['北京','天津','上海','重庆'])],
          'matched_student_changes':df[df.student_change_matches_resource]
        }
        for spec,sub in sensitivity.items():
            if not len(sub):continue
            allcoef.extend(coef(fe_fit(sub,'D',REGS),stage,spec,'D'))
        allcoef.extend(coef(fe_fit(df,'D',REGS+['dH']),stage,'add_schools','D'))
        lag=changes[changes.stage==stage][['province','year','dT','dB']].copy();lag.year+=1;lag=lag.rename(columns={'dT':'dT_lag1','dB':'dB_lag1'})
        lagged=df.merge(lag,on=['province','year'],how='inner');save(lagged,f'{stage}_lag_model_input.csv')
        allcoef.extend(coef(fe_fit(lagged,'D',['dS','dR_real']),stage,'lag_sample_baseline','D'))
        allcoef.extend(coef(fe_fit(lagged,'D',['dS','dR_real','dT_lag1','dB_lag1']),stage,'lagged_resources','D'))
        for o in ['dT','dB','dH']:
            allcoef.extend(coef(fe_fit(df,o,['dS','dR_real']),stage,'resource_response_context',o))
        for status,sub in [('all',df),('student_decline',df[df.dS<0]),('student_growth',df[df.dS>0])]:
            desc.append(dict(stage=stage,student_state=status,n=len(sub),provinces=sub.province.nunique(),median_student_logpoints=float(sub.dS.median()*100),median_teacher_logpoints=float(sub.dT.median()*100),median_class_logpoints=float(sub.dB.median()*100),median_school_logpoints=float(sub.dH.median()*100),teacher_growth=int((sub.dT>0).sum()),class_growth=int((sub.dB>0).sum()),school_growth=int((sub.dH>0).sum())))
    tt=pd.DataFrame(tests);order=np.argsort(tt.wild_restricted_p);adj=np.maximum.accumulate([(4-i)*tt.iloc[j].wild_restricted_p for i,j in enumerate(order)])
    tt['Holm_four_p']=np.nan
    for i,j in enumerate(order):tt.loc[j,'Holm_four_p']=min(1,float(adj[i]))
    co=pd.DataFrame(allcoef);save(co,'all_coefficients_and_sensitivities.csv');save(tt,'four_resource_contrast_tests.csv');save(influence,'leave_one_out.csv');save(diagnostics,'design_diagnostics.csv');save(desc,'descriptive_states.csv')
    save(excluded,'excluded_finance_connections.csv');save(pd.DataFrame(mismatch,columns=['stage','province','year','dS_existing','dS_resource','difference']),'student_change_discrepancies.csv')
    for p in paths:assert sha(p)==hashes[str(p.relative_to(ROOT))]
    receipt={'input_hashes':hashes,'raw_resource_hashes':sourcehashes,'resource_tables_reread':tablecount,'resource_cells_reread':len(sourcechecks),'common_resource_changes':len(changes),'excluded_finance_connections':len(excluded),'student_change_discrepancies':len(mismatch),'exploratory':True,'causal_mediation_estimated':False,'model_scope_approved':False,'main_test_family':4,'bootstrap_draws':9999,'versions':{'numpy':np.__version__,'pandas':pd.__version__,'matplotlib':matplotlib.__version__}}
    (OUT/'analysis_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    # Ordered model comparisons on an explicitly shared sample, with original window separate.
    fig,axes=plt.subplots(1,2,figsize=(7,3.9),sharex=True,layout='constrained')
    seq=['previous_full_window','same_sample_baseline','teacher_only','class_only','joint_resources']
    for si,stage in enumerate(['primary','junior']):
        ax=axes[si];labels=[]
        for j,spec in enumerate(seq):
            row=co[(co.stage==stage)&(co.outcome=='D')&(co.specification==spec)&(co.regressor=='dS')].iloc[0]
            labels.append(['原窗口基准','同样本基准','加入教师','加入班级','教师与班级'][j]+f'  n={row.n}')
            ax.errorbar(row.coefficient,j,xerr=[[row.coefficient-row.CR1_t_95_low],[row.CR1_t_95_high-row.coefficient]],fmt='o' if si==0 else 's',color=PURPLE if si==0 else GOLD,capsize=3)
        deco(ax);ax.set_yticks(range(5),labels,fontsize=8);ax.invert_yaxis();ax.set_title(['小学','初中'][si],loc='left');ax.set_xlabel('学生变化的公用减个人响应差')
    fig.suptitle('学生响应差的变化：区分样本与模型',fontsize=12);export(fig,'图E1_同样本模型比较')
    fig,axes=plt.subplots(1,2,figsize=(7,3.2),sharex=True,layout='constrained')
    for k,r in enumerate(['dT','dB']):
        ax=axes[k]
        for si,stage in enumerate(['primary','junior']):
            row=tt[(tt.stage==stage)&(tt.regressor==r)].iloc[0]
            color=PURPLE if si==0 else GOLD
            if not row.WCR_search_boundary_accepted and row.WCR_disjoint_bands==1:
                ax.errorbar(row.coefficient,si,xerr=[[row.coefficient-row.WCR_95_CI_low],[row.WCR_95_CI_high-row.coefficient]],fmt='o' if si==0 else 's',color=color,capsize=4)
            else:
                ax.plot(row.coefficient,si,marker='o' if si==0 else 's',color=color);ax.text(row.coefficient,si+.15,'置信集未闭合或分离',fontsize=8)
            ax.text(.03,.94-si*.14,f'{["小学","初中"][si]}：Holm p={row.Holm_four_p:.3f}',transform=ax.transAxes,fontsize=8)
        deco(ax);ax.set_yticks([0,1],['小学','初中']);ax.set_ylim(-.5,1.8);ax.set_title(['A  专任教师变化','B  班级变化'][k],loc='left');ax.set_xlabel('公用减个人的资源关联系数')
    fig.suptitle('资源变化与支出增长差的条件关联',fontsize=12);export(fig,'图E2_资源关联直接差异')
    fig,axes=plt.subplots(1,2,figsize=(7,3.9),sharex=True,layout='constrained')
    for k,r in enumerate(['dT','dB']):
        ax=axes[k]
        for j,(stage,o) in enumerate([('primary','dP_real'),('primary','dC_real'),('junior','dP_real'),('junior','dC_real')]):
            row=co[(co.stage==stage)&(co.specification=='joint_resources')&(co.outcome==o)&(co.regressor==r)].iloc[0]
            ax.errorbar(row.coefficient,j,xerr=[[row.coefficient-row.CR1_t_95_low],[row.CR1_t_95_high-row.coefficient]],fmt='o' if o=='dP_real' else 's',color=PURPLE if o=='dP_real' else GOLD,capsize=3)
        deco(ax);ax.set_yticks(range(4),['小学·个人','小学·公用','初中·个人','初中·公用']);ax.invert_yaxis();ax.set_title(['A  专任教师变化','B  班级变化'][k],loc='left');ax.set_xlabel('资源变化的支出关联系数')
    fig.suptitle('资源关联体现在哪一类支出？',fontsize=12);export(fig,'图E3_资源与分项支出')
    (FIG/'图注与阅读说明.md').write_text('''# 资源解释拓展图组

图E1：D=公用支出对数变化−个人支出对数变化。原窗口为2008—2023年，其余四模型均为同一2014—2023年完整资源与经费省年。点为学生变化系数，线为省级聚类CR1及t(G−1)近似单项95%区间。所有模型纳入自身收入变化和省份/年份效应；按标注逐步加入专任教师、班级变化。系数变化可能包含过度控制、内生性与样本窗口影响，不表示中介解释比例。

图E2：同样本同时纳入学生、自身收入、专任教师、班级变化及省份/年份效应。点为D对教师或班级的系数，线为9999次省级约束野生聚类自助检验反演单项95%区间。两个学段×两资源共四项Holm校正；区间非家族同时区间。若置信集搜索未闭合或分離，只展示点并说明，不能用搜索边界冒充置信限。

图E3：图E2的相同样本与设计，分别估计个人、公用实际支出变化。线为省级CR1及t(G−1)近似95%区间，不用区间重叠判断响应差异。专任教师不等于个人支出覆盖的全部人员，班级不等于全部运行成本。

全部为探索性条件关联。资源与经费学校覆盖未完全桥接；公用支出含部分资本性支出，个人不等于纯工资。控制当期资源不能识别因果机制。本轮不评价工资水平、效率、教师裁撤或班额优劣。学校数变化只作敏感性，不等同所有办学网点。三图均纯白、紫金、600 dpi，另存PDF/SVG；两学段共用自身收入，不把重复财政记录当62个独立聚类。
''',encoding='utf8')
    print(tt.to_string(index=False),flush=True)

if __name__=='__main__':main()
