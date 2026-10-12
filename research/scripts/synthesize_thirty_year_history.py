"""Common-cohort descriptive comparison and a traceable synthesis evidence index."""
from pathlib import Path
import json,hashlib,sys
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/data/三十年综合叙述_20261010'
SRC=ROOT/'research/data/省级经费历史分布_20261010/province_finance_real_endpoints.csv'
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')
def main():
    OUT.mkdir(exist_ok=True);f=pd.read_csv(SRC)
    periods=[(1995,2006),(2007,2013),(2013,2023)]
    rows=[];paired=[];cohorts={}
    for stage in ['primary','junior']:
        groups=[f[(f.stage==stage)&(f.start_year==a)&(f.end_year==b)].set_index('province') for a,b in periods]
        common=sorted(set.intersection(*(set(g.index) for g in groups)));cohorts[stage]=common
        for (a,b),g in zip(periods,groups):
            c=g.loc[common]
            for metric in ['P','C','PC']:
                v=c[metric+'_real_annualized_pct']
                rows.append(dict(stage=stage,start_year=a,end_year=b,metric=metric,common_provinces=len(common),common_cohort_median_annualized_pct=v.median(),all_available_provinces=len(g),all_available_median_annualized_pct=g[metric+'_real_annualized_pct'].median(),common_real_increasing=int((v>0).sum()),common_real_decreasing=int((v<0).sum()),interpretation='same geographic cohort; original segmented classifications still pending; not a policy effect'))
        for i,j in [(0,1),(1,2)]:
            left=groups[i].loc[common];right=groups[j].loc[common]
            for province in common:
                for metric in ['P','C','PC']:
                    x=left.loc[province,metric+'_real_annualized_pct'];y=right.loc[province,metric+'_real_annualized_pct']
                    paired.append(dict(stage=stage,province=province,metric=metric,earlier_start=periods[i][0],earlier_end=periods[i][1],later_start=periods[j][0],later_end=periods[j][1],earlier_annualized_pct=x,later_annualized_pct=y,change_annualized_percentage_points=y-x,interpretation='within-province descriptive comparison across source-classification segments; no causal inference'))
    summary=pd.DataFrame(rows);pair=pd.DataFrame(paired)
    summary.to_csv(OUT/'balanced_province_growth_comparison.csv',index=False,encoding='utf-8-sig')
    pair.to_csv(OUT/'province_growth_speed_pairs.csv',index=False,encoding='utf-8-sig')
    counts=pair.groupby(['stage','metric','earlier_start','earlier_end','later_start','later_end']).agg(provinces=('province','size'),slower_count=('change_annualized_percentage_points',lambda v:int((v<0).sum())),faster_count=('change_annualized_percentage_points',lambda v:int((v>0).sum())),median_change_pp=('change_annualized_percentage_points','median')).reset_index()
    counts.to_csv(OUT/'paired_growth_speed_distribution.csv',index=False,encoding='utf-8-sig')
    sources=[('student_history','三十年纵向分析_20261010/national_students_1995_2024.csv','national; two stages; school type/timing pending'),('student_recurrence','三十年纵向分析_20261010/recurrent_student_decline_spells.csv','province repeated declines; geographic edges split'),('income_sources','历史趋势描述_20261010/national_income_original_series.csv','national all affiliations; income not expenditure'),('local_spending_composition','三十年纵向分析_20261010/segmented_finance_structure_changes.csv','national local affiliation; P/(P+C), excludes K'),('organizer_weights','举办者与地区历史_20261010/organizer_income_weights.csv','national original organizer groups; weights are income shares'),('fiscal_share_decomposition','举办者与地区历史_20261010/fiscal_share_decomposition_totals.csv','midpoint arithmetic; not causal decomposition'),('regional_student_directions','举办者与地区历史_20261010/province_student_phase_distributions.csv','province endpoints, not annual persistent directions'),('province_real_spending','省级经费历史分布_20261010/segmented_province_growth_distributions.csv','local affiliation all-source; CPI approximate purchasing power; unweighted medians')]
    ledger=[]
    for topic,path,boundary in sources:
        p=ROOT/'research/data'/path
        ledger.append(dict(topic=topic,relative_source=str(p.relative_to(ROOT)),source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),scope_boundary=boundary))
    pd.DataFrame(ledger).to_csv(OUT/'synthesis_evidence_index.csv',index=False,encoding='utf-8-sig')
    checks=dict(common_28_provinces_each=all(len(v)==28 for v in cohorts.values()),same_stage_geographic_cohort=cohorts['primary']==cohorts['junior'],excluded_Sichuan_Chongqing_Tibet=set(f.province)-set(cohorts['primary'])=={'四川','重庆','西藏'},balanced_rows_18=len(summary)==18,paired_rows_336=len(pair)==336,paired_differences_recalculate=bool(np.allclose(pair.change_annualized_percentage_points,pair.later_annualized_pct-pair.earlier_annualized_pct)),counts_sum_to_28=bool(((counts.slower_count+counts.faster_count)==28).all()),all_source_files_present=len(ledger)==8)
    old=json.loads((ROOT/'research/data/长期财政数据建设_20261010/build_receipt.json').read_text(encoding='utf8'))['protected_hashes']
    checks['protected_files_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in old.items())
    receipt=dict(checks=checks,all_passed=all(checks.values()),balanced_cohorts=cohorts,regression_run=False,scope_bridge_approved=False,not_confirmatory=True,input_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest())
    (OUT/'synthesis_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    assert receipt['all_passed'],checks
    print(json.dumps(receipt,ensure_ascii=False));print(summary.to_string(index=False));print(counts.to_string(index=False))
if __name__=='__main__':main()
