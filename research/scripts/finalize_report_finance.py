"""Select a documented 1994 estimate for the report without changing historical series."""
from pathlib import Path
import pandas as pd,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'research/data/早期财政重建_20261011'
old=P/'national_fiscal_1994_2024_segmented.csv'
old_hash=hashlib.sha256(old.read_bytes()).hexdigest()
x=pd.read_csv(old)
q=pd.read_csv(P/'1994_conversion_scenarios.csv')
method='compulsory_budget_constraint'
for stage in ['primary','junior']:
    z=q[(q.stage==stage)&(q.model==method)]
    a=z[z.anchor_year==1995].iloc[0]
    idx=x.index[(x.year==1994)&(x.stage==stage)][0]
    for key in ['budget','fiscal','total']:
        x.loc[idx,key+'_thousand_yuan']=a[key+'_yi']*100000
    for key in ['fiscal','total']:
        x.loc[idx,key+'_scenario_low_thousand_yuan']=z[key+'_yi'].min()*100000
        x.loc[idx,key+'_scenario_high_thousand_yuan']=z[key+'_yi'].max()*100000
    x.loc[idx,'share_scenario_low_pct']=z.fiscal_share_pct.min()
    x.loc[idx,'share_scenario_high_pct']=z.fiscal_share_pct.max()
    x.loc[idx,'status']='model_backcast_budget_constrained'
    x.loc[idx,'formula']='1994_compulsory_budget_share_with_1995_stage_weights_including_special; other_sources_1994_with_1995_source_weights'
x['fiscal_yi']=x.fiscal_thousand_yuan/100000
x['total_yi']=x.total_thousand_yuan/100000
x['fiscal_share_pct']=100*x.fiscal_thousand_yuan/x.total_thousand_yuan
assert len(x)==62 and x.fiscal_share_pct.between(0,100).all()
original=pd.read_csv(old)
pd.testing.assert_frame_equal(x[x.year>=1995].reset_index(drop=True),original[original.year>=1995].reset_index(drop=True),check_exact=False,rtol=1e-12)
target=P/'national_fiscal_1994_2024_report_final.csv'
x.to_csv(target,index=False,encoding='utf-8-sig')
receipt={'selected_method':method,'anchor_year':1995,'reason':'Uses contemporaneous 1994 national funding sources and compulsory-education budget share while retaining special education in allocation denominator. Stage allocation remains assumed.','estimate_status':'conditional_not_observed','scenario_definition':'Same model with 1995, 1996, 1997 stage weights. Share bounds are minima and maxima of matched scenarios, not independent ratios or confidence intervals.','1994_records':x[x.year==1994].to_dict('records'),'1995_2024_unchanged':True,'previous_series_sha256':old_hash,'report_series_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'whitepaper_594_scope_unresolved':True}
(P/'report_final_selection.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
assert hashlib.sha256(old.read_bytes()).hexdigest()==old_hash
print(x[x.year==1994][['stage','fiscal_yi','total_yi','fiscal_share_pct']].to_string(index=False))
