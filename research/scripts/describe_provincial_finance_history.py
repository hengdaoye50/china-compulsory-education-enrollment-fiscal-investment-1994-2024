"""Segmented provincial spending distributions with chained provincial CPI."""
from pathlib import Path
import json,re,hashlib,math,sys
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/data/省级经费历史分布_20261010'
FIN=ROOT/'research/data/经费共同样本核查_20261010/PC_original_numeric_checks.csv'
EVI=FIN.parent/'PC_original_evidence.json'
ST=ROOT/'research/data/口径核准_20261010/student_numeric_adjudicated.csv'
CPI=ROOT/'research/data/长期财政数据建设_20261010/supplement_original_candidates.csv'
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')
def main():
    OUT.mkdir(exist_ok=True)
    f=pd.read_csv(FIN,keep_default_na=False)
    e={r['evidence_id']:r for r in json.loads(EVI.read_text(encoding='utf8'))}
    f=f[(f.school_scope=='local_affiliation')&(f.province!='全国')&f.numeric_status.str.startswith('accepted')]
    f=f[f.evidence_id.map(lambda k:bool(re.match(r'^4[-—_ ]',e[k]['table'].replace('\\','/').split('/')[-1])))]
    assert not f.duplicated(['year','province','stage']).any()
    f['P']=pd.to_numeric(f.P);f['C']=pd.to_numeric(f.C);f['PC']=f.P+f.C
    assert (f[['P','C']]>0).all().all() and (f.unit=='千元').all()
    index=f.set_index(['year','province','stage'])
    st=pd.read_csv(ST);st=st[st.province!='全国'].set_index(['data_year','province','stage'])
    price=pd.read_csv(CPI,keep_default_na=False);price=price[price.metric=='CPI_yoy']
    assert not price.duplicated(['data_year','province']).any()
    prices={(int(r.data_year),r.province):float(r.raw_value)/100 for r in price.itertuples() if r.raw_value}
    price_ids={(int(r.data_year),r.province):r.record_id for r in price.itertuples() if r.raw_value}
    ends=[];excluded=[]
    for a,b in [(1995,2006),(2007,2013),(2013,2023),(2017,2023),(2023,2024)]:
        assert not a<=2006<b
        for p in sorted(f.province.unique()):
            for s in ['primary','junior']:
                if p=='四川' and a<1997<=b:
                    excluded.append(dict(start_year=a,end_year=b,province=p,stage=s,reason='administrative_boundary_change'));continue
                keys=[(y,p,s) for y in [a,b]]
                if any(k not in index.index for k in keys):
                    excluded.append(dict(start_year=a,end_year=b,province=p,stage=s,reason='source_internal_PC_endpoint_unavailable'));continue
                if any((y,p) not in prices for y in range(a+1,b+1)):
                    excluded.append(dict(start_year=a,end_year=b,province=p,stage=s,reason='CPI_chain_incomplete'));continue
                left=index.loc[keys[0]];right=index.loc[keys[1]]
                factor=math.prod(prices[(y,p)] for y in range(a+1,b+1))
                r=dict(start_year=a,end_year=b,province=p,stage=s,CPI_cumulative_factor=factor,CPI_record_ids=';'.join(price_ids[(y,p)] for y in range(a+1,b+1)),start_evidence_id=left.evidence_id,end_evidence_id=right.evidence_id,finance_scope='local_affiliation_all_source',annual_definition_status='within-classification original endpoints; annual comparability pending',terminal_capital_label_pending=b==2024,student_scope='all organizers regional context only; not same funded population',per_student_calculated=False)
                for m in ['P','C','PC']:
                    x=float(left[m]);y=float(right[m]);ratio=y/x/factor
                    r[m+'_start_thousand']=x;r[m+'_end_thousand']=y
                    r[m+'_nominal_change_pct']=100*(y/x-1);r[m+'_real_change_pct']=100*(ratio-1);r[m+'_real_annualized_pct']=100*(ratio**(1/(b-a))-1)
                if keys[0] in st.index and keys[1] in st.index:
                    x=st.loc[keys[0]];y=st.loc[keys[1]]
                    r['students_start']=float(x.adjudicated_value);r['students_end']=float(y.adjudicated_value);r['student_change_pct']=100*(r['students_end']/r['students_start']-1)
                    r['student_start_record_id']=x.record_id;r['student_end_record_id']=y.record_id
                ends.append(r)
    endpoint=pd.DataFrame(ends)
    endpoint.to_csv(OUT/'province_finance_real_endpoints.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(excluded).to_csv(OUT/'endpoint_exclusions.csv',index=False,encoding='utf-8-sig')
    summaries=[]
    for (a,b,s),g in endpoint.groupby(['start_year','end_year','stage']):
        row=dict(start_year=a,end_year=b,stage=s,provinces=len(g),student_endpoint_decrease=int((g.student_change_pct<0).sum()),PC_up_with_students_down=int(((g.student_change_pct<0)&(g.PC_real_change_pct>0)).sum()),P_up_C_down=int(((g.P_real_change_pct>0)&(g.C_real_change_pct<0)).sum()),terminal_pending=b==2024)
        for m in ['P','C','PC']:
            v=g[m+'_real_change_pct'];row[m+'_real_increasing']=int((v>0).sum());row[m+'_real_decreasing']=int((v<0).sum());row[m+'_real_median_pct']=v.median();row[m+'_real_q25_pct']=v.quantile(.25);row[m+'_real_q75_pct']=v.quantile(.75);row[m+'_annualized_median_pct']=g[m+'_real_annualized_pct'].median()
        summaries.append(row)
    summary=pd.DataFrame(summaries);summary.to_csv(OUT/'segmented_province_growth_distributions.csv',index=False,encoding='utf-8-sig')
    old=pd.read_csv(ROOT/'research/data/三十年纵向分析_20261010/segmented_local_finance_changes.csv')
    annual=[]
    for r in old.itertuples(index=False):
        keys=[(r.year-1,r.province,r.stage),(r.year,r.province,r.stage)]
        if any(k not in index.index for k in keys):continue
        left=index.loc[keys[0]];right=index.loc[keys[1]]
        dpc=math.log(float(right.PC)/float(left.PC))-math.log(prices[(r.year,r.province)])
        annual.append(dict(year=r.year,province=r.province,stage=r.stage,period=r.period,student_change_pct=100*math.expm1(r.dS),P_real_change_pct=100*math.expm1(r.dP_real),C_real_change_pct=100*math.expm1(r.dC_real),PC_real_change_pct=100*math.expm1(dpc),sustained_student_decline=r.shrink2,finance_scope='local_affiliation_all_source',student_scope='regional context; not same funded population',start_evidence_id=left.evidence_id,end_evidence_id=right.evidence_id))
    annual=pd.DataFrame(annual);annual.to_csv(OUT/'province_finance_annual_real_changes.csv',index=False,encoding='utf-8-sig')
    ay=[]
    for (y,s),g in annual.groupby(['year','stage']):
        ay.append(dict(year=y,stage=s,provinces=len(g),P_decreasing=int((g.P_real_change_pct<0).sum()),C_decreasing=int((g.C_real_change_pct<0).sum()),PC_decreasing=int((g.PC_real_change_pct<0).sum()),P_median_pct=g.P_real_change_pct.median(),C_median_pct=g.C_real_change_pct.median(),PC_median_pct=g.PC_real_change_pct.median(),terminal_pending=y==2024))
    pd.DataFrame(ay).to_csv(OUT/'annual_province_growth_distributions.csv',index=False,encoding='utf-8-sig')
    quadrants=[]
    for (period,s),g in annual.groupby(['period','stage']):
        quadrants.append(dict(period=period,stage=s,province_years=len(g),student_annual_decrease=int((g.student_change_pct<0).sum()),PC_up_with_student_annual_down=int(((g.student_change_pct<0)&(g.PC_real_change_pct>0)).sum()),P_up_C_down=int(((g.P_real_change_pct>0)&(g.C_real_change_pct<0)).sum()),PC_real_down=int((g.PC_real_change_pct<0).sum())))
    pd.DataFrame(quadrants).to_csv(OUT/'annual_spending_student_quadrants.csv',index=False,encoding='utf-8-sig')
    checks=dict(no_classification_cross_2007=not bool(((endpoint.start_year<=2006)&(endpoint.end_year>2006)).any()),positive_CPI_factors=bool((endpoint.CPI_cumulative_factor>0).all()),province_endpoints_unique=not endpoint.duplicated(['start_year','end_year','province','stage']).any(),PC_equals_P_plus_C=bool(np.allclose(endpoint.PC_start_thousand,endpoint.P_start_thousand+endpoint.C_start_thousand)&np.allclose(endpoint.PC_end_thousand,endpoint.P_end_thousand+endpoint.C_end_thousand)),real_growth_recalculates=all(np.allclose(endpoint[m+'_real_change_pct'],100*(endpoint[m+'_end_thousand']/endpoint[m+'_start_thousand']/endpoint.CPI_cumulative_factor-1)) for m in ['P','C','PC']),annual_PC_recomputed_from_same_sources=len(annual)==len(old),S_not_divided_into_local_finance=not bool(endpoint.per_student_calculated.any()),geographic_boundary_excluded=not bool(((endpoint.province=='四川')&(endpoint.start_year<1997)&(endpoint.end_year>=1997)).any()),full_CPI_chain_recorded=all(len(str(r.CPI_record_ids).split(';'))==r.end_year-r.start_year for r in endpoint.itertuples()),terminal_2024_separate=bool(endpoint[endpoint.end_year==2024].terminal_capital_label_pending.all()))
    protected=json.loads((ROOT/'research/data/长期财政数据建设_20261010/build_receipt.json').read_text(encoding='utf8'))['protected_hashes']
    chain_matches=[];chain_complete=[];chain_gaps=[]
    for r in endpoint.itertuples():
        g=annual[(annual.province==r.province)&(annual.stage==r.stage)&(annual.year>r.start_year)&(annual.year<=r.end_year)]
        complete=set(g.year)==set(range(r.start_year+1,r.end_year+1))
        chain_complete.append(complete);chain_gaps.append(';'.join(map(str,sorted(set(range(r.start_year+1,r.end_year+1))-set(g.year)))))
        if complete:chain_matches.append(all(np.isclose(math.prod(1+v/100 for v in g[m+'_real_change_pct']),1+getattr(r,m+'_real_change_pct')/100,rtol=1e-10) for m in ['P','C','PC']))
    endpoint['annual_finance_chain_complete']=chain_complete;endpoint['missing_annual_finance_edges']=chain_gaps
    endpoint.to_csv(OUT/'province_finance_real_endpoints.csv',index=False,encoding='utf-8-sig')
    checks['complete_annual_chains_match_302_endpoints']=len(chain_matches)==302 and all(chain_matches)
    checks['two_incomplete_chains_explicitly_marked']=endpoint[~endpoint.annual_finance_chain_complete][['province','stage','missing_annual_finance_edges']].to_dict('records')==[{'province':'内蒙古','stage':'junior','missing_annual_finance_edges':'2011;2012'},{'province':'黑龙江','stage':'primary','missing_annual_finance_edges':'2011;2012'}]
    checks['protected_files_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
    receipt=dict(checks=checks,all_passed=all(checks.values()),province_endpoint_rows=len(endpoint),annual_change_rows=len(annual),exclusions=len(excluded),price_method='product of provincial CPI previous-year=100; approximate purchasing power, not education-specific cost index; no interpolation',PC_definition='P+C only, excludes separately listed K; not full E',model_scope_approved=False,regression_run=False,inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [FIN,EVI,ST,CPI]})
    (OUT/'description_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    assert receipt['all_passed'],checks
    print(json.dumps(receipt,ensure_ascii=False));print(summary.to_string(index=False));print(pd.DataFrame(quadrants).to_string(index=False));print('C decline endpoint provinces 2017_2023',endpoint[(endpoint.start_year==2017)&(endpoint.C_real_change_pct<0)][['province','stage','P_real_change_pct','C_real_change_pct','PC_real_change_pct']].to_string(index=False))
if __name__=='__main__':main()
