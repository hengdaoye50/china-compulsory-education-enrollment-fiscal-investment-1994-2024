from pathlib import Path
import zipfile,io,json,re,csv,sys,collections
import openpyxl
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/data/年鉴资料核查_20261010'
sys.path.insert(0,str(ROOT/'research/.tmp/yearbook_read_deps'))
sys.stdout.reconfigure(encoding='utf-8')
def name(i):
 s=i.filename
 try:s=s.encode('cp437').decode('gbk')
 except UnicodeError:pass
 return s
def read(b):
 if b[:2]==b'PK':
  w=openpyxl.load_workbook(io.BytesIO(b),read_only=True,data_only=True)
  s=w.worksheets[0]; rows=list(s.iter_rows(values_only=True));w.close()
 else:
  import xlrd
  s=xlrd.open_workbook(file_contents=b).sheet_by_index(0)
  rows=[s.row_values(i) for i in range(s.nrows)]
 return [[str(v).strip() if v is not None else '' for v in r] for r in rows]
catalog=[];edu=[];fiscal=[]
provs='北京 天津 河北 山西 内蒙古 辽宁 吉林 黑龙江 上海 江苏 浙江 安徽 福建 江西 山东 河南 湖北 湖南 广东 广西 海南 重庆 四川 贵州 云南 西藏 陕西 甘肃 青海 宁夏 新疆'.split()
for family in ['中国统计年鉴','中国财政年鉴','中国教育统计年鉴','中国教育经费统计年鉴']:
 for p in sorted((ROOT/family).glob('*.zip')):
  year=int(re.search(r'(19|20)\d{2}',p.name)[0]);z=zipfile.ZipFile(p)
  chosen={}
  for i in z.infolist():
   n=name(i)
   if i.is_dir():continue
   catalog.append({'family':family,'volume_year':year,'archive':str(p.relative_to(ROOT)),'table':n,'bytes':i.file_size})
   if family=='中国教育统计年鉴' and re.search('分布|各地|第.?部分|第二部分',n) and re.search(r'\.(xlsx|xls)$',n):
    base=Path(n).stem
    # Province sheets are under distribution/second part, with Total variant preferred.
    if (re.search('分布|第二部分|第2部分',n) or ('总计' in base and year in [2011,2012])) and not re.search('成人|农村|城市|县镇|女|六年制|民办|职业|少数民族',base):
     stage='小学' if '小学' in base else ('初中' if '初中' in base or '普通中学在校学生' in base else None)
     if stage and re.search('学生|在校',base) and (stage not in chosen or '总计' in base):chosen[stage]=i
   if family=='中国财政年鉴' and re.search(r'\.(xlsx|xls)$',n) and re.search('(?:收支.*决算|预算.*决算.*收支)',n) and not re.search('续表|基金|资本|保险|兵团',n):
    prov=next((s for s in provs if s in Path(n).stem),None)
    if not prov:continue
    rows=read(z.read(i));terms=[];titles=[]
    for ri,r in enumerate(rows,1):
     compact=re.sub(r'\s+','',' '.join(r))
     if re.search('中央补助|税收返还|上解中央|收入总计|全省|本级|全市|全区|预算数|决算数',compact):terms.append({'row':ri,'cells':r})
     if re.search('收支决算总表|ACCOUNT.*(?:REVENUE|BUDGET)',compact,re.I):titles.append({'row':ri,'cells':r})
    fiscal.append({'volume_year':year,'province':prov,'archive':str(p.relative_to(ROOT)),'table':n,'row_count':len(rows),'titles':titles,'terms':terms})
  for stage,i in chosen.items():
   rows=read(z.read(i));regionrows=[]
   for ri,r in enumerate(rows,1):
    # Region names in first two columns only, with spaces removed.
    left=re.sub(r'\s+','',' '.join(r[:2]));matched=next((s for s in provs if s in left),None)
    if matched:regionrows.append({'province':matched,'row':ri,'cells':r})
   edu.append({'data_year_label':year,'stage':stage,'archive':str(p.relative_to(ROOT)),'table':name(i),'headers':rows[:15],'regions':regionrows,'province_count':len(set(r['province'] for r in regionrows))})
  z.close()
with (OUT/'all_archive_tables.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['family','volume_year','archive','table','bytes']);w.writeheader();w.writerows(catalog)
(OUT/'education_province_samples.json').write_text(json.dumps(edu,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'fiscal_province_scope.json').write_text(json.dumps(fiscal,ensure_ascii=False,indent=2),encoding='utf8')
print('EDUCATION',[(s['data_year_label'],s['stage'],s['province_count'],s['table']) for s in edu])
print('FISCAL PROVINCE COUNTS',dict(sorted(collections.Counter(s['volume_year'] for s in fiscal).items())))
print('ALL TABLES',len(catalog))
