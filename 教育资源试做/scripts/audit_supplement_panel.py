from pathlib import Path
import openpyxl,re,json,collections,sys
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'教育资源试做/data/年鉴资料核查_20261010'
sys.stdout.reconfigure(encoding='utf-8')
p=next((ROOT/'中国统计年鉴').rglob('*.xlsx'))
w=openpyxl.load_workbook(p,read_only=True,data_only=True)
s=w['原始数据-长面板']; rows=s.iter_rows(values_only=True);header=next(rows)
result={}
for row in rows:
 metric=str(row[4] or '')
 if not re.search('地方.*(?:财政|预算).*(?:收入|支出)|居民消费价格指数|(?:小学|初中).*在校|年末常住人口|地区生产总值',metric):continue
 # Preserve only original observations and missing cells; no filled worksheets used.
 item=result.setdefault(str(row[5]),{'metric':metric,'unit':str(row[6]),'regions':set(),'coverage':collections.Counter(),'examples_2024':[]})
 item['regions'].add(row[1])
 for y,v in zip(header[7:],row[7:]):
  if v is not None and str(v).strip() not in ['', '-', '--', '—','nan']:
   item['coverage'][str(y)]+=1
 idx=next((i for i,h in enumerate(header) if str(h)=='2024'),None)
 if idx is not None and row[idx] is not None and len(item['examples_2024'])<2:item['examples_2024'].append({'region':row[1],'value':row[idx]})
w.close()
for v in result.values():v['regions']=sorted(v['regions']);v['coverage']=dict(v['coverage'])
(OUT/'supplement_panel_coverage.json').write_text(json.dumps({'source':str(p.relative_to(ROOT)),'worksheet':'原始数据-长面板','header':list(header),'metrics':result},ensure_ascii=False,indent=2),encoding='utf8')
print([(k,v['coverage'].get('1995',0),v['coverage'].get('2024',0)) for k,v in result.items() if v['metric'] in ['居民消费价格指数(上年=100)','地方财政一般预算收入','地方财政一般预算支出','地区生产总值']])
