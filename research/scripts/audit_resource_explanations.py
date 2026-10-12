"""Independent matrix reconstruction and integrity checks for resource extension."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'research/data/资源解释拓展_20261011';FIG=ROOT/'research/figures/资源解释图组_20261011'
co=pd.read_csv(OUT/'all_coefficients_and_sensitivities.csv');tests=pd.read_csv(OUT/'four_resource_contrast_tests.csv');excluded=pd.read_csv(OUT/'excluded_finance_connections.csv')
checks=[]
def check(label,condition):
    checks.append({'check':label,'passed':bool(condition)})
    if not condition:raise AssertionError(label)
receipt=json.loads((OUT/'analysis_receipt.json').read_text(encoding='utf8'))
for stage in ['primary','junior']:
    df=pd.read_csv(OUT/f'{stage}_model_input.csv');check(stage+'_sample_balance',len(df)==300 and len(df)+len(excluded[excluded.stage==stage])==310)
    check(stage+'_student_changes_match',np.allclose(df.dS,df.dS_resource,atol=1e-10))
    check(stage+'_resource_logs',all(np.allclose(df[col],np.log(df[metric]/df[metric+'_previous']),atol=1e-12) for metric,col in [('teachers','dT'),('classes','dB'),('schools','dH')]))
    check(stage+'_flags_preserved',not df.model_scope_approved.any())
    pp=np.asarray(df.province);yy=np.asarray(df.year);groups=np.unique(pp);years=np.unique(yy)
    for spec,regs in [('same_sample_baseline',['dS','dR_real']),('joint_resources',['dS','dR_real','dT','dB'])]:
        X=np.column_stack([df[regs].to_numpy(),*[(pp==g).astype(float) for g in groups],*[(yy==y).astype(float) for y in years[1:]]]);inv=np.linalg.inv(X.T@X);rank=np.linalg.matrix_rank(X)
        factor=len(groups)/(len(groups)-1)*(len(df)-1)/(len(df)-rank)
        coeff={}
        for outcome in ['dP_real','dC_real','D']:
            b=np.linalg.lstsq(X,df[outcome],rcond=None)[0];e=df[outcome].to_numpy()-X@b
            scores=np.vstack([X[pp==g].T@e[pp==g] for g in groups]);cov=factor*inv@scores.T@scores@inv
            rr=co[(co.stage==stage)&(co.specification==spec)&(co.outcome==outcome)].set_index('regressor').loc[regs]
            check(f'{stage}_{spec}_{outcome}_full_dummy',np.allclose(b[:len(regs)],rr.coefficient,atol=1e-9))
            check(f'{stage}_{spec}_{outcome}_cluster_SE',np.allclose(np.sqrt(np.diag(cov)[:len(regs)]),rr.cluster_CR1_se,atol=1e-9))
            coeff[outcome]=b[:len(regs)]
        check(f'{stage}_{spec}_direct_difference',np.allclose(coeff['D'],coeff['dC_real']-coeff['dP_real'],atol=1e-10))
    lag=pd.read_csv(OUT/f'{stage}_lag_model_input.csv');resource=pd.read_csv(OUT/'resource_changes_2014_2023.csv');resource=resource[resource.stage==stage].set_index(['province','year'])
    check(stage+'_lag_calendar',all(np.isclose(r.dT_lag1,resource.loc[(r.province,r.year-1),'dT']) and np.isclose(r.dB_lag1,resource.loc[(r.province,r.year-1),'dB']) for r in lag.itertuples(index=False)))
order=np.argsort(tests.wild_restricted_p.to_numpy());adjust=np.maximum.accumulate([(4-i)*tests.iloc[j].wild_restricted_p for i,j in enumerate(order)])
check('Holm_four_reconstruction',all(np.isclose(tests.iloc[j].Holm_four_p,min(1,adjust[i])) for i,j in enumerate(order)))
check('single_interval_null_test_consistency',all((r.WCR_95_CI_low<=0<=r.WCR_95_CI_high)==(r.wild_restricted_p>=.05) for r in tests.itertuples(index=False)))
allinputs={**receipt['input_hashes'],**receipt['raw_resource_hashes']}
check('all_input_and_raw_hashes_unchanged',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in allinputs.items()))
source=pd.read_csv(OUT/'resource_source_rereads.csv')
check('2816_unique_source_cells',len(source)==2816 and not source.duplicated(['stage','year','province','metric']).any() and source.pass_exact.all())
for path in FIG.glob('*.png'):
    im=Image.open(path);check(path.stem+'_600dpi',all(abs(v-600)<1 for v in im.info['dpi']));check(path.stem+'_white_background',im.convert('RGB').getpixel((0,0))==(255,255,255))
(OUT/'validation_receipt.json').write_text(json.dumps({'passed':True,'checks':checks,'independent_method':'Complete dummy regression and full-design province CR1 covariance'},ensure_ascii=False,indent=2),encoding='utf8')
print(len(checks),'checks passed')
