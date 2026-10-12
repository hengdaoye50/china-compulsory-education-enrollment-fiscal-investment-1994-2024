from pathlib import Path
import csv,json,math
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'教育资源试做/设计方案/南开紫配色_20261010'
OUT.mkdir(parents=True,exist_ok=True)
BG='#FAF8F5'; INK='#302A34'; MUTED='#746B77'; GRID='#E5DFE5'
PURPLE='#7E0C6E'; GOLD='#B68A3A'
SEQ=['#F4E8F2','#E5CBE0','#CFA3C6','#B775AB','#9D448E',PURPLE,'#520848']
CAT=[PURPLE,GOLD,'#3F7F7B','#526B9B','#B96678','#77834B','#9A83B3']
NAMES=['南开紫','哑光金','青玉绿','烟蓝','豆沙红','橄榄绿','灰薰衣草']
def font(n,bold=False):return ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc' if bold else 'C:/Windows/Fonts/msyh.ttc',n)
def txt(d,xy,s,n=24,fill=INK,bold=False):d.text(xy,s,font=font(n,bold),fill=fill)
def base(title,subtitle,h):
 im=Image.new('RGB',(1600,h),BG);d=ImageDraw.Draw(im)
 d.rectangle((64,58,74,116),fill=PURPLE)
 txt(d,(96,48),title,46,bold=True);txt(d,(96,117),subtitle,23,MUTED)
 return im,d
def rgb(h):return tuple(int(h[i:i+2],16) for i in (1,3,5))

im,d=base('南开紫 × 哑光金','配色提案 01  /  色阶、主辅色与七色类别搭配',1160)
txt(d,(64,199),'主色与拼色',29,bold=True)
for x,c,title,sub in [(64,PURPLE,'南开紫  #7E0C6E','RGB 126 · 12 · 110'),(565,GOLD,'哑光金  #B68A3A','RGB 182 · 138 · 58')]:
 d.rounded_rectangle((x,255,x+460,405),radius=8,fill=c)
 txt(d,(x+26,282),title,29,'#FFFFFF',True)
 txt(d,(x+26,333),sub,22,'#FFFFFF' if c==PURPLE else INK)
txt(d,(1070,273),'浅底 + 深色文字',26,bold=True)
txt(d,(1070,320),'紫色承担视觉重心',23,MUTED)
txt(d,(1070,363),'金色用于比较与点睛',23,MUTED)
txt(d,(64,458),'单色渐变  /  低值 → 高值',29,bold=True)
for i,c in enumerate(SEQ):
 x=64+i*210
 d.rectangle((x,521,x+200,620),fill=c)
 txt(d,(x+14,638),c,23);txt(d,(x+14,674),f'{i+1:02d}',19,MUTED)
txt(d,(64,743),'七色类别搭配  /  无大小顺序',29,bold=True)
for i,(c,name) in enumerate(zip(CAT,NAMES)):
 x=64+i*210
 d.rectangle((x,806,x+200,891),fill=c)
 txt(d,(x+7,908),name,23);txt(d,(x+7,946),c,22,MUTED)
d.line((64,1015,1530,1015),fill=GRID,width=2)
txt(d,(64,1048),'默认紫金两色；类别增多再扩展。数值色阶与类别配色分别使用。',24)
im.save(OUT/'01_配色与色阶.png')

im,d=base('三十年历史数据 · 配色试样','配色提案 02  /  真实研究数据，检验紫金对比与阅读层级',1420)
txt(d,(64,198),'全国在校生规模',30,bold=True)
txt(d,(64,247),'1995—2024年 · 单位：百万人',22,MUTED)
for x,c,name in [(1140,PURPLE,'小学'),(1335,GOLD,'初中')]:
 d.line((x,213,x+55,213),fill=c,width=6);txt(d,(x+70,194),name,24)
rows=list(csv.DictReader((ROOT/'教育资源试做/data/三十年纵向分析_20261010/national_students_1995_2024.csv').open(encoding='utf-8-sig')))
left,right,top,bottom=145,1485,321,702
def xx(y):return left+(y-1995)/29*(right-left)
def yy(v):return bottom-v/160*(bottom-top)
for v in [0,40,80,120,160]:
 y=yy(v);d.line((left,y,right,y),fill=GRID,width=2);txt(d,(78,y-17),str(v),21,MUTED)
for year in [1995,2000,2005,2010,2015,2020,2024]:txt(d,(xx(year)-27,bottom+17),str(year),20,MUTED)
for stage,c in [('primary',PURPLE),('junior',GOLD)]:
 rr=sorted([r for r in rows if r['stage']==stage],key=lambda r:int(r['year']))
 pts=[(xx(int(r['year'])),yy(float(r['students'])/1e6)) for r in rr]
 d.line(pts,fill=c,width=6)
 for j,(x,y) in enumerate(pts):
  if j%5==0 or j==29:
   if stage=='primary':d.ellipse((x-5,y-5,x+5,y+5),fill=c)
   else:d.polygon([(x,y-7),(x+7,y),(x,y+7),(x-7,y)],fill=c)
 x,y=pts[-1];txt(d,(x-100,y-43),f"{float(rr[-1]['students'])/1e6:.2f}",24,INK,True)
txt(d,(64,776),'同一28省 · 个人、公用支出合计年均实际增速中位数',29,bold=True)
txt(d,(64,825),'单位：%  /  省级CPI调整，各窗口单独计算',22,MUTED)
data=list(csv.DictReader((ROOT/'教育资源试做/data/三十年综合叙述_20261010/balanced_province_growth_comparison.csv').open(encoding='utf-8-sig')))
left,right,top,bottom=145,1485,900,1190
for v in [0,5,10,15]:
 y=bottom-v/16*(bottom-top);d.line((left,y,right,y),fill=GRID,width=2);txt(d,(88,y-16),str(v),21,MUTED)
for i,(a,b) in enumerate([(1995,2006),(2007,2013),(2013,2023)]):
 mid=left+(i+.5)*(right-left)/3
 for stage,c,dx in [('primary',PURPLE,-82),('junior',GOLD,14)]:
  r=next(r for r in data if r['stage']==stage and int(r['start_year'])==a and r['metric']=='PC')
  val=float(r['common_cohort_median_annualized_pct']);x=mid+dx;y=bottom-val/16*(bottom-top)
  d.rectangle((x,y,x+68,bottom),fill=c);txt(d,(x-3,y-40),f'{val:.2f}',23,INK,True)
 txt(d,(mid-102,bottom+19),f'{a}—{b}',24)
txt(d,(64,1281),'来源：用户提供年鉴及已核准研究数据。学生与经费覆盖范围不同，不计算生均值。',21,MUTED)
txt(d,(64,1323),'同省比较仍保留分类变化限制；中位数不是全国加权增速，不表示政策因果效应。',21,MUTED)
im.save(OUT/'02_真实数据配色试样.png')

tokens={'primary':PURPLE,'gold':GOLD,'gold_text':'#805E21','gold_light':'#E8D8AF','gold_dark':'#8D682A','sequential_low_to_high':SEQ,'categorical':dict(zip(NAMES,CAT)),'background':BG,'text':INK,'muted_text':MUTED,'grid':GRID,'notes':['紫金为默认双系列配色；七色为类别扩展，不用于有序数值。','深紫是高值，浅紫是低值；缺失用灰色并另标缺失。','金色填充配深色文字，小字号金色文字采用gold_text。','颜色与直接标签、标记形状配合；不宣称七色适用于所有色觉条件。','默认类别使用纯色；渐变装饰限制在标题或少量背景，避免改变数值辨识。']}
(OUT/'配色参数.json').write_text(json.dumps(tokens,ensure_ascii=False,indent=2),encoding='utf8')
print(OUT)
