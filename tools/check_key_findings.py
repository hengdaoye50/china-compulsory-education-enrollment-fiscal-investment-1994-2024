"""Independent checks of published data and the reported main contrast estimates."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
root=Path(__file__).resolve().parents[1]
base=root/'research/data'
students=pd.read_csv(base/'三十年纵向分析_20261010/national_students_1995_2024.csv')
finance=pd.read_csv(base/'早期财政重建_20261011/national_fiscal_1994_2024_report_final.csv')
tests=pd.read_csv(base/'支出细项与补助拓展_20261011/component_primary_tests.csv')
checks={}
for stage,peak,low,reported in [('primary',1997,2013,.766),('junior',2003,2015,.506)]:
    s=students[students.stage==stage].set_index('year')
    assert set(s.index)==set(range(1995,2025))
    assert int(s.students.idxmax())==peak and int(s.students.idxmin())==low
    f=finance[finance.stage==stage].set_index('year')
    expected=107.31 if stage=='primary' else 111.27
    assert round(100*(f.loc[2024,'fiscal_yi']/f.loc[2013,'fiscal_yi']-1),2)==expected
    d=pd.read_csv(base/f'支出细项与补助拓展_20261011/{stage}_component_model_input.csv')
    assert len(d)==472 and d.province.nunique()==31
    controls=pd.get_dummies(d[['province','year']].astype(str),drop_first=True,dtype=float)
    X=np.column_stack([d[['dS','dR_real']].to_numpy(),np.ones(len(d)),controls.to_numpy()])
    y=d.dG_real.to_numpy()-d.dW_real.to_numpy()
    estimate=float(np.linalg.lstsq(X,y,rcond=None)[0][0])
    recorded=tests[(tests.stage==stage)&(tests.regressor=='dS')].iloc[0]
    assert np.isclose(estimate,recorded.coefficient,atol=1e-10)
    assert round(estimate,3)==reported and recorded.Holm_family_p<.05
    assert np.allclose(d.DGW,y)
    assert np.all(np.abs(d.G_contribution+d.X_contribution-d.C_real_growth)<=d.contribution_rounding_tolerance)
    checks[stage]={'years':30,'peak_year':peak,'low_year':low,'fiscal_nominal_growth_2013_2024_pct':expected,'independent_OLS_contrast':estimate,'published_Holm_p':float(recorded.Holm_family_p),'note':'p values read from preserved bootstrap output; bootstrap not rerun in this check'}
print(json.dumps({'passed':True,'checks':checks},ensure_ascii=False,indent=2))
