"""Explicit, auditable adjudication layer; never rewrites original ledgers."""
from pathlib import Path
import csv,json,hashlib,collections,sys
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'教育资源试做/data/长期财政数据建设_20261010'
OUT=ROOT/'教育资源试做/data/口径核准_20261010'
def read(name):
 with (SRC/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(name,rows):
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def number(r):
 v=r.get('adjudicated_value',r['numeric_candidate'])
 return int(float(v)) if v!='' else None
def main():
 sys.stdout.reconfigure(encoding='utf8')
 ledger=read('raw_value_ledger.csv'); students=[dict(r) for r in ledger if r['metric'].startswith('S')]
 specs=[(2005,'新疆','primary','S_grade1',347901),(2006,'全国','primary','S',107115346),
 (2006,'山西','primary','S_grade4',706371),(2006,'四川','primary','S_grade5',1281101),
 (2007,'全国','junior','S_grade2',19074114),(2008,'湖北','junior','S_grade4',1395),
 (2008,'四川','junior','S_grade4',1897),(2013,'全国','primary','S_grade2',16452428),
 (2005,'贵州','junior','S',2054382),(2016,'广东','junior','S_grade2',1140343)]
 decisions=[]
 for y,p,s,m,v in specs:
  matches=[r for r in students if (r['data_year'],r['province'],r['stage'],r['metric'])==(str(y),p,s,m)]
  assert len(matches)==1
  r=matches[0];r['adjudicated_value']=str(v)
  decisions.append(dict(record_id=r['record_id'],source_id=r['source_id'],year=y,province=p,stage=s,metric=m,cell=r['cell'],raw_value=r['raw_value'],adjudicated_value=v,approval='pending_arithmetic',basis='explicit cell correction; no generic character stripping'))
 groups=collections.defaultdict(list)
 for r in students:groups[(r['data_year'],r['stage'],r['province'])].append(r)
 checks=[]
 for (y,s,p),rs in groups.items():
  t=next(r for r in rs if r['metric']=='S');gs=[r for r in rs if r['metric']!='S']
  known=[number(r) for r in gs if number(r) is not None];blank=len(gs)-len(known)
  ok=number(t)==sum(known)
  checks.append(dict(year=y,stage=s,province=p,check='observed_grade_sum',total=number(t),comparison=sum(known),difference=number(t)-sum(known),blank_grade_cells=blank,status='pass_observed_only' if ok else 'difference'))
 national={}
 for y,s in sorted({(r['data_year'],r['stage']) for r in students}):
  totals=[r for r in students if r['data_year']==y and r['stage']==s and r['metric']=='S']
  n=next(r for r in totals if r['province']=='全国');ps=[r for r in totals if r['province']!='全国']
  diff=number(n)-sum(number(r) for r in ps);national[(y,s)]=diff==0
  checks.append(dict(year=y,stage=s,province='全国',check='province_sum',total=number(n),comparison=sum(number(r) for r in ps),difference=diff,blank_grade_cells='',status='pass_exact' if diff==0 else 'difference'))
 for d in decisions:
  rs=groups[(str(d['year']),d['stage'],d['province'])];total=next(r for r in rs if r['metric']=='S')
  assert number(total)==sum(number(r) for r in rs if r['metric']!='S' and number(r) is not None),d
  assert national[(str(d['year']),d['stage'])],d
  d['approval']='approved_internal_reconstruction'
  d['basis']='exact total versus observed grades AND exact national versus province totals; original retained'
  if d['year']==2013:d['basis']+='; same-year separate national 小学学生数 table confirms 16452428 (student_cross_table_evidence.json)'
  if d['province']=='贵州':d['basis']+='; independent urban 197910 + county 918929 + rural 937543 = 2054382 (student_cross_table_evidence.json)'
  if d['year']==2016:
   d['approval']='approved_official_web_crosscheck'
   d['basis']+='; Ministry of Education 2016 province table explicitly reports grade2=1140343: https://www.moe.gov.cn/jyb_sjzl/moe_560/jytjsj_2016/2016_gd/201708/t20170823_311739.html; urban 626522 + town 409438 + rural 104383 = 1140343; transitional areas are nested subsets, not additive categories'
 totals=[]
 for r in students:
  if r['metric']!='S':continue
  r['adjudicated_value']=str(number(r)); grade=next(c for c in checks if (c['year'],c['stage'],c['province'],c['check'])==(r['data_year'],r['stage'],r['province'],'observed_grade_sum'))
  r['numeric_acceptance']='accepted_source_internal' if grade['difference']==0 and national[(r['data_year'],r['stage'])] and number(r)>0 else 'pending'
  r['blank_grade_cells']=grade['blank_grade_cells'];r['model_eligible']='False'
  r['bridge_status']='school scope and finance affiliation pending; missing grades retained as missing'
  totals.append(r)
 write('student_cell_adjudications.csv',decisions);write('student_numeric_adjudicated.csv',totals);write('student_rechecks.csv',checks)
 mappings={'由东':'山东','_甘肃':'甘肃','陕两':'陕西','山两':'山西','广两':'广西','内蒙占':'内蒙古','黑龙汀':'黑龙江','江两':'江西','两藏':'西藏','浙汀':'浙江'}
 resolved=[];recovered=[]
 dictionaries={r['source_id']:r for r in read('education_finance_table_dictionary.csv')}
 order=['北京','天津','河北','山西','内蒙古','辽宁','吉林','黑龙江','上海','江苏','浙江','安徽','福建','江西','山东','河南','湖北','湖南','广东','广西','海南','重庆','四川','贵州','云南','西藏','陕西','甘肃','青海','宁夏','新疆']
 for r in read('unresolved_region_source_rows.csv'):
  target=mappings[r['raw_region']];row=int(r['source_row'])
  neighbors=sorted({(int(x['source_row']),x['province']) for x in ledger if x['source_id']==r['source_id'] and x['province'] not in ['全国',target]})
  before=[x for x in neighbors if x[0]<row];after=[x for x in neighbors if x[0]>row]
  assert before and after
  j=order.index(target);assert (before[-1][1],after[0][1])==(order[j-1],order[j+1]),r
  r.update(standardized_region=target,previous_row_region=str(before[-1]),next_row_region=str(after[0]),status='approved_label_only_by_unique_standard_order_neighbors; numeric fields unchanged; not model admitted')
  resolved.append(r)
  definition=dictionaries[r['source_id']];values=json.loads(r['raw_row'])
  for metric,cols in json.loads(definition['mappings']).items():
   for col in cols:
    recovered.append(dict(source_id=r['source_id'],data_year=r['year'],stage=r['stage'],province=target,raw_region=r['raw_region'],metric=metric,source_row=row,source_column=col,raw_value=values[col-1],unit=r['unit'],school_scope=r['school_scope'],funding_scope=r['funding_scope'],status='label_recovered_original_value; numeric_and_scope_acceptance_pending',model_eligible=False))
 write('region_label_adjudications.csv',resolved)
 write('finance_label_recovered_candidates.csv',recovered)
 receipt={'student_corrections':len(decisions),'region_label_candidates':len(resolved),'totals':len(totals),'accepted_province_totals':sum(r['province']!='全国' and r['numeric_acceptance']=='accepted_source_internal' for r in totals),'accepted_national_totals':sum(r['province']=='全国' and r['numeric_acceptance']=='accepted_source_internal' for r in totals),'grade_check_differences':[c for c in checks if c['status']=='difference'],'national_checks_passed':sum(c['check']=='province_sum' and c['status']=='pass_exact' for c in checks),'original_input_sha256':{n:hashlib.sha256((SRC/n).read_bytes()).hexdigest() for n in ['raw_value_ledger.csv','student_candidate_series.csv','unresolved_region_source_rows.csv']}}
 (OUT/'adjudication_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(receipt,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
