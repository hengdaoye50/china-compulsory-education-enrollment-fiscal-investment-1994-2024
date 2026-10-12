"""Independent full-dummy OLS, clustered covariance, accounting and release checks."""
import os,sys,json,hashlib
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'research/data/支出细项与补助拓展_20261011';FIG=ROOT/'research/figures/支出细项与补助图组_20261011'
sys.path.insert(0,str(ROOT/'research/.tmp/figure_deps'))
import numpy as np
import pandas as pd
from PIL import Image
checks=[]
def check(name,ok,detail=''):
    checks.append(dict(check=name,passed=bool(ok),detail=str(detail)))
    assert ok,(name,detail)
def main():
    receipt=json.loads((DATA/'analysis_receipt.json').read_text(encoding='utf8'));levels=pd.read_csv(DATA/'component_levels.csv');cells=pd.read_csv(DATA/'component_original_rereads.csv');sub=pd.read_csv(DATA/'subsidy_levels_numeric.csv');co=pd.read_csv(DATA/'all_coefficients.csv')
    check('component_key_uniqueness',not levels.duplicated(['stage','year','province']).any())
    check('full_component_levels_31x17x2',len(levels)==1054)
    check('source_cells_4_per_level',len(cells)==4216 and cells.exact_reread.all())
    check('P_sum_with_display_rounding',((levels.W+levels.A-levels.P).abs()<=1.5).all())
    check('C_sum_with_display_rounding',((levels.G+levels.X-levels.C).abs()<=1.5).all())
    check('subsidy_unique_year_province',not sub.duplicated(['year','province']).any())
    check('subsidy_units_only_explicit_yi_or_wanyuan',sub.unit_to_yi.isin([1,.0001]).all())
    check('subsidy_positive_not_blank_filled',(sub.B>0).all())
    check('subsidy_title_province_and_year',all(r.province in r.title_context and str(r.year) in r.title_context for r in sub.itertuples()))
    check('subsidy_own_income_match',(sub.own_difference.abs()<=np.maximum(.015,sub.prior_R.abs()*1e-6)).all())
    check('all_old_protected_hashes_preserved',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in receipt['protected_sha256'].items()))
    for stage in ['primary','junior']:
        for kind in ['component','subsidy']:
            d=pd.read_csv(DATA/f'{stage}_{kind}_model_input.csv');check(f'{stage}_{kind}_unique',not d.duplicated(['year','province']).any());check(f'{stage}_{kind}_CPI_reconstruction',np.allclose(np.log(d.C/d.C_previous)-np.log(d.CPI_yoy/100),d.dC_real,atol=1e-10))
            check(f'{stage}_{kind}_contribution_rounding_bound',(d.contribution_rounding_residual.abs()<=d.contribution_rounding_tolerance).all())
            check(f'{stage}_{kind}_direct_contrast_identity',np.allclose(d.DGW,d.dG_real-d.dW_real,atol=1e-12))
            specs={'components':['dS','dR_real']} if kind=='component' else {'same_sample_own':['dS','dR_real'],'own_and_subsidy':['dS','dR_real','dBsub_real'],'own_plus_subsidy':['dS','dRplusB_real']}
            for spec,regs in specs.items():
                outcomes=['dW_real','dA_real','dG_real','dX_real','D','DGW'] if kind=='component' else ['dG_real','DGW','D']
                for y in outcomes:
                    z=d.dropna(subset=[y]);p=pd.get_dummies(z.province,dtype=float).values;t=pd.get_dummies(z.year,dtype=float).values[:,1:];X=np.column_stack([z[regs].values,p,t]);Y=z[y].values;b=np.linalg.lstsq(X,Y,rcond=None)[0];e=Y-X@b;inv=np.linalg.inv(X.T@X);G=z.province.nunique();rank=np.linalg.matrix_rank(X);meat=np.zeros_like(inv)
                    for province in z.province.unique():
                        m=z.province.values==province;score=X[m].T@e[m];meat+=np.outer(score,score)
                    cov=G/(G-1)*(len(z)-1)/(len(z)-rank)*inv@meat@inv
                    target=co[(co.stage==stage)&(co.specification==spec)&(co.outcome==y)].set_index('regressor').loc[regs]
                    check(f'{stage}_{spec}_{y}_independent_beta',np.allclose(b[:len(regs)],target.coefficient,atol=1e-9))
                    check(f'{stage}_{spec}_{y}_independent_CR1',np.allclose(np.sqrt(np.diag(cov)[:len(regs)]),target.cluster_CR1_se,atol=1e-9))
    additional=pd.read_csv(DATA/'additional_regime_sensitivity.csv')
    for stage in ['primary','junior']:
        d=pd.read_csv(DATA/f'{stage}_component_model_input.csv')
        for spec,mask in [('without_2017_18',~d.year.isin([2017,2018])),('period_2008_2016',d.year<=2016),('period_2019_2023',d.year>=2019)]:
            z=d[mask];X=np.column_stack([z[['dS','dR_real']].values,pd.get_dummies(z.province,dtype=float).values,pd.get_dummies(z.year,dtype=float).values[:,1:]]);Y=z.DGW.values;b=np.linalg.lstsq(X,Y,rcond=None)[0];e=Y-X@b;inv=np.linalg.inv(X.T@X);meat=np.zeros_like(inv);G=z.province.nunique()
            for p in z.province.unique():
                m=z.province.values==p;score=X[m].T@e[m];meat+=np.outer(score,score)
            cov=G/(G-1)*(len(z)-1)/(len(z)-np.linalg.matrix_rank(X))*inv@meat@inv;want=additional[(additional.stage==stage)&(additional.specification==spec)].set_index('regressor').loc[['dS','dR_real']]
            check(f'{stage}_{spec}_additional_beta',np.allclose(b[:2],want.coefficient,atol=1e-9));check(f'{stage}_{spec}_additional_CR1',np.allclose(np.sqrt(np.diag(cov)[:2]),want.cluster_CR1_se,atol=1e-9))
    for name in ['component_primary_tests.csv','subsidy_exploratory_tests.csv']:
        d=pd.read_csv(DATA/name);check(name+'_four_tests',len(d)==4);check(name+'_9999_draws',(d.bootstrap_draws==9999).all());check(name+'_CI_search_closed',not d.WCR_search_boundary_accepted.any());check(name+'_CI_single_band',(d.WCR_disjoint_bands==1).all())
        ix=np.argsort(d.wild_restricted_p.values);want=np.minimum(1,np.maximum.accumulate(d.wild_restricted_p.values[ix]*(4-np.arange(4))));check(name+'_independent_Holm',np.allclose(d.Holm_family_p.values[ix],want))
    for p in sorted(FIG.glob('*.png')):
        im=Image.open(p);check(p.stem+'_white_background',im.convert('RGB').getpixel((0,0))==(255,255,255));check(p.stem+'_600dpi',abs(im.info['dpi'][0]-600)<1);check(p.stem+'_vector_pair',(p.with_suffix('.pdf').exists() and p.with_suffix('.svg').exists()))
    pd.DataFrame(checks).to_csv(DATA/'independent_validation.csv',index=False,encoding='utf-8-sig');(DATA/'validation_receipt.json').write_text(json.dumps(dict(checks=len(checks),all_passed=all(x['passed'] for x in checks),source_reread_count=len(cells),causal_identification=False),ensure_ascii=False,indent=2),encoding='utf8');print('PASS',len(checks))
if __name__=='__main__':main()
