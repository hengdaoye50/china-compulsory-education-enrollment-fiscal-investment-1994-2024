"""Summarize thirty-year descriptions; no hypothesis tests or student division."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/data/历史趋势描述_20261010'
HISTORY=ROOT/'research/data/三十年纵向分析_20261010'
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')
def main():
    f=pd.read_csv(OUT/'national_income_original_series.csv')
    evidence=json.loads((OUT/'national_income_original_evidence.json').read_text(encoding='utf8'))
    students=pd.read_csv(HISTORY/'national_students_1995_2024.csv')
    finance=pd.read_csv(HISTORY/'national_finance_composition_1995_2024.csv')
    local=finance[finance.school_scope=='local_affiliation'][['year','stage','personal_share_of_PC_pct','numeric_status']]
    merged=f.merge(students[['year','stage','students']],on=['year','stage'],validate='one_to_one').merge(local,on=['year','stage'],validate='one_to_one')
    merged['income_nominal_yi_yuan']=np.where(merged.unit=='千元',merged.income_total_thousand_yuan/100000,np.nan)
    merged['national_fiscal_nominal_yi_yuan']=np.where(merged.unit=='千元',merged.national_fiscal_thousand_yuan/100000,np.nan)
    merged=merged.rename(columns={'personal_share_of_PC_pct':'local_affiliation_personal_share_of_PC_pct'})
    merged['scope_note']='students all organizers; income national all affiliations; PC share local affiliation; context comparison only'
    merged.to_csv(OUT/'historical_description_master.csv',index=False,encoding='utf-8-sig')
    periods=[]
    for (label,group) in f.groupby('budget_original_header',dropna=False):
        periods.append(dict(original_budget_label=label,years=';'.join(map(str,sorted(group.year.unique()))),rows=len(group),interpretation='source categories; gaps and label changes retained; not institutional stage identification'))
    pd.DataFrame(periods).to_csv(OUT/'income_category_periods.csv',index=False,encoding='utf-8-sig')
    endpoints=[]
    for stage in ['primary','junior']:
        ix=f[f.stage==stage].set_index('year')
        for a,b in [(1995,2003),(2005,2009),(2005,2013),(2013,2024),(2017,2024)]:
            left=ix.loc[a];right=ix.loc[b]
            rec=dict(stage=stage,start_year=a,end_year=b,amount_unit_confirmed=left.unit==right.unit=='千元',income_nominal_growth_pct=100*(right.income_total_thousand_yuan/left.income_total_thousand_yuan-1),interpretation='original endpoints; nominal; annual scope changes pending; not reform effects')
            for m in ['budget','national_fiscal','tuition','business']:
                rec[m+'_share_start']=left[m+'_share_pct'];rec[m+'_share_end']=right[m+'_share_pct'];rec[m+'_share_change_pp']=right[m+'_share_pct']-left[m+'_share_pct']
            rec['national_fiscal_nominal_growth_pct']=100*(right.national_fiscal_thousand_yuan/left.national_fiscal_thousand_yuan-1) if pd.notna(left.national_fiscal_thousand_yuan) else None
            endpoints.append(rec)
    pd.DataFrame(endpoints).to_csv(OUT/'national_income_phase_changes.csv',index=False,encoding='utf-8-sig')
    checks={}
    checks['complete_60_stage_year_income_rows']=len(f)==60 and not f.duplicated(['year','stage']).any() and all(set(f[f.stage==s].year)==set(range(1995,2025)) for s in ['primary','junior'])
    checks['one_national_source_each_year']=len(evidence)==30 and all('中央' not in e['table'] and '地方)' not in e['table'] for e in evidence)
    checks['raw_cell_values_recalculate']=all(float(str(r['values'][1]).strip())==float(f[(f.year==e['data_year'])&(f.stage==r['stage'])].iloc[0].income_total_thousand_yuan) for e in evidence for r in e['stage_rows'])
    checks['fiscal_total_not_other_fiscal']=bool(f.loc[f.national_fiscal_thousand_yuan.notna(),'national_fiscal_original_header'].str.startswith('国家').all()) and bool(f.loc[f.year<2005,'national_fiscal_thousand_yuan'].isna().all())
    checks['component_observed_sum_within_8_raw_units']=bool((f.total_minus_observed_components.abs()<=8).all())
    checks['reported_shares_recalculate']=all(np.allclose(f[m+'_share_pct'].dropna(),(100*f[m+'_thousand_yuan']/f.income_total_thousand_yuan).dropna()) for m in ['national_fiscal','budget','tuition','business'])
    checks['unresolved_units_not_converted']=bool(merged.loc[merged.unit!='千元','income_nominal_yi_yuan'].isna().all())
    checks['original_missing_not_filled']=bool(f.loc[f.government_fund_source_cell.isna(),'government_fund_thousand_yuan'].isna().all())
    checks['no_per_student_division']=not bool(f.per_student_calculated.any())
    protected=json.loads((ROOT/'research/data/长期财政数据建设_20261010/build_receipt.json').read_text(encoding='utf8'))['protected_hashes']
    checks['protected_files_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
    result=dict(checks=checks,all_passed=all(checks.values()),national_income_years='1995_2024',rows=len(f),unresolved_unit_years=sorted(map(int,f[f.unit!='千元'].year.unique())),unresolved_budget_label_years=sorted(map(int,f[f.budget_source_cell.isna()].year.unique())),component_max_abs_difference=float(f.total_minus_observed_components.abs().max()),exploratory_regressions_rerun=False,inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'national_income_original_series.csv',OUT/'national_income_original_evidence.json',HISTORY/'national_students_1995_2024.csv',HISTORY/'national_finance_composition_1995_2024.csv']})
    (OUT/'description_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    assert result['all_passed'],checks
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print(pd.DataFrame(endpoints)[['stage','start_year','end_year','income_nominal_growth_pct','national_fiscal_nominal_growth_pct','budget_share_start','budget_share_end','national_fiscal_share_start','national_fiscal_share_end','tuition_share_start','tuition_share_end']].to_string(index=False))
if __name__=='__main__':main()
