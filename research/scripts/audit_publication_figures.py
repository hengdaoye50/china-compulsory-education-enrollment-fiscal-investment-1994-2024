"""Numerical and export checks for the revised figure set; no hypothesis tests."""
from pathlib import Path
import json,hashlib
import pandas as pd
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'research/figures/正式学术图组_20261011';QA=OUT/'qa';QA.mkdir(exist_ok=True)
manifest=json.loads((OUT/'figure_manifest.json').read_text(encoding='utf8'))
tables={n:pd.read_csv(OUT/'figure_data'/f'fig{n:02d}.csv') for n in range(1,9)}
checks={}
checks['source_files_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in manifest['input_sha256'].items())
checks['exporter_text_bounds_all_pass']=all(manifest['checks'].values())
checks['national_student_count_and_unique']=len(tables[1])==60 and not tables[1].duplicated(['stage','year']).any()
i=tables[2]
checks['income_share_formula']=bool(np.allclose(i.fiscal_share_pct,i.fiscal_thousand_yuan/i.total_thousand_yuan*100))
checks['income_2006_unit_confirmed_amount_restored']=bool(i.loc[i.year==2006,'fiscal_yi'].notna().all() and (i.loc[i.year==2006,'status']=='published_cross_source_unit_confirmed').all())
checks['1994_estimates_explicitly_identified']=bool(len(i)==62 and (i.loc[i.year==1994,'status']=='model_backcast_budget_constrained').all())
checks['early_accounting_regimes_identified']=bool((i.loc[i.year.between(1995,1997),'accounting']=='expenditure').all() and (i.loc[i.year>=1998,'accounting']=='income').all())
c=tables[4]
checks['personal_share_formula']=bool(np.allclose(c.personal_share_of_PC_pct,c.P_thousand_yuan/(c.P_thousand_yuan+c.C_thousand_yuan)*100))
early=c[(c.year==1995)&(c.stage=='junior')]
checks['1995_junior_PC_present_total_not_approved']=len(early)==1 and early[['P_thousand_yuan','C_thousand_yuan']].notna().all().all() and early.numeric_status.iloc[0]=='observed_PC_only_total_not_approved'
for n,metric in [(5,'PC'),(7,'C')]:
 r=tables[n];n_years=r.end_year-r.start_year;ratio=(r[metric+'_end_thousand']/r[metric+'_start_thousand'])/r.CPI_cumulative_factor
 checks[f'fig{n:02d}_real_cumulative_recomputed']=bool(np.allclose(r[metric+'_real_change_pct'],(ratio-1)*100))
 checks[f'fig{n:02d}_real_annualized_recomputed']=bool(np.allclose(r[metric+'_real_annualized_pct'],(ratio**(1/n_years)-1)*100))
r=tables[5];sets=[set(g.province) for _,g in r.groupby(['stage','start_year','end_year'])]
checks['fig05_same_28_regions_all_groups']=len(sets)==6 and all(len(s)==28 and s==sets[0] for s in sets)
r=tables[6]
checks['fig06_pair_differences']=bool(np.allclose(r.change_annualized_percentage_points,r.later_annualized_pct-r.earlier_annualized_pct))
counts={s:int((g.change_annualized_percentage_points<0).sum()) for s,g in r.groupby('stage')}
checks['fig06_decline_counts']=counts=={'primary':28,'junior':26}
checks['fig07_all_31_regions']=len(tables[7])==62 and all(g.province.nunique()==31 for _,g in tables[7].groupby('stage'))
r=tables[8];checks['fig08_decomposition_adds_to_observed']=bool(np.allclose(r.observed_change_pp,r.composition_pp+r.within_pp))
metadata=[]
for f in sorted((OUT/'png').glob('fig*.png')):
 im=Image.open(f);alpha=im.getchannel('A').getextrema() if im.mode=='RGBA' else None
 metadata.append({'file':f.name,'pixels':list(im.size),'dpi':im.info.get('dpi'),'white_corner':im.convert('RGB').getpixel((0,0))==(255,255,255),'opaque':alpha is None or alpha==(255,255)})
checks['all_8_exports_white_opaque_600dpi']=len(metadata)==8 and all(m['white_corner'] and m['opaque'] and m['dpi'][0]>599 for m in metadata)
old=json.loads((ROOT/'research/data/长期财政数据建设_20261010/build_receipt.json').read_text(encoding='utf8'))['protected_hashes']
checks['protected_inputs_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in old.items())
checks={k:bool(v) for k,v in checks.items()}
report={'revision_date':'2026-10-11','checks':checks,'all_passed':bool(all(checks.values())),'metadata':metadata,'paired_slower_counts':counts,'scope':'All eight figures and their plotted data; not a complete raw-yearbook pipeline certification','visual_review':'All eight combined previews inspected; figs 4/5/6/8 captions and layouts revised; complete final Word report not rendered'}
final_record=ROOT/'正式分析报告_20261011/报告制作记录.json'
if final_record.exists():
 final=json.loads(final_record.read_text(encoding='utf8'))
 report['final_word_report_verified']=bool(final.get('render_verified') and final.get('all_checks_passed'))
 if report['final_word_report_verified']:report['visual_review']='All eight figures reviewed in the final nine-page Word-to-PDF report; all page PNGs inspected, wording revisions rechecked; final report has a separate numerical and layout receipt.'
(QA/'revision_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
assert report['all_passed'],checks
print(json.dumps({'all_passed':report['all_passed'],'checks':len(checks),'slower_counts':counts},ensure_ascii=False))
