"""Independent direct-dummy and province-cluster reconstruction of new models."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'教育资源试做/data/定量深化_20261011';FIG=ROOT/'教育资源试做/定量深化图组_20261011'
checks=[]
def check(name,condition):
    checks.append({'check':name,'passed':bool(condition)})
    if not condition:raise AssertionError(name)
receipt=json.loads((OUT/'analysis_receipt.json').read_text(encoding='utf8'))
co=pd.read_csv(OUT/'all_main_coefficients.csv');tt=pd.read_csv(OUT/'four_direct_contrast_tests.csv')
for stage,folder in [('primary','小学探索分析_20261010'),('junior','初中探索分析_20261010')]:
    df=pd.read_csv(OUT/f'{stage}_model_input.csv');ex=pd.read_csv(ROOT/f'教育资源试做/data/{folder}/excluded_adjacent_changes.csv')
    check(f'{stage}_potential_sample_balance',len(df)+len(ex)==31*16 and len(df)==472)
    pp=np.asarray(df.province);groups=np.unique(pp);yy=np.asarray(df.year);years=np.unique(yy)
    X=np.column_stack([df.dS,df.dR_real,*[(pp==g).astype(float) for g in groups],*[(yy==y).astype(float) for y in years[1:]]])
    bread=np.linalg.inv(X.T@X);rank=np.linalg.matrix_rank(X)
    for outcome in ['dP_real','dC_real','D']:
        b=np.linalg.lstsq(X,df[outcome],rcond=None)[0];e=df[outcome].to_numpy()-X@b
        scores=np.vstack([X[pp==g].T@e[pp==g] for g in groups]);factor=len(groups)/(len(groups)-1)*(len(df)-1)/(len(df)-rank)
        cov=factor*bread@scores.T@scores@bread
        rr=co[(co.stage==stage)&(co.outcome==outcome)].set_index('regressor').loc[['dS','dR_real']]
        check(f'{stage}_{outcome}_full_dummy_coefficients',np.allclose(b[:2],rr.coefficient,atol=1e-9))
        check(f'{stage}_{outcome}_independent_cluster_SE',np.allclose(np.sqrt(np.diag(cov)[:2]),rr.cluster_CR1_se,atol=1e-9))
    check(f'{stage}_scope_flags_preserved',not df.model_scope_approved.any())
    lag=pd.read_csv(OUT/f'{stage}_lag_model_input.csv');base=df.set_index(['province','year'])
    check(f'{stage}_lag_calendar_adjacency',all(np.isclose(r.dS_lag1,base.loc[(r.province,r.year-1),'dS']) for r in lag.itertuples(index=False)))
order=np.argsort(tt.wild_restricted_p.to_numpy());a=np.maximum.accumulate([(4-i)*tt.iloc[j].wild_restricted_p for i,j in enumerate(order)])
check('Holm_adjustment_reconstructed',all(np.isclose(min(1,a[i]),tt.iloc[j].Holm_four_p) for i,j in enumerate(order)))
check('confidence_intervals_and_single_tests_agree',all(((r.WCR_95_CI_low<=0<=r.WCR_95_CI_high)==(r.wild_restricted_p>=.05)) for r in tt.itertuples(index=False)))
for path,h in receipt['inputs'].items():check('unchanged_'+path,hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h)
for path in FIG.glob('*.png'):
    im=Image.open(path);check(path.stem+'_600dpi',all(abs(v-600)<1 for v in im.info['dpi']))
    check(path.stem+'_white_background',im.convert('RGB').getpixel((0,0))==(255,255,255))
(OUT/'validation_receipt.json').write_text(json.dumps({'checks':checks,'passed':all(x['passed'] for x in checks),'method':'Independent complete dummy regression and full design province CR1 covariance'},ensure_ascii=False,indent=2),encoding='utf8')
print(f'{len(checks)} checks passed')
