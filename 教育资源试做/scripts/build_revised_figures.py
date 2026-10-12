"""Redraw figures from preserved data; captions and notes live in the report."""
from pathlib import Path
import sys,os,json,hashlib
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'教育资源试做'
OUT=ROOT/'visualizations/地区与统计图组_20261012';OUT.mkdir(exist_ok=True)
source=(BASE/'scripts/build_formal_trend_figures.py').read_text(encoding='utf8')
source=source.replace("ROOT/'visualizations/长期趋势图组_20261012'","ROOT/'visualizations/地区与统计图组_20261012'")
source='\n'.join(line for line in source.splitlines() if not line.lstrip().startswith('fig.text('))
exec(compile(source,str(BASE/'scripts/build_formal_trend_figures.py'),'exec'))
import pandas as pd
import matplotlib.pyplot as plt
FIG=OUT/'图表精修';FIG.mkdir(exist_ok=True)
manifest=[];sources={}
def read(relative):
    p=BASE/relative;sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest();return pd.read_csv(p)
def clean(ax):
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',color='#E8E8E8',lw=.5);ax.set_axisbelow(True)
def save2(fig,name,data):
    for ext in ['png','svg','pdf']:fig.savefig(FIG/f'{name}.{ext}',dpi=600,facecolor='white')
    data.to_csv(FIG/f'{name}.csv',index=False,encoding='utf-8-sig')
    manifest.append({'file':name+'.png','sha256':hashlib.sha256((FIG/(name+'.png')).read_bytes()).hexdigest(),'size_inches':fig.get_size_inches().tolist()});plt.close(fig)
names={'primary':'小学','junior':'初中'};colors={'primary':'#7E0C6E','junior':'#B68A3A'}
d=read('正式学术图组_20261011/figure_data/fig06.csv')
fig,axs=plt.subplots(1,2,figsize=(6.6,3.6),sharex=True,sharey=True);fig.subplots_adjust(left=.12,right=.98,top=.90,bottom=.20,wspace=.18)
for ax,st in zip(axs,names):
    q=d[d.stage==st];ax.scatter(q.earlier_annualized_pct,q.later_annualized_pct,c=colors[st],marker='o' if st=='primary' else 'D',s=18)
    ax.plot([0,24],[0,24],'--',c='#888888',lw=.7);ax.set_xlim(0,24);ax.set_ylim(0,24);ax.set_aspect('equal');ax.set_title(names[st]);ax.set_xlabel('2007—2013年年均实际增长（%）');clean(ax)
axs[0].set_ylabel('2013—2023年年均实际增长（%）');save2(fig,'fig06',d)
d=read('正式学术图组_20261011/figure_data/fig04.csv')
fig,ax=plt.subplots(figsize=(6.6,3.4));fig.subplots_adjust(left=.12,right=.97,top=.96,bottom=.19)
for st in names:
    for lo,hi in [(1995,2006),(2007,2013),(2014,2023),(2024,2024)]:
        q=d[(d.stage==st)&d.year.between(lo,hi)];ax.plot(q.year,q.personal_share_of_PC_pct,c=colors[st],marker='o' if st=='primary' else 'D',ms=3,label=names[st] if lo==1995 else None)
    r=d[(d.stage==st)&(d.year==2024)].iloc[0];ax.annotate(f'{r.personal_share_of_PC_pct:.2f}%',(2024,r.personal_share_of_PC_pct),xytext=(-8,8 if st=='primary' else -14),textcoords='offset points',ha='right')
for x in [2006.5,2013.5,2023.5]:ax.axvline(x,color='#999999',ls=':',lw=.7)
ax.set_ylim(50,85);ax.set_xticks([1995,2000,2005,2010,2015,2020,2024]);ax.set_ylabel('个人占个人与公用合计（%）');ax.set_xlabel('年份');ax.legend(frameon=False,ncol=2);clean(ax);save2(fig,'fig04',d)
d=read('data/资源解释拓展_20261011/all_coefficients_and_sensitivities.csv')
specs=[('previous_full_window','原窗口基准 472条'),('same_sample_baseline','同样本基准 300条'),('teacher_only','加入教师 300条'),('class_only','加入班级 300条'),('joint_resources','共同加入 300条')]
fig,axs=plt.subplots(1,2,figsize=(6.6,3.7),sharex=True);fig.subplots_adjust(left=.20,right=.98,top=.90,bottom=.17,wspace=.55)
for ax,st in zip(axs,names):
    for i,(spec,label) in enumerate(specs):
        r=d[(d.stage==st)&(d.specification==spec)&(d.outcome=='D')&(d.regressor=='dS')].iloc[0]
        ax.errorbar(r.coefficient,4-i,xerr=[[r.coefficient-r.CR1_t_95_low],[r.CR1_t_95_high-r.coefficient]],fmt='o',c=colors[st],capsize=3,ms=4)
    ax.set_yticks(range(5),[x[1] for x in reversed(specs)]);ax.set_ylim(-.4,4.4);ax.axvline(0,c='#888888',lw=.7);ax.set_xlabel('公用减个人：学生系数差');ax.set_title(names[st]);clean(ax)
save2(fig,'图E1_同样本模型比较',d[d.specification.isin([x[0] for x in specs])])
d=read('data/资源解释拓展_20261011/four_resource_contrast_tests.csv')
fig,axs=plt.subplots(1,2,figsize=(6.6,3.0),sharex=True);fig.subplots_adjust(left=.18,right=.98,top=.87,bottom=.22,wspace=.55)
for ax,st in zip(axs,names):
    for i,(reg,label) in enumerate([('dT','教师变化'),('dB','班级变化')]):
        r=d[(d.stage==st)&(d.regressor==reg)].iloc[0];ax.errorbar(r.coefficient,1-i,xerr=[[r.coefficient-r.WCR_95_CI_low],[r.WCR_95_CI_high-r.coefficient]],fmt='o',c=colors[st],capsize=3,ms=4);ax.text(.03,.85-i*.48,f'校正p={r.Holm_four_p:.3f}',transform=ax.transAxes,fontsize=8)
    ax.set_yticks([0,1],['班级变化','教师变化']);ax.set_ylim(-.45,1.45);ax.axvline(0,c='#888888',lw=.7);ax.set_xlabel('公用减个人：资源系数差');ax.set_title(names[st]);clean(ax)
save2(fig,'图E2_资源关联直接差异',d)
d=read('data/支出细项与补助拓展_20261011/primary_subsidy_model_input.csv')
flag=(d.dR_real<0)&(d.dRplusB_real>=0)
fig,ax=plt.subplots(figsize=(6.6,3.5));fig.subplots_adjust(left=.13,right=.97,top=.96,bottom=.18)
ax.scatter(d.loc[~flag,'dR_real']*100,d.loc[~flag,'dRplusB_real']*100,s=12,c='#7E0C6E',alpha=.35,label='其他省年')
ax.scatter(d.loc[flag,'dR_real']*100,d.loc[flag,'dRplusB_real']*100,s=14,c='#B68A3A',alpha=.75,label='自身收入降而合计未降（60条）')
ax.plot([-45,45],[-45,45],'--',c='#888888',lw=.7);ax.axvline(0,c='#888888',lw=.7);ax.axhline(0,c='#888888',lw=.7)
ax.set_xlim(-48,50);ax.set_ylim(-46,47);ax.set_xlabel('自身收入实际对数变化（×100）');ax.set_ylabel('收入加中央补助实际对数变化（×100）');ax.legend(frameon=False,fontsize=8,loc='upper left');clean(ax);save2(fig,'图F5_自身收入与补助合计变化',d)
d=read('data/经费断点再核查_20261012/口径差异核查图数据.csv')
fig,ax=plt.subplots(figsize=(6.6,2.7));fig.subplots_adjust(left=.20,right=.96,top=.96,bottom=.23)
bars=ax.barh(range(4),d.difference_pp,color=[colors[x] for x in d.stage],height=.55)
for j,r in d.iterrows():ax.text(r.difference_pp+(.04 if r.difference_pp>0 else -.04),j,f'{r.difference_pp:+.3f}',ha='left' if r.difference_pp>0 else 'right',va='center')
ax.set_yticks(range(4),d.label);ax.invert_yaxis();ax.set_xlim(-1.6,1.6);ax.axvline(0,c='#888888',lw=.7);ax.set_xlabel('定义差异对财政性占比的影响（百分点）');clean(ax);save2(fig,'口径差异核查图',d)
d=read('正式学术图组_20261011/figure_data/fig07.csv');v=d.pivot(index='province',columns='stage',values='C_real_change_pct').sort_values('primary')
fig,ax=plt.subplots(figsize=(6.6,6.0));fig.subplots_adjust(left=.13,right=.98,top=.97,bottom=.10)
for i,(p,r) in enumerate(v.iterrows()):ax.plot([r.primary,r.junior],[i,i],c='#AAAAAA',lw=.6)
for st in names:ax.scatter(v[st],range(len(v)),c=colors[st],marker='o' if st=='primary' else 'D',s=16,label=names[st])
ax.set_yticks(range(len(v)),v.index,fontsize=8);ax.invert_yaxis();ax.axvline(0,c='#777777',lw=.7);ax.set_xlabel('公用支出累计实际增长（%）');ax.legend(frameon=False,ncol=2,loc='upper right');clean(ax);save2(fig,'fig07',d)
(FIG/'图表精修记录.json').write_text(json.dumps({'figures':manifest,'input_sha256':sources,'statistics_reestimated':False,'background':'white','dpi':600},ensure_ascii=False,indent=2),encoding='utf8')
print('Seven older figures redrawn; data and estimates preserved.')
