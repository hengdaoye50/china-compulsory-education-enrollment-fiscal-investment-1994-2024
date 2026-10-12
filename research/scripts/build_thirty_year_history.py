"""Thirty-year student history and segmented expenditure composition, never per-student."""
import json,csv,re,hashlib,sys,math
from pathlib import Path
from collections import Counter
import pandas as pd
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/data/三十年纵向分析_20261010'
STUDENTS=ROOT/'research/data/口径核准_20261010/student_numeric_adjudicated.csv'
FIN=ROOT/'research/data/经费共同样本核查_20261010/PC_original_numeric_checks.csv'
EVIDENCE=FIN.parent/'PC_original_evidence.json'
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')

def main():
    OUT.mkdir(exist_ok=True)
    st=pd.read_csv(STUDENTS,keep_default_na=False)
    national=st[st.province=='全国'][['data_year','stage','adjudicated_value','record_id','source_id','school_scope']].copy()
    national.columns=['year','stage','students','record_id','source_id','school_scope']
    national['students']=national.students.astype(int)
    national=national.sort_values(['stage','year'])
    national['student_change_pct']=national.groupby('stage').students.pct_change(fill_method=None)*100
    national['scope_status']='source_internal_numeric; ordinary/type/timing annual definitions pending'
    national.to_csv(OUT/'national_students_1995_2024.csv',index=False,encoding='utf-8-sig')
    endpoints=[]
    periods={'primary':[(1995,1997),(1997,2013),(2013,2023),(2023,2024),(1995,2024)],'junior':[(1995,2003),(2003,2015),(2015,2024),(1995,2024)]}
    for stage,ps in periods.items():
        n=national[national.stage==stage].set_index('year')
        for a,b in ps:
            sa=int(n.loc[a,'students']);sb=int(n.loc[b,'students'])
            endpoints.append(dict(stage=stage,start_year=a,end_year=b,start_students=sa,end_students=sb,change_pct=(sb/sa-1)*100,annualized_pct=((sb/sa)**(1/(b-a))-1)*100,interpretation='descriptive national original series; not causal and not scope certification'))
    pd.DataFrame(endpoints).to_csv(OUT/'national_student_endpoints.csv',index=False,encoding='utf-8-sig')
    # Region-specific recurrent decline spells. Split uncertain Sichuan administrative edges.
    changes=[];spells=[]
    for (p,stage),group in st[st.province!='全国'].groupby(['province','stage']):
        rows={int(r.data_year):r for r in group.itertuples(index=False)};active=[]
        def close(right_censored=False,scope_break=False):
            if len(active)>=2:
                first,last=active[0],active[-1]
                a=float(rows[first-1].adjudicated_value);b=float(rows[last].adjudicated_value)
                spells.append(dict(province=p,stage=stage,first_decline_year=first,last_decline_year=last,baseline_year=first-1,decline_years=len(active),student_start=int(a),student_end=int(b),change_pct=(b/a-1)*100,left_study_edge=first==1996,right_study_edge=right_censored,terminated_by_geography_break=scope_break,scope_status='student type and timing still pending; geographic break explicitly omitted'))
            active.clear()
        for y in range(1996,2025):
            if y not in rows or y-1 not in rows or (p=='四川' and y in [1997,1998]):close(scope_break=True);continue
            previous=float(rows[y-1].adjudicated_value);current=float(rows[y].adjudicated_value);decline=current<previous
            changes.append(dict(year=y,province=p,stage=stage,student_previous=int(previous),student_current=int(current),student_change_pct=(current/previous-1)*100,decline=decline,current_record_id=rows[y].record_id,previous_record_id=rows[y-1].record_id,geography_status='stable_edge_candidate'))
            if decline:active.append(y)
            else:close()
        close(right_censored=True)
    changes=pd.DataFrame(changes);spells=pd.DataFrame(spells)
    changes.to_csv(OUT/'province_student_changes_1996_2024.csv',index=False,encoding='utf-8-sig')
    spells.to_csv(OUT/'recurrent_student_decline_spells.csv',index=False,encoding='utf-8-sig')
    recurrence=spells.groupby(['province','stage']).size().rename('spells').reset_index()
    recurrence.to_csv(OUT/'province_decline_recurrence.csv',index=False,encoding='utf-8-sig')
    phase=[]
    for label,lo,hi in [('1996_2005',1996,2005),('2006_2015',2006,2015),('2016_2024',2016,2024)]:
        for stage in ['primary','junior']:
            s=changes[(changes.stage==stage)&changes.year.between(lo,hi)]
            phase.append(dict(period=label,stage=stage,valid_province_year_edges=len(s),declining_edges=int(s.decline.sum()),declining_share=float(s.decline.mean()),provinces_ever_declining=s[s.decline].province.nunique()))
    pd.DataFrame(phase).to_csv(OUT/'student_decline_phase_distribution.csv',index=False,encoding='utf-8-sig')
    evidence={e['evidence_id']:e for e in json.loads(EVIDENCE.read_text(encoding='utf8'))}
    finance=pd.read_csv(FIN,keep_default_na=False);records=[]
    for r in finance[finance.province=='全国'].itertuples(index=False):
        e=evidence[r.evidence_id];name=e['table'].replace('\\','/').split('/')[-1]
        # Part 5 once carried a misleading Part-4 title; select expenditure Part 4 by provenance too.
        if not re.match(r'^4[-—_ ]',name):continue
        P=Decimal(r.P) if r.P else None;C=Decimal(r.C) if r.C else None
        status='approved_source_internal' if r.numeric_status.startswith('accepted') else 'observed_PC_only_total_not_approved'
        share=float(P/(P+C)*100) if P is not None and C is not None else None
        records.append(dict(year=r.year,stage=r.stage,school_scope=r.school_scope,P_thousand_yuan=r.P,C_thousand_yuan=r.C,E_thousand_yuan=r.E,personal_share_of_PC_pct=share,numeric_status=status,evidence_id=r.evidence_id,table=e['table'],source_sha256=e['source_sha256'],classification_segment='old_1995_2006' if r.year<=2006 else 'post_2007_annual_scope_pending',capital_label_edge_pending=r.year==2024,per_student_calculated=False,model_scope_approved=False))
    finance=pd.DataFrame(records).sort_values(['school_scope','stage','year'])
    assert not finance.duplicated(['year','stage','school_scope']).any()
    finance.to_csv(OUT/'national_finance_composition_1995_2024.csv',index=False,encoding='utf-8-sig')
    local=finance[finance.school_scope=='local_affiliation'];assert len(local)==60
    finend=[]
    # Intervals remain definition-pending descriptive candidates; no compound cross-break claim.
    for stage in ['primary','junior']:
        n=local[local.stage==stage].set_index('year')
        for a,b in ([(1995,2006),(2007,2013),(2013,2023),(2023,2024)] if stage=='primary' else [(1996,2006),(2007,2013),(2013,2023),(2023,2024)]):
            sa=float(n.loc[a,'personal_share_of_PC_pct']);sb=float(n.loc[b,'personal_share_of_PC_pct'])
            finend.append(dict(stage=stage,scope='local_affiliation',start_year=a,end_year=b,personal_PC_share_start=sa,personal_PC_share_end=sb,change_percentage_points=sb-sa,classification_cross_2007=False,definition_status='descriptive original share; annual comparability pending',capital_label_pending=b==2024))
    pd.DataFrame(finend).to_csv(OUT/'segmented_finance_structure_changes.csv',index=False,encoding='utf-8-sig')
    checks=dict(national_student_60=len(national)==60,national_30_year_each=all(national[national.stage==s].year.nunique()==30 for s in ['primary','junior']),local_finance_60=len(local)==60,no_2006_2007_finance_endpoint=all(not(a['start_year']<=2006<a['end_year']) for a in finend),spells_all_at_least_two=bool((spells.decline_years>=2).all()),geographic_edges_omitted=not bool(((changes.province=='四川')&changes.year.isin([1997,1998])).any()),no_per_student_division=not finance.per_student_calculated.any())
    receipt=dict(years='1995_2024',student_province_edges=len(changes),decline_spells=len(spells),recurrent_provinces_by_stage={s:int(((recurrence.stage==s)&(recurrence.spells>=2)).sum()) for s in ['primary','junior']},checks=checks,inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [STUDENTS,FIN,EVIDENCE]})
    (OUT/'history_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');assert all(checks.values())
    print(json.dumps(receipt,ensure_ascii=False));print(pd.DataFrame(endpoints).to_string(index=False));print(pd.DataFrame(finend).to_string(index=False))

if __name__=='__main__':main()
