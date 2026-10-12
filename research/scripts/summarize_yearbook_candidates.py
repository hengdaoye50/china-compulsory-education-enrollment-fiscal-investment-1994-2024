"""Separate candidate panel and explicit exception ledger. Never edits main panels."""
import csv, json, hashlib, sys
from decimal import Decimal as D
from collections import defaultdict
from parse import ROOT, save_csv
sys.stdout.reconfigure(encoding='utf-8')
DATA=ROOT/'data'
def read(name):return list(csv.DictReader((DATA/name).open(encoding='utf-8-sig',newline='')))
protected=json.loads((DATA/'province_finance_next_protected_baseline.json').read_text(encoding='utf-8'))
def verify():assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==s for p,s in protected.items())
verify()
amounts=read('yearbook_stage_spending_candidates.csv')
groups=defaultdict(dict)
for r in amounts:
 if r['province'] in ['全国','大连','宁波','厦门','青岛','深圳']:continue
 key=(r['province'],r['year'],r['stage'],r['affiliation_scope'])
 groups[key][(r['part'],r['metric'])]=r
out=[]
for (province,year,stage,scope),cells in sorted(groups.items()):
 r=dict(province=province,year=year,stage=stage,affiliation_scope=scope,unit='千元',source_type='user supplied Excel compilation',status='candidate only; original publisher provenance and annual school coverage pending',fiscal_student_denominator='',denominator_status='not obtained; no reconstruction')
 for part,label in [('4','all_source'),('5','fiscal_subsidy'),('6','general_budget')]:
  for metric in ['total','personal','public','construction']:
   c=cells[part,metric];r[label+'_'+metric]=c['value'];r[label+'_'+metric+'_source']=c['file']+'#'+c['sheet']+'!'+c['cell']
  r[label+'_career_personal_plus_public']=str(D(cells[part,'personal']['value'])+D(cells[part,'public']['value']))
 r['career_calculation']='derived sum of original personal and public spending; construction excluded; no students used'
 r['source_detail_alert']='part5 E31 raw .4470162; fine component unresolved, headline amounts retained' if (province,year,stage,scope)==('贵州','2017','junior','all_affiliations') else ''
 r['per_student_alert']='part7 C37 differs from announcement by 0.01 yuan; no correction' if (province,year,stage,scope)==('新疆','2017','primary','local_affiliation') else ''
 out.append(r)
assert len(out)==868 and sum(r['affiliation_scope']=='local_affiliation' for r in out)==434
save_csv(DATA/'yearbook_province_stage_spending_candidate_panel.csv',out)
raw=read('yearbook_stage_source_cells.csv')
exceptions=[]
for x in read('yearbook_announcement_cell_checks.csv'):
 if x['status']=='difference_to_investigate':exceptions.append(dict(kind='province per-student mismatch',province=x['province'],year=x['year'],stage=x['stage'],file=x['file'],cell=x['cell'],original_value=x['yearbook_value'],reference_value=x['announcement_value'],difference=x['difference'],resolution='unresolved; original values preserved; consult original publisher cell',reference_source=x['announcement_source']))
for x in read('yearbook_stage_arithmetic_checks.csv'):
 if x['status']=='unresolved':
  e=next(r for r in raw if r['file']==x['file'] and r['cell']=='E31')
  companion=next(r for r in raw if r['volume_year']=='2018' and '5-34_' in r['file'] and r['cell']=='E31')
  exceptions.append(dict(kind='fine component arithmetic anomaly',province=x['province'],year=x['year'],stage=x['stage'],file=x['file'],cell='E31',original_value=e['value'],reference_value=companion['value'],difference=x['difference'],resolution='unresolved; no silent correction; affected fine component isolated, headline B/C/G/L retained',reference_source=companion['file']+'#'+companion['sheet']+'!E31'))
assert len(exceptions)==2
save_csv(DATA/'yearbook_stage_exception_ledger.csv',exceptions)
scope=[
 dict(topic='plan-listed cities',basis='Education Ministry Finance Department answer, 2021-04-27',url='https://hudong.moe.gov.cn/jyb_hygq/hygq_zczx/moe_1346/moe_1351/202104/t20210427_528714.html',finding='Parts 2-7 province statistics already include plan-listed cities; never add the five city rows again',evidence_type='official page text retrieved through web search; hudong raw HTML HTTP404 retained; www alternative receipt recorded separately',limit='not a proof of identical organizer coverage with resource statistics'),
 dict(topic='affiliation versus organizer',basis='Education Ministry Finance Department answer, 2023-06-23',url='https://www.moe.gov.cn/jyb_hygq/hygq_zczx/moe_1346/moe_1351/202307/t20230724_1070556.html',finding='Central/local describes affiliation; education and other departments describes government organizers; these are different dimensions',evidence_type='official web text plus download receipt',limit='answer discusses 2021 volume; audit annual headers, do not automatically assume all annual scopes identical'),
 dict(topic='nested funds',basis='same official 2023-06-23 answer',url='https://www.moe.gov.cn/jyb_hygq/hygq_zczx/moe_1346/moe_1351/202307/t20230724_1070556.html',finding='Education spending contains fiscal subsidy spending; subsidy contains general budget career and construction spending; three parts must not be added',evidence_type='official web text plus download receipt',limit='government fund spending etc within subsidy; no claim only two funding sources'),
 dict(topic='public spending includes capital',basis='Education Ministry Finance Department answer, 2024-01-12; local notes',url='https://www.moe.gov.cn/jyb_hygq/hygq_zczx/moe_1346/moe_1351/202401/t20240112_1099927.html',finding='General public budget public spending includes goods/services and capital; not purely recurrent operating expenditure',evidence_type='official web text plus download receipt',limit='separate construction column and annual headers retained'),
 dict(topic='national per-student comparison',basis='Part7 local ordinary school title versus national announcement total',url='',finding='28 national local totals kept as coverage noncomparisons; 868 province comparisons separate',evidence_type='original workbook title and source cells; announcement ledger',limit='numerical match of provincial values alone does not certify complete organizer/denominator comparability'),
]
save_csv(DATA/'yearbook_stage_scope_evidence.csv',scope)
audit=json.loads((DATA/'yearbook_stage_audit.json').read_text(encoding='utf-8'))
audit.update(candidate_panel_rows=868,local_candidate_panel_rows=434,distinct_province_year_stage=434,exception_ledger_rows=2,all_source_and_subsidy_and_general_budget_not_added=True)
(DATA/'yearbook_stage_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
verify()
print(json.dumps(audit,ensure_ascii=False,indent=2))
