"""Report-only figures from preserved data; original geographic rings retained."""
from pathlib import Path
import sys,os,json,hashlib
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'教育资源试做'
OUT=ROOT/'visualizations/长期趋势图组_20261012';FIG=OUT/'图表';FIG.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(BASE/'.tmp/figure_deps'));os.environ['MPLCONFIGDIR']=str(BASE/'.tmp/mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager,colors
from matplotlib.patches import Polygon,Patch
import pandas as pd
font_manager.fontManager.addfont('C:/Windows/Fonts/msyh.ttc')
plt.rcParams.update({'font.family':font_manager.FontProperties(fname='C:/Windows/Fonts/msyh.ttc').get_name(),'font.size':9,'axes.unicode_minus':False,'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white','pdf.fonttype':42,'svg.fonttype':'path'})
P='#7E0C6E';G='#B68A3A';manifest=[]
def save(fig,name,data):
    for ext in ['png','pdf','svg']:fig.savefig(FIG/f'{name}.{ext}',dpi=600)
    data.to_csv(FIG/f'{name}.csv',index=False,encoding='utf-8-sig')
    manifest.append(dict(name=name,size_inches=fig.get_size_inches().tolist(),dpi=600,sha256=hashlib.sha256((FIG/f'{name}.png').read_bytes()).hexdigest()))
    plt.close(fig)
f=pd.read_csv(BASE/'data/早期财政重建_20261011/national_fiscal_1994_2024_report_final.csv')
students=pd.read_csv(BASE/'正式学术图组_20261011/figure_data/fig01.csv')
fig,axs=plt.subplots(2,1,figsize=(6.6,3.0),sharex=True,sharey=True);fig.subplots_adjust(left=.12,right=.97,top=.95,bottom=.17,hspace=.29)
for ax,s,c,m,label in zip(axs,['primary','junior'],[P,G],['o','D'],['小学','初中']):
    q=students[students.stage==s].sort_values('year');y=q.students/10000
    ax.plot(q.year,y,color=c,marker=m,markevery=3,ms=2.5,label=label)
    ax.set_ylim(0,16000);ax.set_ylabel('在校生（万人）');ax.legend(loc='upper right',frameon=False);ax.grid(axis='y',color='#E8E8E8',lw=.5);ax.spines[['top','right']].set_visible(False)
    for idx in [y.idxmax(),y.idxmin()]:
        r=q.loc[idx];ax.annotate(f'{int(r.year)}年：{r.students/10000:,.0f}',(r.year,r.students/10000),xytext=(8,7),textcoords='offset points',fontsize=8)
    ax.annotate(f'{y.iloc[-1]:,.0f}',(2024,y.iloc[-1]),xytext=(-4,-13),textcoords='offset points',ha='right',fontsize=8)
axs[-1].set_xticks([1995,2000,2005,2010,2015,2020,2024]);axs[-1].set_xlabel('年份')
save(fig,'全国生源长期趋势',students)
dc=pd.read_csv(BASE/'正式学术图组_20261011/figure_data/fig08.csv')
fig,axs=plt.subplots(1,2,figsize=(6.6,3.25),sharey=True);fig.subplots_adjust(left=.12,right=.98,top=.84,bottom=.20,wspace=.16)
for ax,s,label in zip(axs,['primary','junior'],['小学','初中']):
    q=dc[dc.stage==s].sort_values('start_year');x=list(range(len(q)))
    ax.bar([v-.18 for v in x],q.composition_pp,width=.34,color=P,label='收入权重贡献')
    ax.bar([v+.18 for v in x],q.within_pp,width=.34,color=G,label='组内比例贡献',hatch='//',edgecolor=G)
    ax.plot(x,q.observed_change_pp,'ko',ms=4,label='全国比例变化');ax.axhline(0,color='#777777',lw=.7);ax.set_xticks(x,[f'{r.start_year}—{r.end_year}' for r in q.itertuples()]);ax.set_title(label);ax.set_ylim(-5.3,2.5);ax.grid(axis='y',color='#E8E8E8',lw=.5);ax.set_axisbelow(True);ax.spines[['top','right']].set_visible(False)
axs[0].set_ylabel('占比变化与贡献（百分点）');fig.legend(*axs[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,1.0),ncol=3,frameon=False,fontsize=8)
save(fig,'举办者收入构成分解',dc)
fig,axs=plt.subplots(2,1,figsize=(6.6,4.2),sharex=True);fig.subplots_adjust(left=.13,right=.97,top=.95,bottom=.20,hspace=.30)
for s,c,m,l in [('primary',P,'o','小学'),('junior',G,'D','初中')]:
    r=f[f.stage==s].sort_values('year')
    for ax,col in zip(axs,['fiscal_yi','fiscal_share_pct']):
        for j,(lo,hi) in enumerate([(1995,1997),(1998,2001),(2002,2024)]):
            q=r[r.year.between(lo,hi)];ax.plot(q.year,q[col],color=c,marker=m,markersize=2.7,markevery=3,label=l if j==0 else None)
        q=r[r.year==1994];ax.scatter(q.year,q[col],facecolors='white',edgecolors=c,marker=m,s=28,zorder=4)
        ax.grid(axis='y',color='#E8E8E8',linewidth=.5);ax.spines[['top','right']].set_visible(False)
        for v in [1997.5,2001.5,2006.5]:ax.axvline(v,color='#AAA2AA',ls=':',lw=.65)
    axs[1].annotate(f'{r.fiscal_share_pct.iloc[-1]:.2f}%',(2024,r.fiscal_share_pct.iloc[-1]),xytext=(-4,7 if s=='primary' else -13),textcoords='offset points',ha='right',fontsize=8)
axs[0].set_ylabel('财政性经费（亿元，名义值）');axs[0].set_ylim(bottom=0);axs[0].legend(frameon=False,ncol=2,loc='upper left')
axs[1].set_ylabel('财政性经费占比（%）');axs[1].set_ylim(65,100);axs[1].set_xlim(1993.5,2025);axs[1].set_xticks([1994,2000,2005,2010,2015,2020,2024]);axs[1].set_xlabel('年份')
fig.text(.13,.045,'1994年空心点为条件估算；1995—1997年为支出来源重建，其后为收入。\n1998、2002年处分段；2007年标示来源组成调整，连接线仅用于历史描述。',fontsize=8)
save(fig,'财政性经费长期趋势',f)
qt=pd.read_csv(BASE/'data/定量深化_20261011/four_direct_contrast_tests.csv')
fig,axs=plt.subplots(1,2,figsize=(6.6,3.55),sharex=True);fig.subplots_adjust(left=.09,right=.98,top=.87,bottom=.22,wspace=.30)
for k,reg in enumerate(['dS','dR_real']):
    ax=axs[k]
    for j,(s,c,m) in enumerate([('primary',P,'o'),('junior',G,'s')]):
        row=qt[(qt.stage==s)&(qt.regressor==reg)].iloc[0]
        ax.errorbar(row.coefficient,j,xerr=[[row.coefficient-row.WCR_95_CI_low],[row.WCR_95_CI_high-row.coefficient]],fmt=m,color=c,capsize=3,markersize=5)
        ax.text(.02,.92-j*.12,f'{["小学","初中"][j]}：校正p＝{row.Holm_four_p:.4f}',transform=ax.transAxes,fontsize=8)
    ax.set_yticks([0,1],['小学','初中']);ax.set_ylim(-.5,1.7);ax.axvline(0,color='#777777',lw=.7);ax.grid(axis='x',color='#EEEEEE',lw=.5);ax.spines[['top','right']].set_visible(False)
    ax.set_title(['A  区域生源变化','B  自身财政收入实际变化'][k],fontsize=9.5);ax.set_xlabel('公用减个人的响应系数差')
save(fig,'个人公用直接响应差',qt)
raw=BASE/'data/地图来源_20261012/china_provinces_original.geojson';geo=json.loads(raw.read_text(encoding='utf8'))
d=pd.read_csv(BASE/'正式学术图组_20261011/figure_data/fig07.csv')
codes={11:'北京',12:'天津',13:'河北',14:'山西',15:'内蒙古',21:'辽宁',22:'吉林',23:'黑龙江',31:'上海',32:'江苏',33:'浙江',34:'安徽',35:'福建',36:'江西',37:'山东',41:'河南',42:'湖北',43:'湖南',44:'广东',45:'广西',46:'海南',50:'重庆',51:'四川',52:'贵州',53:'云南',54:'西藏',61:'陕西',62:'甘肃',63:'青海',64:'宁夏',65:'新疆'}
palette=['#B68A3A','#F0E5EF','#D2A2C9','#AB5A9D','#7E0C6E'];labels=['小于0%','0%—不足25%','25%—不足50%','50%—不足100%','100%及以上']
def color(v):return palette[0 if v<0 else 1 if v<25 else 2 if v<50 else 3 if v<100 else 4]
def shapes(ax,lookup,annotate=False):
    matched=set()
    for ft in geo['features']:
        code=ft['properties'].get('adcode');jd=code=='100000_JD'
        province=codes.get(int(code)//10000) if not jd else None
        val=lookup.get(province);face='#333333' if jd else color(val) if val is not None else '#EEEEEE'
        if province is not None and val is not None:matched.add(province)
        geom=ft['geometry'];polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
        for rings in polys:
            for k,ring in enumerate(rings):ax.add_patch(Polygon(ring,closed=True,facecolor=face if k==0 else 'white',edgecolor='#555555',linewidth=.35))
        if annotate and province and val is not None:
            center=ft['properties'].get('centroid') or ft['properties'].get('center')
            if center and province not in ['北京','天津','上海','香港','澳门']:
                ax.text(*center,province,fontsize=7,color='white' if val>=50 else '#302A34',ha='center',va='center')
    ax.set_aspect(1.2);ax.set_xticks([]);ax.set_yticks([])
    for sp in ax.spines.values():sp.set_visible(False)
    return matched
for s,label in [('primary','小学'),('junior','初中')]:
    q=d[d.stage==s];assert len(q)==31 and q.province.nunique()==31
    lookup=dict(zip(q.province,q.C_real_change_pct))
    fig=plt.figure(figsize=(6.7,4.9));ax=fig.add_axes([.025,.16,.93,.80]);matched=shapes(ax,lookup,True);assert len(matched)==31
    ax.set_xlim(73,135);ax.set_ylim(16,54)
    inset=fig.add_axes([.805,.225,.145,.25]);shapes(inset,lookup);inset.set_xlim(105,125);inset.set_ylim(3,25)
    for sp in inset.spines.values():sp.set_visible(True);sp.set_linewidth(.5)
    inset.set_title('南海诸岛',fontsize=7,pad=2)
    fig.legend(handles=[Patch(facecolor=c,edgecolor='#777777',label=l) for c,l in zip(palette,labels)]+[Patch(facecolor='#EEEEEE',edgecolor='#777777',label='未纳入分析')],loc='lower center',bbox_to_anchor=(.5,.045),ncol=3,frameon=False,fontsize=8)
    fig.text(.03,.01,'地方隶属学校；2017—2023年累计实际增长。港澳台未纳入数据分析。',fontsize=8)
    save(fig,f'{label}公用支出空间分布',q)
(FIG/'图表生成记录.json').write_text(json.dumps(dict(figures=manifest,map_source=json.loads((raw.parent/'source.json').read_text()),map_features=len(geo['features']),matched_provinces_each_stage=31,bins='negative, 0-25,25-50,50-100,>=100; identical for both stages',geography='original rings retained; main map and South China Sea inset; unanalysed regions gray'),ensure_ascii=False,indent=2),encoding='utf8')
print('Finance trend and two provincial maps exported; 31 provinces matched per stage.')
