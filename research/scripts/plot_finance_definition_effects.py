"""Show deterministic accounting differences, never sampling uncertainty."""
from pathlib import Path
import sys,os,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/.tmp/figure_deps'))
os.environ['MPLCONFIGDIR']=str(ROOT/'research/.tmp/mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd
from PIL import Image
OUT=ROOT/'research/data/经费断点再核查_20261012'
a=pd.read_csv(OUT/'企业来源统一口径候选.csv')
b=pd.read_csv(OUT/'2007财政性分子逐项核对.csv')
rows=[]
for s,label in [('primary','小学'),('junior','初中')]:
    r=a[(a.year==2001)&(a.stage==s)].iloc[0]
    rows.append(dict(year=2001,stage=s,label=f'2001年 {label}',difference_pp=r.adjusted_share_pct-r.published_share_pct,amount_yi=r.adjustment_yi,definition='企业拨款及产业收入－企业总收入'))
for s,label in [('primary','小学'),('junior','初中')]:
    r=b[b.stage==s].iloc[0]
    rows.append(dict(year=2007,stage=s,label=f'2007年 {label}',difference_pp=r.share_difference_pp,amount_yi=r.additional_identified_yi,definition='完整财政性组成－沿用旧表可识别组成'))
df=pd.DataFrame(rows)
df.to_csv(OUT/'口径差异核查图数据.csv',index=False,encoding='utf-8-sig')
font_manager.fontManager.addfont('C:/Windows/Fonts/msyh.ttc')
with plt.rc_context({'font.family':font_manager.FontProperties(fname='C:/Windows/Fonts/msyh.ttc').get_name(),'font.size':9,'axes.unicode_minus':False,'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white','pdf.fonttype':42,'svg.fonttype':'path'}):
    fig,ax=plt.subplots(figsize=(6.6,4.3))
    fig.subplots_adjust(left=.20,right=.96,bottom=.36,top=.82)
    colors=['#7E0C6E' if s=='primary' else '#B68A3A' for s in df.stage]
    bars=ax.barh(range(4),df.difference_pp,color=colors,height=.55,edgecolor='#444444',linewidth=.5)
    for bar,s in zip(bars,df.stage):
        if s=='junior':bar.set_hatch('//')
    ax.set_yticks(range(4),df.label);ax.invert_yaxis()
    ax.set_xlim(-1.6,1.6);ax.set_xticks([-1.5,-1,-.5,0,.5,1,1.5])
    ax.set_xlabel('计算定义差异对财政性经费占比的影响（百分点）')
    ax.axvline(0,color='#555555',linewidth=.8)
    ax.set_axisbelow(True);ax.grid(axis='x',color='#E8E8E8',linewidth=.5)
    ax.spines[['top','right','left']].set_visible(False)
    for j,r in df.iterrows():
        pos=r.difference_pp+(.055 if r.difference_pp>=0 else -.055)
        ax.text(pos,j,f'{r.difference_pp:+.3f}',va='center',ha='left' if pos>0 else 'right',fontsize=9)
    fig.suptitle('财政性教育经费两处口径衔接的量化核查',y=.96,fontsize=11,fontweight='bold')
    fig.text(.20,.86,'2001年：企业项重算；2007年：新表单列公共资金的组成差额',fontsize=8.5)
    notes='注：四个差额均由原表组成项计算，表示定义差异，不是年度增长或统计误差。\n2001年重算扣除企业学校学杂费及其他收入；2007年差额为企业、民办学校\n预算内资金及教育税费。2006年未独立列项，不能据此认定这些资金当年为零。\n来源：相应《中国教育经费统计年鉴》原表；详见配套数据及来源记录。'
    fig.text(.06,.045,notes,fontsize=8,linespacing=1.5,va='bottom')
    fig.canvas.draw()
    from matplotlib.text import Text
    outside=[]
    for t in fig.findobj(Text):
        if t.get_visible() and t.get_text():
            bb=t.get_window_extent(fig.canvas.get_renderer())
            if bb.x0<0 or bb.y0<0 or bb.x1>fig.bbox.width or bb.y1>fig.bbox.height:outside.append(t.get_text())
    assert not outside,outside
    for ext in ['png','pdf','svg']:fig.savefig(OUT/f'口径差异核查图.{ext}',dpi=600)
    plt.close(fig)
img=Image.open(OUT/'口径差异核查图.png')
assert img.getpixel((0,0))[:3]==(255,255,255)
manifest=dict(dimensions_cm=[16.764,10.922],png_pixels=img.size,dpi=600,background='white',uncertainty='none; deterministic accounting differences',input_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'企业来源统一口径候选.csv',OUT/'2007财政性分子逐项核对.csv']},matplotlib_version=matplotlib.__version__,text_bounds_passed=True)
(OUT/'口径差异核查图导出记录.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print('Figure exported in PNG/PDF/SVG; text bounds and white background verified.')
