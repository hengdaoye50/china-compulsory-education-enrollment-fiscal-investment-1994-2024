"""Focused checks of exploratory calculations and coefficient computation."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import json,hashlib,sys
import numpy as np
import pandas as pd
from run_primary_exploration import ROOT,OUT,INPUT
from exploratory_panel_stats import fe_fit
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')

def main():
    data=pd.read_csv(OUT/'primary_annual_changes.csv');result=pd.read_csv(OUT/'exploratory_FE_results.csv')
    panel=pd.read_csv(INPUT,keep_default_na=False);panel=panel[panel.stage=='primary'];ix={(r.year,r.province):r for r in panel.itertuples(index=False)}
    formulas=[]
    for r in data.itertuples(index=False):
        a=ix[(r.year,r.province)];b=ix[(r.year-1,r.province)];pi=np.log(r.CPI_yoy/100)
        formulas.append(np.isclose(r.dC_real,np.log(float(a.C_thousand_yuan)/float(b.C_thousand_yuan))-pi) and np.isclose(r.D,r.dC_real-r.dP_real) and np.isclose(r.Z,max(0,-r.dR_real)) and bool(r.shrink2)==(float(a.S_numeric)<float(b.S_numeric)<float(ix[(r.year-2,r.province)].S_numeric)))
    fit=fe_fit(data[data.shrink2],'D',['Z','dS']);target=result[(result.specification=='main_two_year')&(result.hypothesis=='H1')].iloc[0]
    # A balanced synthetic panel with known slopes and arbitrary fixed effects checks algebra.
    rng=np.random.default_rng(17);p=np.repeat(np.arange(8),7);y=np.tile(np.arange(7),8)
    x=rng.normal(size=(56,2));response=x@np.array([.7,-.4])+p*.3+y*.2
    synthetic=pd.DataFrame(dict(province=p,year=y,x1=x[:,0],x2=x[:,1],outcome=response))
    synthetic_fit=fe_fit(synthetic,'outcome',['x1','x2'])
    receipt=json.loads((OUT/'analysis_receipt.json').read_text(encoding='utf8'))
    protected=json.loads((ROOT/'research/data/长期财政数据建设_20261010/build_receipt.json').read_text(encoding='utf8'))['protected_hashes']
    validation=dict(adjacent_positions_unique=len(data)==len(data[['year','province']].drop_duplicates())==472,exclusions_balance_496=len(pd.read_csv(OUT/'excluded_adjacent_changes.csv'))+len(data)==496,all_change_formulas_recomputed=all(formulas),D_common_price_cancels=np.allclose(data.D,data.dC_nominal-data.dP_nominal),main_157_and_17_pressure=int(data.shrink2.sum())==157 and int(((data.Z>0)&data.shrink2).sum())==17,FWL_matches_recorded_H1=np.isclose(fit['beta'][0],target.coefficient),synthetic_FE_known_coefficients_recovered=np.allclose(synthetic_fit['beta'],[.7,-.4]),primary_H1_interval_and_p_agree=target.WCR_95_CI_low<0<target.WCR_95_CI_high and target.wild_restricted_p>.05,all_original_model_approvals_still_false=panel.model_eligible.astype(str).eq('False').all(),inputs_unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in receipt['inputs'].items()),protected_outputs_unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items()))
    validation={k:bool(v) for k,v in validation.items()}
    output=dict(checks=validation,passed=all(validation.values()))
    (OUT/'validation_receipt.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf8')
    assert output['passed'],output
    print(json.dumps(output,ensure_ascii=False))

if __name__=='__main__':main()
