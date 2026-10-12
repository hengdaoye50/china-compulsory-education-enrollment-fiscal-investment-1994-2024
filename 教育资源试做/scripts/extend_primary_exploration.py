"""Direct state contrast and lagged economic-condition sensitivity."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import math,sys,json
import numpy as np
import pandas as pd
from run_primary_exploration import OUT,SUPP
from exploratory_panel_stats import fe_fit,wild_t,point
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')

def main():
    data=pd.read_csv(OUT/'primary_annual_changes.csv',encoding='utf-8-sig')
    supp=pd.read_csv(SUPP,encoding='utf-8-sig',keep_default_na=False)
    values={(int(r.data_year),r.province,r.metric):float(r.raw_value) for r in supp.itertuples(index=False) if r.metric in ['GDP','CPI_yoy'] and r.raw_value}
    data['lag_real_GDP_growth']=[math.log(values[(r.year-1,r.province,'GDP')]/values[(r.year-2,r.province,'GDP')])-math.log(values[(r.year-1,r.province,'CPI_yoy')]/100) for r in data.itertuples(index=False)]
    data['state']=data.shrink2.astype(int);data['Z_state']=data.Z*data.state;data['dS_state']=data.dS*data.state
    data['Z_post']=data.Z*data.post;data['dS_post']=data.dS*data.post
    out=[]
    main=data[data.shrink2].copy()
    for name,s,outcome,regs,c in [('H1_lag_GDP',main,'D',['Z','dS','lag_real_GDP_growth'],[1,0,0]),('H2_lag_GDP',main,'dC_real',['Z','dS','Z_post','dS_post','lag_real_GDP_growth'],[0,0,1,0,0]),('full_panel_state_slope_difference',data,'D',['Z','dS','state','Z_state','dS_state'],[0,0,0,1,0])]:
        fit=fe_fit(s,outcome,regs)
        stats=wild_t(fit,c,B=9999,seed=20261030) if name=='full_panel_state_slope_difference' else point(fit,c)
        out.append(dict(specification=name,outcome=outcome,n=fit['n'],provinces=fit['G'],years=fit['years'],**stats,interpretation='exploratory; state contrast versus all other student states; GDP unverified compiled sensitivity'))
    pd.DataFrame(out).to_csv(OUT/'economic_and_state_extensions.csv',index=False,encoding='utf-8-sig')
    # Year influence diagnoses common-period sensitivity without changing the primary specification.
    result=[]
    for y in sorted(main.year.unique()):
        f=fe_fit(main[main.year!=y],'D',['Z','dS'])
        result.append(dict(omitted_year=int(y),n=f['n'],**point(f,[1,0])))
    pd.DataFrame(result).to_csv(OUT/'leave_one_year_out_H1.csv',index=False,encoding='utf-8-sig')
    print(pd.DataFrame(out).to_string(index=False),flush=True)

if __name__=='__main__':main()
