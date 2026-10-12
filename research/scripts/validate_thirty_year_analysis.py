"""Verify the new longitudinal and paired-stage results without re-running audits."""
from pathlib import Path
import json, hashlib, sys
import pandas as pd
import numpy as np
from exploratory_panel_stats import fe_fit, point
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/data/三十年纵向分析_20261010'
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')

def main():
    read=lambda name:pd.read_csv(OUT/name)
    checks={}
    national=read('national_students_1995_2024.csv')
    checks['two_complete_30_year_student_series']=all(set(national[national.stage==s].year)==set(range(1995,2025)) for s in ['primary','junior'])
    endpoints=read('national_student_endpoints.csv')
    checks['endpoint_rates_recalculate']=bool(np.allclose(endpoints.change_pct,100*(endpoints.end_students/endpoints.start_students-1)))
    spells=read('recurrent_student_decline_spells.csv')
    rec=spells.groupby(['province','stage']).size().reset_index(name='spells')
    counts={s:int(((rec.stage==s)&(rec.spells>=2)).sum()) for s in ['primary','junior']}
    checks['two_year_recurrence_21_18']=counts==dict(primary=21,junior=18)
    r3=spells[spells.decline_years>=3].groupby(['province','stage']).size().reset_index(name='spells')
    counts3={s:int(((r3.stage==s)&(r3.spells>=2)).sum()) for s in ['primary','junior']}
    checks['three_year_recurrence_15_11']=counts3==dict(primary=15,junior=11)
    finance=read('national_finance_composition_1995_2024.csv')
    checks['PC_shares_recalculate']=bool(np.allclose(finance.personal_share_of_PC_pct,100*finance.P_thousand_yuan/(finance.P_thousand_yuan+finance.C_thousand_yuan)))
    checks['part4_provenance_only']=bool(finance.table.str.replace('\\','/',regex=False).str.split('/').str[-1].str.match(r'^4[-—_ ]').all())
    regional=read('segmented_local_finance_changes.csv')
    checks['no_2007_finance_change']=not bool((regional.year==2007).any())
    pair=read('paired_stage_common_sample.csv')
    checks['paired_identical_R_98_edges']=len(pair)==98 and np.allclose(pair.Z_primary,pair.Z_junior) and bool((pair.shrink2_primary & pair.shrink2_junior).all())
    fit=fe_fit(pair,'D_difference',['Z','dS_primary','dS_junior'])
    saved=read('paired_stage_H1_difference.csv').iloc[0]
    checks['paired_coefficient_recalculate']=bool(np.isclose(point(fit,[1,0,0])['coefficient'],saved.coefficient,atol=1e-10))
    family=read('four_exploratory_hypotheses.csv');p=family.wild_p.to_numpy();order=np.argsort(p)
    adj=np.maximum.accumulate([min(1,(4-i)*p[j]) for i,j in enumerate(order)])
    checks['Holm_four_tests_recalculate']=bool(np.allclose(adj,family.Holm_four_exploratory_p.to_numpy()[order]))
    checks['scope_not_approved']=not bool(finance.model_scope_approved.any()) and not bool(regional.model_scope_approved.any())
    receipt=json.loads((ROOT/'research/data/长期财政数据建设_20261010/build_receipt.json').read_text(encoding='utf8'))
    checks['protected_inputs_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in receipt['protected_hashes'].items())
    # Both years of fund reclassification are tested together; point/CR1 diagnostics only.
    extra=[]
    for stage,folder in [('primary','小学探索分析_20261010'),('junior','初中探索分析_20261010')]:
        data=pd.read_csv(ROOT/'research/data'/folder/f'{stage}_annual_changes.csv')
        sub=data[data.shrink2 & ~data.year.isin([2015,2016])].copy()
        sub['Z_post']=sub.Z*sub.post;sub['dS_post']=sub.dS*sub.post
        for h,y,x,c in [('H1','D',['Z','dS'],[1,0]),('H2','dC_real',['Z','dS','Z_post','dS_post'],[0,0,1,0])]:
            f=fe_fit(sub,y,x)
            extra.append(dict(stage=stage,hypothesis=h,specification='exclude_2015_2016_R_reclassification',n=len(sub),**point(f,c),interpretation='targeted sensitivity; no bootstrap p; not a replacement main model'))
    pd.DataFrame(extra).to_csv(OUT/'additional_reclassification_sensitivity.csv',index=False,encoding='utf-8-sig')
    result=dict(checks=checks,all_passed=all(checks.values()),recurrent_provinces_two_year=counts,recurrent_provinces_three_year=counts3,paired_positive_Z=int((pair.Z>0).sum()),paired_positive_Z_provinces=int(pair[pair.Z>0].province.nunique()),paired_confidence_set_disjoint=int(saved.WCR_disjoint_bands),paired_CI_search_boundary=bool(saved.WCR_search_boundary_accepted),new_output_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.csv'))})
    (OUT/'analysis_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    assert result['all_passed'],checks
    print(json.dumps(result,ensure_ascii=False,indent=2));print(pd.DataFrame(extra).to_string(index=False))
    return result

if __name__=='__main__':main()
