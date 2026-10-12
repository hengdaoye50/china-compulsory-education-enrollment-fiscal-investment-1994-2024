"""Original organizer income and regional student history; accounting, no regression."""
from pathlib import Path
import json,zipfile,re,hashlib,sys
import pandas as pd
import numpy as np
from build_historical_income import ROOT,clean,decoded,rows_from,num,stage
OUT=ROOT/'research/data/举办者与地区历史_20261010'
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')
def main():
    OUT.mkdir(exist_ok=True);records=[];evidence=[];issues=[];header_repairs=[]
    for volume in range(2008,2026):
        archives=list((ROOT/'中国教育经费统计年鉴').glob(f'*{volume}*.zip'))
        if archives:
            archive=str(archives[0].relative_to(ROOT))
            with zipfile.ZipFile(archives[0]) as z:
                entries=[(decoded(i),z.read(i)) for i in z.infolist() if not i.is_dir() and re.match(r'^1[-—_ ]',decoded(i).replace('\\','/').split('/')[-1]) and '收入情况' in decoded(i)]
        else:
            archive='2024 rar; existing extracted files'
            entries=[(str(p.relative_to(ROOT)),p.read_bytes()) for p in (ROOT/f'research/用户提供资料/年鉴解压/卷{volume}').rglob('*.xlsx') if re.match(r'^1[-—_ ]',p.name) and '收入情况' in p.name]
        counts={}
        for name,b in entries:
            base=name.replace('\\','/').split('/')[-1]
            if '收入情况' not in base or '中央' in base or '地方' in base:continue
            group='departments' if '部门' in base else 'enterprise' if '企业办' in base else 'private' if '民办' in base else 'all'
            rows=rows_from(b);sr=[(i,stage(r[0]),r) for i,r in enumerate(rows) if r and stage(r[0])]
            if not sr:continue
            counts[group]=counts.get(group,0)+1
            first=next(i for i,r in enumerate(rows) if len(r)>1 and num(r[1]) is not None)
            headers=rows[:first];labels=['|'.join(clean(r[c]) for r in headers if c<len(r) and clean(r[c])) for c in range(max(map(len,rows)))]
            def find(pattern):return next((i for i,v in enumerate(labels) if re.search(pattern,v.replace('|',''))),None)
            cols={'total':1,'fiscal':find(r'^国家.*财政性.*教育经费'),'tuition':find(r'#.*学费|#.*学杂费'),'business':find(r'事业收入|^收入事业$')}
            repair=(volume-1,group) in [(2018,'enterprise'),(2019,'private')]
            if repair:
                assert cols['fiscal'] is None and len(labels)>=20
                cols['fiscal']=2  # Explicit corrupt-header mapping, checked below against non-overlapping components.
            assert all(cols[m] is not None for m in ['total','tuition','business']),(volume,name,labels)
            sid=hashlib.sha256((archive+'|'+name).encode()).hexdigest()[:24]
            unit='千元' if any('千元' in clean(v) for r in headers for v in r) else 'unit_pending'
            evidence.append(dict(source_id=sid,year=volume-1,organizer=group,archive=archive,table=name,table_sha256=hashlib.sha256(b).hexdigest(),unit=unit,headers=headers,column_labels=labels,stage_rows=[dict(row=i+1,stage=s,values=r) for i,s,r in sr]))
            for i,s,r in sr:
                a=dict(year=volume-1,stage=s,organizer=group,source_id=sid,unit=unit,scope_note='original organizer classification; departments does not certify all public schools; enterprise label changed',annual_scope_approved=False)
                for m,c in cols.items():a[m]=num(r[c]) if c is not None else None;a[m+'_cell']=f'{c+1}:{i+1}' if c is not None else '';a[m+'_original_header']=labels[c] if c is not None else ''
                a['fiscal_mapping_status']='explicit_corrupt_header_checked_numeric_components' if repair else 'original_header_match' if cols['fiscal'] is not None else 'broad_fiscal_total_not_reported'
                if repair:
                    components=[num(r[c]) for c in [3,10,12,13,14]]
                    diff=a['fiscal']-sum(v for v in components if v is not None)
                    assert abs(diff)<=5,(volume,group,s,diff)
                    header_repairs.append(dict(year=volume-1,stage=s,organizer=group,source_id=sid,source_row=i+1,original_header=labels[2],mapped_metric='broad_fiscal_total_C_column',nonoverlapping_component_columns='D;K;M;N;O',total_minus_observed_components=diff,original_blank_components=sum(v is None for v in components),basis='source-internal components and national organizer reconciliation; publisher wording not corrected'))
                a['fiscal_share_pct']=100*a['fiscal']/a['total'] if a['fiscal'] is not None and a['total'] else None
                records.append(a)
        if counts!={'all':1,'departments':1,'enterprise':1,'private':1}:issues.append(dict(year=volume-1,table_counts=counts))
    f=pd.DataFrame(records).sort_values(['stage','year','organizer'])
    assert not f.duplicated(['year','stage','organizer']).any()
    f.to_csv(OUT/'organizer_income_2007_2024.csv',index=False,encoding='utf-8-sig')
    (OUT/'organizer_original_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'organizer_selection_issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2),encoding='utf8')
    pd.DataFrame(header_repairs).to_csv(OUT/'fiscal_header_adjudication.csv',index=False,encoding='utf-8-sig')
    qc=[];mix=[]
    for (y,s),g in f.groupby(['year','stage']):
        ix=g.set_index('organizer');a=ix.loc['all'];parts=ix.loc[['departments','enterprise','private']]
        for m in ['total','fiscal','tuition','business']:
            qc.append(dict(year=y,stage=s,metric=m,total=a[m],observed_component_sum=parts[m].sum(min_count=1),blank_components=int(parts[m].isna().sum()),difference=a[m]-parts[m].sum(min_count=1),comparable_components=not(m=='fiscal' and parts.fiscal.isna().any()),interpretation='observed cells summed; original blanks retained, not zero imputed; missing broad fiscal definitions are not reconciliation failures'))
        for group in parts.index:
            p=parts.loc[group]
            mix.append(dict(year=y,stage=s,organizer=group,income_weight_pct=100*p.total/a.total,fiscal_share_within_group_pct=p.fiscal_share_pct,tuition_share_of_national_pct=100*p.tuition/a.tuition if pd.notna(p.tuition) and a.tuition else None,tuition_original_blank=pd.isna(p.tuition),nominal_total_yi=p.total/100000 if p.unit=='千元' else None))
    q=pd.DataFrame(qc);q.to_csv(OUT/'organizer_accounting_checks.csv',index=False,encoding='utf-8-sig')
    mix=pd.DataFrame(mix);mix.to_csv(OUT/'organizer_income_weights.csv',index=False,encoding='utf-8-sig')
    decomp=[]
    for s in ['primary','junior']:
        for a,b in [(2014,2024),(2017,2024),(2014,2021),(2021,2024)]:
            left=mix[(mix.stage==s)&(mix.year==a)].set_index('organizer');right=mix[(mix.stage==s)&(mix.year==b)].set_index('organizer')
            for group in left.index:
                x=left.loc[group];y=right.loc[group]
                # Midpoint decomposition of sum w*f. Units: percentage points of overall fiscal share.
                composition=(y.income_weight_pct-x.income_weight_pct)*(y.fiscal_share_within_group_pct+x.fiscal_share_within_group_pct)/200
                within=(y.fiscal_share_within_group_pct-x.fiscal_share_within_group_pct)*(y.income_weight_pct+x.income_weight_pct)/200
                decomp.append(dict(stage=s,start_year=a,end_year=b,organizer=group,composition_contribution_pp=composition,within_group_contribution_pp=within,total_contribution_pp=composition+within,interpretation='symmetric endpoint accounting, not causal attribution; yearly source classifications pending'))
    d=pd.DataFrame(decomp);d.to_csv(OUT/'fiscal_share_midpoint_decomposition.csv',index=False,encoding='utf-8-sig')
    st=pd.read_csv(ROOT/'research/data/口径核准_20261010/student_numeric_adjudicated.csv')
    st=st[st.province!='全国'];index=st.set_index(['province','stage','data_year'])
    regions=[];omissions=[]
    for a,b in [(1995,2005),(2005,2015),(2015,2024)]:
        for p in sorted(st.province.unique()):
            for s in ['primary','junior']:
                if p=='四川' and a<1997<=b:
                    omissions.append(dict(province=p,stage=s,start_year=a,end_year=b,reason='geographic boundary change'));continue
                try:x=index.loc[(p,s,a)];y=index.loc[(p,s,b)]
                except KeyError:
                    omissions.append(dict(province=p,stage=s,start_year=a,end_year=b,reason='endpoint unavailable'));continue
                regions.append(dict(province=p,stage=s,start_year=a,end_year=b,students_start=x.adjudicated_value,students_end=y.adjudicated_value,change_pct=100*(y.adjudicated_value/x.adjudicated_value-1),start_record_id=x.record_id,end_record_id=y.record_id,interpretation='fixed historical endpoints; school type/timing scope pending; no permanently shrinking label'))
    r=pd.DataFrame(regions);r.to_csv(OUT/'province_student_period_endpoints.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(omissions).to_csv(OUT/'province_period_omissions.csv',index=False,encoding='utf-8-sig')
    distributions=[];paired=[]
    for (a,b,s),g in r.groupby(['start_year','end_year','stage']):
        distributions.append(dict(start_year=a,end_year=b,stage=s,available_provinces=len(g),decreasing=int((g.change_pct<0).sum()),increasing=int((g.change_pct>0).sum()),unchanged=int((g.change_pct==0).sum()),median_change_pct=g.change_pct.median(),min_change_pct=g.change_pct.min(),max_change_pct=g.change_pct.max()))
    for (a,b),g in r.groupby(['start_year','end_year']):
        pivot=g.pivot(index='province',columns='stage',values='change_pct').dropna()
        for p,v in pivot.iterrows():paired.append(dict(province=p,start_year=a,end_year=b,primary_change_pct=v.primary,junior_change_pct=v.junior,direction_pair=('小学下降' if v.primary<0 else '小学上升' if v.primary>0 else '小学不变')+'／'+('初中下降' if v.junior<0 else '初中上升' if v.junior>0 else '初中不变')))
    distributions=pd.DataFrame(distributions);paired=pd.DataFrame(paired)
    distributions.to_csv(OUT/'province_student_phase_distributions.csv',index=False,encoding='utf-8-sig')
    paired.to_csv(OUT/'province_stage_direction_pairs.csv',index=False,encoding='utf-8-sig')
    checks=dict(organizer_144_rows=len(f)==144,source_72_tables=len(evidence)==72,all_units_explicit=bool((f.unit=='千元').all()),no_selection_issues=not issues,organizer_total_fiscal_within_5=bool((q[q.metric.isin(['total','fiscal']) & q.comparable_components].difference.abs()<=5).all()),tuition_business_observed_accounting_within_5=bool((q[q.metric.isin(['tuition','business'])].difference.abs()<=5).all()),regional_counts_29_31_31=distributions.available_provinces.tolist()==[29,29,31,31,31,31],regional_endpoints_recalculate=bool(np.allclose(r.change_pct,100*(r.students_end/r.students_start-1))),four_corrupt_header_cells_component_verified=len(header_repairs)==4 and all(abs(r['total_minus_observed_components'])<=5 for r in header_repairs))
    delta=[]
    for (s,a,b),g in d.groupby(['stage','start_year','end_year']):
        left=f[(f.stage==s)&(f.year==a)&(f.organizer=='all')].iloc[0];right=f[(f.stage==s)&(f.year==b)&(f.organizer=='all')].iloc[0]
        delta.append(dict(stage=s,start_year=a,end_year=b,observed_change_pp=right.fiscal_share_pct-left.fiscal_share_pct,decomposition_sum_pp=g.total_contribution_pp.sum(),composition_pp=g.composition_contribution_pp.sum(),within_pp=g.within_group_contribution_pp.sum()))
    delta=pd.DataFrame(delta);delta.to_csv(OUT/'fiscal_share_decomposition_totals.csv',index=False,encoding='utf-8-sig')
    checks['decomposition_matches_original_overall_within_rounding']=bool(np.allclose(delta.observed_change_pp,delta.decomposition_sum_pp,atol=0.00001))
    old=json.loads((ROOT/'research/data/长期财政数据建设_20261010/build_receipt.json').read_text(encoding='utf8'))['protected_hashes']
    checks['protected_files_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in old.items())
    receipt=dict(checks=checks,all_passed=all(checks.values()),original_blank_tuition_rows=int(f.tuition.isna().sum()),max_accounting_difference=float(q.difference.abs().max()),regression_run=False,inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'research/data/口径核准_20261010/student_numeric_adjudicated.csv',ROOT/'research/data/历史趋势描述_20261010/national_income_original_series.csv']})
    (OUT/'description_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(receipt,ensure_ascii=False));print(distributions.to_string(index=False));print(delta.to_string(index=False));print(mix[mix.year.isin([2013,2024])].to_string(index=False));print(paired.groupby(['start_year','end_year','direction_pair']).size().to_string())
    assert receipt['all_passed'],checks
if __name__=='__main__':main()
