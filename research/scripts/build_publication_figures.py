"""Publication figures. Run with --root PATH; input tables remain unchanged."""
from pathlib import Path
import sys,os,json,hashlib,argparse,shutil
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);parser.add_argument('--font',type=Path);parser.add_argument('--output-dir',type=Path);parser.add_argument('--omit-figure-number',action='store_true');args=parser.parse_args()
ROOT=args.root.resolve()
deps=ROOT/'research/.tmp/figure_deps'
if deps.exists():sys.path.insert(0,str(deps))
os.environ['MPLCONFIGDIR']=str(ROOT/'research/.tmp/mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import numpy as np
DATA=ROOT/'research/data'
OUT=args.output_dir.resolve() if args.output_dir else ROOT/'research/figures/正式学术图组_20261011'
for folder in ['png','svg','pdf','figure_data']: (OUT/folder).mkdir(parents=True,exist_ok=True)
font=args.font or Path('C:/Windows/Fonts/msyh.ttc')
if not font.exists(): raise FileNotFoundError('Supply --font with a local Chinese font; fonts are not redistributed.')
font_manager.fontManager.addfont(str(font))
plt.rcParams.update({'font.family':font_manager.FontProperties(fname=font).get_name(),'font.size':9,'axes.titlesize':10,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,'lines.linewidth':1.4,'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white','svg.fonttype':'path','pdf.fonttype':42})
PURPLE='#7E0C6E';GOLD='#B68A3A';TEAL='#3F7F7B';INK='#302A34';GRAY='#999099'
STAGES=['primary','junior'];NAMES={'primary':'小学','junior':'初中'};COLORS={'primary':PURPLE,'junior':GOLD};MARKERS={'primary':'o','junior':'D'}
sources={};captions=[];checks={};combined=PdfPages(OUT/'义务教育三十年历史分析_学术图组.pdf')
def load(relative):
 p=DATA/relative;sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest();return pd.read_csv(p)
def style(ax,grid=True):
 ax.set_axisbelow(True)
 if grid:ax.grid(axis='y',color='#E8E8E8',linewidth=.45)
 ax.tick_params(length=3,color='#666666')
def save(fig,num,title,notes,data):
 ident=f'fig{num:02d}'
 fig.suptitle(title if args.omit_figure_number else f'图{num}  {title}',x=.5,y=.98,fontsize=11,fontweight='bold')
 fig.canvas.draw();renderer=fig.canvas.get_renderer()
 prop=font_manager.FontProperties(size=8)
 wrapped=[]
 for note in notes:
  line=''
  for char in note:
   if line and renderer.get_text_width_height_descent(line+char,prop,False)[0]>.86*fig.bbox.width:
    wrapped.append(line);line=char
   else:line+=char
  wrapped.append(line)
 fig.text(.08,.018,'\n'.join(wrapped),fontsize=8,color=INK,va='bottom',linespacing=1.5)
 fig.canvas.draw()
 from matplotlib.text import Text
 outside=[]
 for artist in fig.findobj(Text):
  if not artist.get_visible() or not artist.get_text():continue
  bb=artist.get_window_extent(fig.canvas.get_renderer())
  if bb.x0 < -1 or bb.y0 < -1 or bb.x1>fig.bbox.width+1 or bb.y1>fig.bbox.height+1:
   outside.append(artist.get_text())
 checks[ident+'_text_within_page']=not outside
 if outside:raise ValueError(f'{ident}: text outside page: {outside}')
 fig.savefig(OUT/'png'/f'{ident}.png',dpi=600)
 fig.savefig(OUT/'svg'/f'{ident}.svg')
 fig.savefig(OUT/'pdf'/f'{ident}.pdf')
 combined.savefig(fig)
 data.to_csv(OUT/'figure_data'/f'{ident}.csv',index=False,encoding='utf-8-sig')
 captions.append({'id':ident,'title':title,'notes':notes,'row_count':len(data),'physical_width_cm':round(fig.get_figwidth()*2.54,2),'physical_height_cm':round(fig.get_figheight()*2.54,2),'dpi':600})
 plt.close(fig)

s=load('三十年纵向分析_20261010/national_students_1995_2024.csv').sort_values(['stage','year'])
assert len(s)==60 and not s.duplicated(['stage','year']).any();checks['national_student_60_unique']=True
fig,axes=plt.subplots(2,1,figsize=(6.5,5.6),sharex=True,sharey=True);fig.subplots_adjust(left=.12,right=.96,top=.88,bottom=.20,hspace=.24)
for ax,stage in zip(axes,STAGES):
 r=s[s.stage==stage];y=r.students/10000
 ax.plot(r.year,y,color=COLORS[stage],marker=MARKERS[stage],markersize=2.8,markevery=3,label=NAMES[stage])
 ax.set_ylim(0,16000);ax.set_ylabel('在校生数（万人）');style(ax);ax.legend(loc='upper right',frameon=False)
 for index in [y.idxmax(),y.idxmin()]:
  row=r.loc[index];val=row.students/10000
  ax.annotate(f'{int(row.year)}年：{val:,.0f}',(row.year,val),xytext=(10,12),textcoords='offset points',fontsize=7.5,arrowprops={'arrowstyle':'-','color':GRAY,'lw':.6})
 ax.annotate(f'{y.iloc[-1]:,.0f}',(2024,y.iloc[-1]),xytext=(-5,-15),textcoords='offset points',ha='right',fontsize=8)
axes[-1].set_xticks([1995,2000,2005,2010,2015,2020,2024]);axes[-1].set_xlim(1994,2025)
save(fig,1,'全国小学与初中在校生人数的变化（1995—2024年）',['来源：《中国教育统计年鉴》，按实际数据年整理。上下两图采用相同纵轴范围。','注：标注所示年份为观察期内人数最多、最少的年份，末端数字为2024年人数。','各年学校类型及统计时点的定义仍待进一步核对；曲线不能直接解释为出生人口变化。'],s)

i=load('早期财政重建_20261011/national_fiscal_1994_2024_report_final.csv').sort_values(['stage','year']).copy()
assert len(i)==62;checks['fiscal_1994_2024_62']=True
fig,axes=plt.subplots(2,1,figsize=(6.5,6.4),sharex=True);fig.subplots_adjust(left=.13,right=.96,top=.89,bottom=.30,hspace=.25)
for stage in STAGES:
 r=i[i.stage==stage]
 for start,end in [(1995,1997),(1998,2001),(2002,2006),(2007,2024)]:
  q=r[r.year.between(start,end)]
  for ax,metric in zip(axes,['fiscal_yi','fiscal_share_pct']):
   ax.plot(q.year,q[metric],color=COLORS[stage],marker=MARKERS[stage],markevery=3,markersize=2.6,label=NAMES[stage] if start==1995 else None)
 model=r[r.year==1994].iloc[0]
 for ax,metric,low,high in [(axes[0],'fiscal_yi',model.fiscal_scenario_low_thousand_yuan/100000,model.fiscal_scenario_high_thousand_yuan/100000),(axes[1],'fiscal_share_pct',model.share_scenario_low_pct,model.share_scenario_high_pct)]:
  ax.errorbar(1994,model[metric],yerr=[[model[metric]-low],[high-model[metric]]],color=COLORS[stage],marker=MARKERS[stage],markerfacecolor='white',markersize=4,capsize=2,linestyle='none',linewidth=.8,zorder=4)
 axes[1].annotate(f'{r.fiscal_share_pct.iloc[-1]:.2f}%',(2024,r.fiscal_share_pct.iloc[-1]),xytext=(-4,-13 if stage=='junior' else 7),textcoords='offset points',ha='right',fontsize=8)
axes[0].set_ylabel('财政性经费（亿元，名义值）');axes[0].set_ylim(bottom=0);axes[0].legend(frameon=False,loc='upper left',ncol=2)
axes[1].set_ylabel('财政性经费占比（%）');axes[1].set_ylim(65,100);axes[1].set_xticks([1994,2000,2005,2010,2015,2020,2024]);axes[1].set_xlim(1993.5,2025)
for a in axes:
 style(a)
 for v in [1997.5,2001.5,2006.5]:a.axvline(v,color=GRAY,lw=.65,ls=':')
axes[0].text(1995.5,.72,'支出',transform=axes[0].get_xaxis_transform(),ha='center',fontsize=7.5)
axes[0].text(2012,.72,'收入',transform=axes[0].get_xaxis_transform(),ha='center',fontsize=7.5)
save(fig,2,'全国小学与初中财政性教育经费及其占比（1994—2024年）',['来源：《中国教育经费统计年鉴》；1994年全国来源及义务教育预算比例见方法附录。','注：1994年空心点为预算比例约束暂估；误差棒为1995—1997年分配比例情景，不是置信区间。','1995—1997年按支出来源重建，1998—2004年按收入来源重建；2005年起读取公布值。','竖虚线及断线标示1998年收支口径、2002年企业经费计入方式、2007年民办经费定义变化。','占比以当年同口径经费总额为分母；不同分段不视为完全可比。金额未扣除物价变化。','2006年千元单位已与国家统计局全国合计核实并恢复。下图纵轴为65%—100%。'],i)

o=load('举办者与地区历史_20261010/organizer_income_weights.csv')
fig,axes=plt.subplots(2,1,figsize=(6.5,5.2),sharex=True,sharey=True);fig.subplots_adjust(left=.12,right=.96,top=.88,bottom=.22,hspace=.25)
for ax,stage in zip(axes,STAGES):
 r=o[(o.stage==stage)&(o.organizer=='private')].sort_values('year')
 ax.plot(r.year,r.income_weight_pct,color=COLORS[stage],marker=MARKERS[stage],markersize=3)
 ax.set_ylabel('民办学校收入占比（%）');ax.set_title(NAMES[stage],loc='left');ax.set_ylim(0,13);style(ax)
 peak=r.loc[r.income_weight_pct.idxmax()];ax.annotate(f'2021年：{peak.income_weight_pct:.2f}%',(2021,peak.income_weight_pct),xytext=(-95,12),textcoords='offset points',fontsize=8,arrowprops={'arrowstyle':'-','color':GRAY,'lw':.6})
 ax.annotate(f'{r.income_weight_pct.iloc[-1]:.2f}%',(2024,r.income_weight_pct.iloc[-1]),xytext=(-3,-15),textcoords='offset points',ha='right',fontsize=8)
axes[-1].set_xticks([2007,2010,2015,2020,2024]);axes[-1].set_xlim(2006.5,2025)
save(fig,3,'民办学校收入占全国同学段教育经费收入的比例',['来源：《中国教育经费统计年鉴》按举办者分类的收入表，时期为2007—2024年。','注：占比=民办学校收入÷全国同学段学校收入×100%，不表示民办学生人数占比。','标注为观察期内最高占比及2024年占比；学校类别变更对跨期比较的影响仍待核实。'],o[o.organizer=='private'])

c=load('三十年纵向分析_20261010/national_finance_composition_1995_2024.csv');c=c[c.school_scope=='local_affiliation'].sort_values(['stage','year'])
fig,ax=plt.subplots(figsize=(6.5,4.4));fig.subplots_adjust(left=.12,right=.96,top=.86,bottom=.34)
for stage in STAGES:
 r=c[c.stage==stage]
 for j,(a,b) in enumerate([(1995,2006),(2007,2013),(2014,2023),(2024,2024)]):
  rr=r[r.year.between(a,b)]
  ax.plot(rr.year,rr.personal_share_of_PC_pct,color=COLORS[stage],marker=MARKERS[stage],markersize=3,label=NAMES[stage] if j==0 else None)
 ax.annotate(f'{r.personal_share_of_PC_pct.iloc[-1]:.2f}%',(2024,r.personal_share_of_PC_pct.iloc[-1]),xytext=(-5,7 if stage=='primary' else -15),textcoords='offset points',ha='right',fontsize=8)
for v in [2006.5,2013.5,2023.5]:ax.axvline(v,color=GRAY,lw=.7,ls=':')
ax.set_ylabel('个人支出占两项支出合计的比例（%）');ax.set_ylim(50,85);ax.set_xlim(1994.5,2025);ax.set_xticks([1995,2000,2005,2010,2015,2020,2024]);style(ax);ax.legend(frameon=False,loc='upper left',ncol=2)
save(fig,4,'地方隶属学校个人支出占个人与公用支出合计的比例',['来源：《中国教育经费统计年鉴》支出明细表，全国地方隶属学校数据，1995—2024年。','注：占比=个人支出÷（个人支出+公用支出）×100%，不含另列基本建设支出。','个人支出不等同于教师工资，公用支出也不只包括日常教学费用。','2007、2014年相关分类或范围变化处分段断线；2024年资本性项目名称变化，单独标示。','1995年初中个人、公用支出有值，可计算本图比例；其总支出尚未核准。'],c)

e=load('省级经费历史分布_20261010/province_finance_real_endpoints.csv')
b=load('三十年综合叙述_20261010/balanced_province_growth_comparison.csv');cohort=json.loads((DATA/'三十年综合叙述_20261010/synthesis_receipt.json').read_text(encoding='utf8'))['balanced_cohorts']['primary']
periods=[(1995,2006),(2007,2013),(2013,2023)];plotrows=[]
fig,axes=plt.subplots(1,2,figsize=(6.5,4.8),sharey=True);fig.subplots_adjust(left=.11,right=.97,top=.86,bottom=.35,wspace=.15)
for ax,stage in zip(axes,STAGES):
 arrays=[]
 for j,(a,z) in enumerate(periods):
  r=e[(e.stage==stage)&(e.start_year==a)&(e.end_year==z)&e.province.isin(cohort)].sort_values('province');assert len(r)==28
  plotrows.append(r);v=r.PC_real_annualized_pct.to_numpy();arrays.append(v)
  ax.scatter(j+1+np.linspace(-.15,.15,len(v)),v,s=10,alpha=.55,color=COLORS[stage],zorder=2)
  expected=b[(b.stage==stage)&(b.start_year==a)&(b.metric=='PC')].common_cohort_median_annualized_pct.iloc[0];assert np.isclose(np.median(v),expected)
  ax.text(j+1,max(v)+1,f'{np.median(v):.2f}',ha='center',fontsize=8,fontweight='bold')
 ax.boxplot(arrays,positions=[1,2,3],widths=.5,showfliers=False,patch_artist=False,boxprops={'color':COLORS[stage]},medianprops={'color':INK,'linewidth':1.2},whiskerprops={'color':COLORS[stage]},capprops={'color':COLORS[stage]})
 ax.set_title(NAMES[stage]);ax.set_xticks([1,2,3],['1995—\n2006','2007—\n2013','2013—\n2023']);ax.set_ylim(0,24);style(ax)
axes[0].set_ylabel('年均实际增长率（%）');checks['fixed_28_medians_match']=True
save(fig,5,'个人与公用支出合计年均实际增长率的地区分布',['来源：地方隶属学校支出原表及各地区居民消费价格指数（CPI）。','注：三个时期均采用相同的28个省级行政单位；四川、重庆、西藏未纳入，原因见方法说明。','每点代表一个地区；横向错位仅为防止重叠。上方数字和箱内横线均表示中位数。','箱体表示第25—75百分位数，须线采用1.5倍四分位距规则；所有地区均以散点显示。','增长率为扣除物价变化后的复合年均增长率。箱线表示地区分布，不是置信区间。'],pd.concat(plotrows))

pair=load('三十年综合叙述_20261010/province_growth_speed_pairs.csv');pair=pair[(pair.metric=='PC')&(pair.earlier_start==2007)].copy()
fig,axes=plt.subplots(1,2,figsize=(6.5,4.5),sharex=True,sharey=True);fig.subplots_adjust(left=.12,right=.97,top=.83,bottom=.32,wspace=.15)
for ax,stage in zip(axes,STAGES):
 r=pair[pair.stage==stage];assert len(r)==28
 ax.scatter(r.earlier_annualized_pct,r.later_annualized_pct,color=COLORS[stage],marker=MARKERS[stage],s=20,alpha=.85)
 ax.plot([0,24],[0,24],ls='--',lw=.8,color=GRAY);ax.set_xlim(0,24);ax.set_ylim(0,24);ax.set_aspect('equal');ax.set_title(NAMES[stage])
 ax.set_xlabel('2007—2013年年均增长率（%）');style(ax)
axes[0].set_ylabel('2013—2023年年均增长率（%）')
save(fig,6,'个人与公用支出合计年均实际增长率的跨时期比较',['来源：地方隶属学校支出原表及各地区CPI；两时期均采用相同的28个省级行政单位。','注：每点表示同一地区两个时期的增长率；虚线表示两时期增长率相等。','虚线下方表示后一时期增长率较低：小学28个地区、初中26个地区。','两轴尺度相同。增长率降低不等于金额下降；跨期分类变化尚未完全消除，不作因果解释。'],pair)

r=e[(e.start_year==2017)&(e.end_year==2023)].copy();assert len(r)==62
order=r[r.stage=='primary'].sort_values('C_real_change_pct').province.tolist()
fig,ax=plt.subplots(figsize=(6.5,8.8));fig.subplots_adjust(left=.15,right=.95,top=.92,bottom=.15)
ax.axvline(0,lw=.8,color=INK)
for y,province in enumerate(order):
 sub=r[r.province==province].set_index('stage');v=[sub.loc[s,'C_real_change_pct'] for s in STAGES]
 ax.plot(v,[y,y],color='#C9C9C9',lw=.7)
 for stage,value in zip(STAGES,v):ax.scatter(value,y,color=COLORS[stage],marker=MARKERS[stage],s=23,label=NAMES[stage] if y==0 else None,zorder=3)
ax.set_yticks(range(31),order);ax.invert_yaxis();ax.set_xlabel('公用支出实际累计增长率（%）');ax.set_xlim(min(r.C_real_change_pct)-6,max(r.C_real_change_pct)+7);ax.legend(frameon=False,ncol=2,loc='upper right');style(ax,False);ax.grid(axis='x',color='#E8E8E8',lw=.45)
save(fig,7,'各地区小学与初中公用支出的实际增长（2017—2023年）',['来源：地方隶属学校公用支出原表及各地区CPI，涵盖31个省级行政单位。','注：横轴为2017—2023年累计实际增长率，不是年均增长率；按小学增长率从低到高排列。','线段连接同一地区的两个学段；零线左侧表示扣除物价变化后的支出金额下降。','公用支出含原表资本性等项目。CPI近似反映一般物价变化，不代表教育专属成本。'],r)

de=load('举办者与地区历史_20261010/fiscal_share_decomposition_totals.csv');de=de[((de.start_year==2014)&(de.end_year==2021))|((de.start_year==2021)&(de.end_year==2024))]
assert np.allclose(de.observed_change_pp,de.composition_pp+de.within_pp);checks['decomposition_identity']=True
fig,axes=plt.subplots(1,2,figsize=(6.5,4.5),sharex=True,sharey=True);fig.subplots_adjust(left=.15,right=.96,top=.80,bottom=.31,wspace=.17)
for ax,stage in zip(axes,STAGES):
 for y,(a,z) in enumerate([(2014,2021),(2021,2024)]):
  row=de[(de.stage==stage)&(de.start_year==a)].iloc[0]
  for off,col,color,label in [(-.18,'composition_pp',PURPLE,'学校类别收入构成变化'),(.18,'within_pp',GOLD,'各类学校内部比例变化')]:
   ax.barh(y+off,row[col],height=.28,color=color,hatch='///' if col=='within_pp' else None,edgecolor=INK,linewidth=0,label=label if y==0 and stage=='primary' else None)
  ax.scatter(row.observed_change_pp,y,marker='D',s=20,color=INK,label='合计变化' if y==0 and stage=='primary' else None,zorder=4)
  ax.text(.97,y,f'合计 {row.observed_change_pp:+.3f}' if abs(row.observed_change_pp)<.01 and row.observed_change_pp>0 else f'合计 {row.observed_change_pp:+.2f}',transform=ax.get_yaxis_transform(),ha='right',va='center',fontsize=7.5)
 ax.axvline(0,color=GRAY,lw=.7);ax.set_title(NAMES[stage]);ax.set_yticks([0,1],['2014—2021','2021—2024']);ax.set_xlim(-6,3.8);ax.set_xlabel('占比变化（百分点）');style(ax,False);ax.grid(axis='x',color='#E8E8E8',lw=.45)
axes[0].invert_yaxis()
fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.915),ncol=3,frameon=False,fontsize=7.5)
save(fig,8,'财政性教育经费收入占比变化的构成分解',['来源：按举办者分类的教育经费收入表。黑色菱形为全国占比变化，单位为百分点。','注：紫色表示各类学校收入占全国收入比例变化的贡献；金色表示各类学校内部财政性收入','比例变化的贡献。两部分相加等于全国占比变化，计算方法见方法说明。','学校类别按年鉴举办者分类；这是算术分解，不表示政策效果或同一批学校的资金变化。'],de)
combined.close()
manifest={'figures':captions,'input_sha256':sources,'checks':checks,'background':'#FFFFFF','palette':{'primary':PURPLE,'junior':GOLD},'font_path_used':str(font),'matplotlib_version':matplotlib.__version__,'inference':'descriptive; no new regression or causal identification','revision_date':'2026-10-11'}
(OUT/'figure_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
text=['# 正式学术图组使用说明','', '本版交付8幅独立学术图。PNG为600 dpi纯白背景，SVG和PDF保留矢量图形。建议在Word中以约16厘米宽插入PNG，锁定纵横比，关闭图片压缩；图题与图注也可另设为正文。','', 'SVG中的文字转为路径，减少跨电脑字体缺失；PDF嵌入字体。矢量几何可以编辑，SVG文字不作为可编辑文本。','', '各图精确数据位于figure_data，来源散列、行数及图注位于figure_manifest.json。图组仅为描述性结果，未添加回归结论或虚构置信区间。','']
for cap in captions:text+=['## '+cap['id']+' '+cap['title'],'']+cap['notes']+['']
(OUT/'图题与图注.md').write_text('\n'.join(text),encoding='utf8')
print('Generated 8 figures in PNG/SVG/PDF, 8 exact chart-data tables, manifest and captions.')
