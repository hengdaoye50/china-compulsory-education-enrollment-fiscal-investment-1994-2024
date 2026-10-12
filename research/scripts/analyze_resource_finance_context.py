"""Parallel trends under explicit scope limits; no matched-student or causal claim."""
import csv,json,sys,hashlib,re
from decimal import Decimal as D
from fractions import Fraction
from parse import ROOT,read as parse_html,save_csv
sys.stdout.reconfigure(encoding='utf-8')
DATA=ROOT/'data'
def read(n):return list(csv.DictReader((DATA/n).open(encoding='utf-8-sig',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pct(a,b):return (D(a)/D(b)-1)*100
def fmt(v):return '' if v is None else str(v)
def sign(v):return 'increase' if v>0 else 'decrease' if v<0 else 'unchanged'
protected=json.loads((DATA/'province_finance_next_protected_baseline.json').read_text(encoding='utf-8'))
def protect():assert all(sha(ROOT/p)==s for p,s in protected.items())
protect()
resource=read('education_resource_panel.csv');resources={(r['province'],r['year'],r['stage']):r for r in resource}
finance=[r for r in read('fiscal_analysis_province_series.csv') if r['affiliation_scope']=='all_affiliations' and r['fund']=='general_budget']
assert len(finance)==434
assert len({(r['province'],r['year'],r['stage']) for r in finance})==434
sources=json.loads((ROOT/'resource_finance_bridge_sources.json').read_text(encoding='utf-8'))
assert all(r['status']=='downloaded' and sha(ROOT/r['path'])==r['sha256'] for r in sources)
receipts={r['key']:r for r in sources}
evidence=[]
def record(key,row,column,metric):
 value=int(row[column]);r=receipts[key]
 evidence.append(dict(metric=metric,value=value,row_label=row[0],column_index=column,source_url=r['url'],raw_file=r['path'],sha256=r['sha256']))
 return value
rows17=parse_html(ROOT/receipts['bridge_2017_students_type']['path']).tables[0]
primary17=record('bridge_2017_students_type',next(r for r in rows17 if '（一）普通小学' in r[0]),3,'2017_regular_primary_stage_total')
assert primary17==int(resources['全国','2017','primary']['students'])
total17=record('bridge_2017_students_type',next(r for r in rows17 if r[0].startswith('1. 初中')),3,'2017_junior_total')
start=next(i for i,r in enumerate(rows17) if r[0].startswith('1. 初中'))
parts17=rows17[start+1:start+6]
assert sum(int(r[3]) for r in parts17)==total17
voc17=record('bridge_2017_students_type',next(r for r in parts17 if '职业初中' in r[0]),3,'2017_junior_vocational_in_five_category_classification')
rowsdetail17=parse_html(ROOT/receipts['bridge_2017_junior_type']['path']).tables[0]
attached17=record('bridge_2017_junior_type',next(r for r in rowsdetail17 if '附设职业初中班' in r[0]),3,'2017_attached_vocational_reference_not_added_to_five_category_total')
rows23=parse_html(ROOT/receipts['bridge_2023_junior_type']['path']).tables[0]
total23=record('bridge_2023_junior_type',next(r for r in rows23 if '总 计' in r[0]),3,'2023_junior_total')
parts23=[r for r in rows23 if any(r[0].startswith(t) for t in ['初级中学','九年一贯制学校','职业初中','完全中学','十二年一贯制学校','附设普通初中班','附设职业初中班'])]
assert len(parts23)==7 and sum(int(r[3]) for r in parts23)==total23
voc23=sum(record('bridge_2023_junior_type',r,3,'2023_vocational_component') for r in parts23 if r[0].startswith(('职业初中','附设职业初中班')))
assert total17==int(resources['全国','2017','junior']['students']) and total23==int(resources['全国','2023','junior']['students'])
types=[dict(year=y,total=total,vocational=vo,ordinary_remainder=total-vo,vocational_share_pct=str(D(vo)/total*100),method=method,limit='national diagnostic only; no provincial or teacher/class adjustment') for y,total,vo,method in [(2017,total17,voc17,'five mutually exclusive categories sum to total; detailed attached100 not added again'),(2023,total23,voc23,'seven mutually exclusive categories sum to total; vocational305 and attached36 added')]]
rowsprimary=parse_html(ROOT/receipts['bridge_2023_primary_organizer']['path']).tables[0]
national_block=rowsprimary[4:10]
primary_total=record('bridge_2023_primary_organizer',national_block[0],7,'2023_primary_total')
assert primary_total==int(resources['全国','2023','primary']['students'])
assert sum(int(r[7]) for r in national_block[1:])==primary_total
gov_primary=sum(record('bridge_2023_primary_organizer',r,7,'2023_primary_government_organizer_students') for r in national_block[1:] if r[0].startswith(('教育部门','其他部门')))
organizer=dict(year=2023,stage='primary',total_students=primary_total,government_department_students=gov_primary,outside_government_students=primary_total-gov_primary,outside_government_pct=str(D(primary_total-gov_primary)/primary_total*100),limit='national end-year education students; not fiscal weighted denominator; not allocated to provinces')

# Re-read the actual 42 resource tables at their annual column positions.
schema=json.loads((DATA/'resource_schemas.json').read_text(encoding='utf-8'))
checks=[];selected=[]
for s in schema:
 if not 2017<=s['year']<=2023 or s['kind'] not in ['students','teachers','classes']:continue
 selected.append((s['year'],s['stage'],s['kind']))
 metric={'students':'students','teachers':'teachers','classes':'classes'}[s['kind']]
 col=s['columns'][metric]
 for row in [r for tab in parse_html(ROOT/s['path']).tables for r in tab]:
  if not row:continue
  region=re.sub(r'\s+','',row[0])
  region=re.sub(r'[A-Za-z()\-]','',region)
  if region in ['总计','全国','合计']:region='全国'
  if (region,str(s['year']),s['stage']) not in resources:continue
  if len(row)<=col or not re.fullmatch(r'\d+',re.sub(r'[,\s]','',row[col])):continue
  val=int(row[col].replace(',','').replace(' ',''));existing=int(resources[region,str(s['year']),s['stage']][metric])
  assert val==existing
  checks.append(dict(year=s['year'],province=region,stage=s['stage'],metric=metric,value=val,status='pass',source_url=s['source'],raw_file=s['path'],column_index=col))
assert len(selected)==len(set(selected))==42 and len(checks)==1344
context=[]
for f in finance:
 r=resources[f['province'],f['year'],f['stage']]
 context.append(dict(province=f['province'],year=f['year'],stage=f['stage'],students=r['students'],teachers=r['teachers'],classes=r['classes'],spending_total_thousand_yuan=f['total'],spending_cpi_adjusted_2017_thousand_yuan=f['cpi_adjusted_total_2017_prices'],spending_career_thousand_yuan=f['career'],students_source=r['students_source'],teachers_source=r['teachers_source'],classes_source=r['classes_source'],spending_source=f['source_file'],resource_scope='all organizers, education stage totals; junior includes vocational',finance_scope='all affiliations ordinary primary/junior, all organizers, general public budget funds',time_scope='fiscal calendar-year flow and education survey reference-time stocks',comparison_status='parallel context only; exact school/organizer/segment match unconfirmed',per_student_or_causal_use=False))
assert len(context)==434
bykey={(r['province'],r['year'],r['stage']):r for r in context}
changes=[]
for r in context:
 previous=bykey.get((r['province'],str(int(r['year'])-1),r['stage']))
 if not previous:continue
 c={k:r[k] for k in ['province','year','stage','comparison_status']}
 for m in ['students','teachers','classes','spending_total_thousand_yuan','spending_cpi_adjusted_2017_thousand_yuan']:
  c[m+'_change_pct']=str(pct(r[m],previous[m]))
  c[m+'_direction']=sign(D(c[m+'_change_pct']))
 changes.append(c)
assert len(changes)==372
summary=[]
for stage in ['primary','junior']:
 for y in range(2018,2024):
  rows=[r for r in changes if r['stage']==stage and r['year']==str(y)]
  assert len(rows)==31
  decreasing=[r for r in rows if r['students_direction']=='decrease']
  summary.append(dict(year=y,stage=stage,province_changes=31,student_decrease_provinces=len(decreasing),student_decrease_and_cpi_adjusted_spending_increase=sum(r['spending_cpi_adjusted_2017_thousand_yuan_direction']=='increase' for r in decreasing),student_decrease_and_nominal_spending_increase=sum(r['spending_total_thousand_yuan_direction']=='increase' for r in decreasing),student_decrease_and_teacher_increase=sum(r['teachers_direction']=='increase' for r in decreasing),student_decrease_and_class_increase=sum(r['classes_direction']=='increase' for r in decreasing),limit='direction co-occurrence across separately scoped series; not matched-school response or inefficiency'))
endpoints=[]
national_fin={(r['year'],r['stage']):r for r in read('fiscal_analysis_national_series.csv') if r['affiliation_scope']=='all_affiliations' and r['fund']=='general_budget'}
for province in sorted({r['province'] for r in context}|{'全国'}):
 for stage in ['primary','junior']:
  a=resources[province,'2017',stage];b=resources[province,'2023',stage]
  x=dict(province=province,stage=stage,start_year=2017,end_year=2023,comparison_status='parallel context, scopes not certified identical')
  for m in ['students','teachers','classes']:x[m+'_change_pct']=str(pct(b[m],a[m]))
  if province=='全国':
   f0=national_fin['2017',stage];f1=national_fin['2023',stage]
   x['spending_nominal_change_pct']=str(pct(f1['total'],f0['total']))
   x['spending_cpi_adjusted_change_pct']=str(pct(f1['cpi_adjusted_total_2017_prices_100m_yuan'],f0['cpi_adjusted_total_2017_prices_100m_yuan']))
  else:
   c0=bykey[province,'2017',stage];c1=bykey[province,'2023',stage]
   x['spending_nominal_change_pct']=str(pct(c1['spending_total_thousand_yuan'],c0['spending_total_thousand_yuan']))
   x['spending_cpi_adjusted_change_pct']=str(pct(c1['spending_cpi_adjusted_2017_thousand_yuan'],c0['spending_cpi_adjusted_2017_thousand_yuan']))
  endpoints.append(x)
formula=[]
for r in changes:
 a=bykey[r['province'],str(int(r['year'])-1),r['stage']];b=bykey[r['province'],r['year'],r['stage']]
 for m in ['students','teachers','classes']:
  exact=(Fraction(b[m])/Fraction(a[m])-1)*100
  assert abs(D(r[m+'_change_pct'])-D(exact.numerator)/D(exact.denominator))<D('1e-20')
  formula.append(dict(province=r['province'],year=r['year'],stage=r['stage'],metric=m,status='pass',method='Decimal percentage vs exact rational'))
for name,rows in [('resource_finance_bridge_source_cells.csv',evidence),('resource_finance_bridge_junior_type.csv',types),('resource_finance_bridge_primary_organizers.csv',[organizer]),('resource_finance_bridge_resource_checks.csv',checks),('resource_finance_parallel_context.csv',context),('resource_finance_parallel_changes.csv',changes),('resource_finance_parallel_summary.csv',summary),('resource_finance_parallel_endpoints.csv',endpoints),('resource_finance_parallel_formula_checks.csv',formula)]:save_csv(DATA/name,rows)
protect()
audit=dict(common_years=list(range(2017,2024)),parallel_province_context_rows=434,annual_change_rows=372,endpoint_rows=64,source_downloads=len(sources),resource_tables_reread=42,resource_original_cells_checked=len(checks),rational_formula_checks=len(formula),resource_finance_student_denominator_matched=False,per_student_calculated=False,causal_models_run=False,protected_files_unchanged=True,charts_updated=False)
(DATA/'resource_finance_bridge_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
print(json.dumps(types,ensure_ascii=False));print(json.dumps(organizer,ensure_ascii=False))
for r in endpoints:
 if r['province']=='全国':print(json.dumps(r,ensure_ascii=False))
for r in summary:print(json.dumps(r,ensure_ascii=False))
all_fin=read('fiscal_analysis_province_series.csv')
sens=[]
for stage in ['primary','junior']:
 for year in range(2018,2024):
  decreases={r['province'] for r in changes if r['year']==str(year) and r['stage']==stage and r['students_direction']=='decrease'}
  for scope in ['all_affiliations','local_affiliation']:
   for fund in ['all_source','fiscal_subsidy','general_budget']:
    selected=[r for r in all_fin if r['year']==str(year) and r['stage']==stage and r['affiliation_scope']==scope and r['fund']==fund and r['province'] in decreases]
    assert len(selected)==len(decreases)
    sens.append(dict(year=year,stage=stage,affiliation_scope=scope,fund=fund,student_decrease_provinces=len(decreases),cpi_adjusted_total_increase=sum(D(r['cpi_adjusted_total_yoy_pct'])>0 for r in selected),cpi_adjusted_career_increase=sum(D(r['cpi_adjusted_career_yoy_pct'])>0 for r in selected),limit='same separately scoped student context; sensitivity changes fiscal definition, not denominator match'))
save_csv(DATA/'resource_finance_parallel_sensitivity.csv',sens)
detail=[r for r in changes if r['year']=='2023' and r['students_direction']=='decrease']
save_csv(DATA/'resource_finance_parallel_2023_declines.csv',detail)
print('2023 funding sensitivity:')
for r in sens:
 if r['year']==2023:print(json.dumps(r,ensure_ascii=False))
audit.update(sensitivity_records=len(sens),declining_student_2023_records=len(detail),national_junior_total_student_change_pct=str(pct(total23,total17)),national_junior_ordinary_remainder_change_pct=str(pct(total23-voc23,total17-voc17)),sensitivity_does_not_certify_scope=True)
(DATA/'resource_finance_bridge_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
protect()
# Companion notebook preserves the reviewed calculations; it was not separately executed.
from pathlib import Path
nb={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},'cells':[{'cell_type':'markdown','metadata':{},'source':['# 资源与财政并列趋势核查\n','2017—2023共同窗口；不同学校覆盖明确保留。不能以此计算官方生均或解释因果。\n']},{'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':['from pathlib import Path\n','import sys\n','script = Path.cwd() / "scripts/analyze_resource_finance_context.py"\n','if not script.exists(): script = Path.cwd() / "research/scripts/analyze_resource_finance_context.py"\n','sys.path.insert(0, str(script.resolve().parent))\n']},{'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':(ROOT/'scripts/analyze_resource_finance_context.py').read_text(encoding='utf-8').split('# Companion notebook preserves')[0].splitlines(keepends=True)}]}
(ROOT/'notebooks/资源财政并列核查.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=2),encoding='utf-8')
