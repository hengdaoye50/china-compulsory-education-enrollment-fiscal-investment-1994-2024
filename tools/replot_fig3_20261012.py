from pathlib import Path
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research'
OUT=ROOT/'visualizations/地区与统计图组_20261012/图表'
OUT.mkdir(parents=True,exist_ok=True)
font_path=os.environ.get('MPL_CJK_FONT')
if font_path:
    font_manager.fontManager.addfont(font_path)
    font_name=font_manager.FontProperties(fname=font_path).get_name()
else:
    available={f.name for f in font_manager.fontManager.ttflist}
    font_name=next((n for n in ['Microsoft YaHei','Noto Sans CJK SC','Source Han Sans SC','SimHei'] if n in available),None)
    if font_name is None:raise RuntimeError('请将MPL_CJK_FONT设置为本机中文字体文件路径。')
plt.rcParams.update({'font.family':font_name,'font.size':9,'axes.unicode_minus':False,'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white','pdf.fonttype':42,'svg.fonttype':'path'})
P='#7E0C6E';G='#B68A3A'
dc=pd.read_csv(BASE/'figures/正式学术图组_20261011/figure_data/fig08.csv')
fig,axs=plt.subplots(1,2,figsize=(6.6,3.25),sharey=True);fig.subplots_adjust(left=.12,right=.98,top=.84,bottom=.20,wspace=.16)
for ax,s,label in zip(axs,['primary','junior'],['小学','初中']):
    q=dc[dc.stage==s].sort_values('start_year');x=list(range(len(q)))
    ax.bar([v-.18 for v in x],q.composition_pp,width=.34,color=P,label='收入权重贡献')
    ax.bar([v+.18 for v in x],q.within_pp,width=.34,color=G,label='组内比例贡献',hatch='//',edgecolor=G)
    ax.plot(x,q.observed_change_pp,'ko',ms=4,label='全国比例变化');ax.axhline(0,color='#777777',lw=.7);ax.set_xticks(x,[f'{r.start_year}—{r.end_year}' for r in q.itertuples()]);ax.set_title(label);ax.set_ylim(-5.3,2.5);ax.grid(axis='y',color='#E8E8E8',lw=.5);ax.set_axisbelow(True);ax.spines[['top','right']].set_visible(False)
axs[0].set_ylabel('占比变化与贡献（百分点）');fig.legend(*axs[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,1.0),ncol=3,frameon=False,fontsize=8)

for ext in ['png','pdf','svg']: fig.savefig(OUT/f'举办者收入构成分解.{ext}',dpi=600,facecolor='white')
dc.to_csv(OUT/'举办者收入构成分解.csv',index=False,encoding='utf-8-sig')
