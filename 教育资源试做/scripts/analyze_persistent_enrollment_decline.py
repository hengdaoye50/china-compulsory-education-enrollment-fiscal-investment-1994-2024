"""Observed enrollment runs, not demographic shrinkage or causal response."""
import csv,json,hashlib,sys
from decimal import Decimal as D
from collections import defaultdict
from fractions import Fraction
from parse import ROOT,save_csv
sys.stdout.reconfigure(encoding='utf-8')
DATA=ROOT/'data'
def read(n):return list(csv.DictReader((DATA/n).open(encoding='utf-8-sig',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pct(a,b):return (D(a)/D(b)-1)*100
protected=json.loads((DATA/'province_finance_next_protected_baseline.json').read_text(encoding='utf-8'))
def protect():assert all(sha(ROOT/p)==s for p,s in protected.items())
protect()
context=read('resource_finance_parallel_context.csv')
bykey={(r['province'],int(r['year']),r['stage']):r for r in context}
changes=read('resource_finance_parallel_changes.csv')
assert len(changes)==372
groups=defaultdict(list)
for r in changes:groups[r['province'],r['stage']].append(r)
assert len(groups)==62
finance=read('fiscal_analysis_province_series.csv')
fmap={(r['province'],int(r['year']),r['stage'],r['affiliation_scope'],r['fund']):r for r in finance}
spells=[];profiles=[];sensitivity=[];formula=[]
for threshold in [D(0),D('.5'),D(1)]:
 for (province,stage),rows in sorted(groups.items()):
  rows=sorted(rows,key=lambda r:int(r['year']));assert [int(r['year']) for r in rows]==list(range(2018,2024))
  runs=[];current=[]
  for r in rows:
   if D(r['students_change_pct']) < -threshold:current.append(r)
   elif current:runs.append(current);current=[]
  if current:runs.append(current)
  trailing=len(runs[-1]) if runs and int(runs[-1][-1]['year'])==2023 else 0
  longest=max([len(r) for r in runs],default=0)
  sensitivity.append(dict(province=province,stage=stage,annual_decline_threshold_pct=str(threshold),decline_years=sum(len(r) for r in runs),longest_run_years=longest,trailing_run_ending_2023=trailing,runs_at_least2=sum(len(r)>=2 for r in runs),runs_at_least3=sum(len(r)>=3 for r in runs),definition='strict yearly decline beyond threshold; 2 consecutive changes require 3 annual stocks'))
  if threshold:continue
  for index,run in enumerate(runs,1):
   first=int(run[0]['year']);last=int(run[-1]['year']);base=first-1
   a=bykey[province,base,stage];b=bykey[province,last,stage]
   result=dict(province=province,stage=stage,spell_id=index,start_decline_year=first,end_decline_year=last,base_year=base,consecutive_decline_changes=len(run),start_at_window_boundary=first==2018,end_at_window_boundary=last==2023,interpretation='maximal observed enrollment-decline run, not population decline; fiscal/resource school coverage unconfirmed')
   for m in ['students','teachers','classes','spending_total_thousand_yuan','spending_cpi_adjusted_2017_thousand_yuan']:
    value=pct(b[m],a[m]);result[m+'_cumulative_pct']=str(value)
    rational=(Fraction(b[m])/Fraction(a[m])-1)*100
    assert abs(value-D(rational.numerator)/D(rational.denominator))<D('1e-20')
    formula.append(dict(province=province,stage=stage,spell_id=index,metric=m,status='pass'))
   result['decline_years_with_teacher_increase']=sum(D(r['teachers_change_pct'])>0 for r in run)
   result['decline_years_with_class_increase']=sum(D(r['classes_change_pct'])>0 for r in run)
   result['decline_years_with_cpi_adjusted_budget_increase']=sum(D(r['spending_cpi_adjusted_2017_thousand_yuan_change_pct'])>0 for r in run)
   spells.append(result)
   if len(run)<2:continue
   for scope in ['all_affiliations','local_affiliation']:
    for fund in ['all_source','fiscal_subsidy','general_budget']:
     f0=fmap[province,base,stage,scope,fund];f1=fmap[province,last,stage,scope,fund]
     profiles.append(dict(province=province,stage=stage,spell_id=index,base_year=base,end_year=last,decline_changes=len(run),affiliation_scope=scope,fund=fund,cpi_adjusted_total_cumulative_pct=str(pct(f1['cpi_adjusted_total_2017_prices'],f0['cpi_adjusted_total_2017_prices'])),cpi_adjusted_career_cumulative_pct=str(pct(f1['cpi_adjusted_career_2017_prices'],f0['cpi_adjusted_career_2017_prices'])),limit='fiscal-definition sensitivity only; not matched fiscal students'))
summary=[]
for stage in ['primary','junior']:
 for threshold in [D(0),D('.5'),D(1)]:
  rows=[r for r in sensitivity if r['stage']==stage and r['annual_decline_threshold_pct']==str(threshold)]
  summary.append(dict(stage=stage,annual_decline_threshold_pct=str(threshold),provinces=31,provinces_with_any_decline=sum(r['decline_years']>0 for r in rows),provinces_with_run_at_least2=sum(r['longest_run_years']>=2 for r in rows),provinces_with_run_at_least3=sum(r['longest_run_years']>=3 for r in rows),provinces_ending2023_run_at_least2=sum(r['trailing_run_ending_2023']>=2 for r in rows),provinces_ending2023_run_at_least3=sum(r['trailing_run_ending_2023']>=3 for r in rows)))
for name,rows in [('persistent_decline_spells.csv',spells),('persistent_decline_fund_sensitivity.csv',profiles),('persistent_decline_province_profile.csv',sensitivity),('persistent_decline_summary.csv',summary),('persistent_decline_formula_checks.csv',formula)]:save_csv(DATA/name,rows)
protect()
audit=dict(window=[2017,2023],annual_opportunities_per_province_stage=6,province_stages=62,observed_maximal_spells=len(spells),spells_at_least2=sum(r['consecutive_decline_changes']>=2 for r in spells),spells_at_least3=sum(r['consecutive_decline_changes']>=3 for r in spells),formula_checks=len(formula),threshold_profile_rows=len(sensitivity),fund_sensitivity_rows=len(profiles),financial_denominator_used=False,causal_models_run=False,protected_files_unchanged=True,charts_updated=False)
(DATA/'persistent_decline_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False))
print('Spells of at least 2 annual declines:')
for r in spells:
 if r['consecutive_decline_changes']>=2:print(json.dumps(r,ensure_ascii=False))
