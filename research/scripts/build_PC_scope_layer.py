"""Recheck all-source expenditure originals; build a scope-pending matching layer."""
import csv, json, re, hashlib, io
from collections import defaultdict, Counter
from decimal import Decimal
from pathlib import Path
import openpyxl
from inspect_bridge_evidence import ROOT, sheets, getbytes, norm

BASE = ROOT / 'research/data/长期财政数据建设_20261010'
OUT = ROOT / 'research/data/经费共同样本核查_20261010'
PROVS = '北京 天津 河北 山西 内蒙古 辽宁 吉林 黑龙江 上海 江苏 浙江 安徽 福建 江西 山东 河南 湖北 湖南 广东 广西 海南 重庆 四川 贵州 云南 西藏 陕西 甘肃 青海 宁夏 新疆'.split()

def read(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def write(n, rows):
    with (OUT/n).open('w', encoding='utf-8-sig', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def number(v):
    s=str(v).strip()
    return Decimal(s.replace(',', '')) if re.fullmatch(r'[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?', s) else None

def main():
    OUT.mkdir(exist_ok=True)
    inputs=[BASE/'raw_value_ledger.csv', BASE/'source_registry.csv', ROOT/'research/data/口径核准_20261010/student_numeric_adjudicated.csv', ROOT/'research/data/财政收入补核_20261010/R_province_year_numeric_panel_with_summaries.csv',BASE/'education_finance_table_dictionary.csv']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    registry={r['source_id']:r for r in read(inputs[1])}
    headeridx={r['source_id']:json.loads(r['headers']) for r in read(BASE/'education_finance_table_dictionary.csv')}
    ledger=read(inputs[0]); groups=defaultdict(list)
    for r in ledger:
        if r['stage'] not in ['primary','junior'] or r['metric'] not in ['E','P','C','K'] or r['funding_scope'] not in ['all_source','all-source education spending']: continue
        s=registry[r['source_id']]
        groups[(r['data_year'],r['stage'],r['province'],r['school_scope'],s['archive'],s['table'],s['sheet'])].append(r)
    cache={}; evidences=[]; result=[]
    def original(s):
        key=(s['archive'],s['table'],s['sheet'])
        if key not in cache:
            if s['source_quality']=='previously_extracted_user_excel':
                b=(ROOT/s['table']).read_bytes(); w=openpyxl.load_workbook(io.BytesIO(b),read_only=True,data_only=True)
                rr=list(w[s['sheet']].iter_rows(values_only=True)); w.close()
            else:
                b=getbytes(s); rr=dict(sheets(s))[s['sheet']]
            assert hashlib.sha256(b).hexdigest()==s['table_sha256'], key
            cache[key]=rr
        return cache[key]
    for key, cells in groups.items():
        year,stage,province,scope,archive,table,sheet=key
        bymetric={m:[r for r in cells if r['metric']==m] for m in ['E','P','C','K']}
        unique=all(len(v)==1 for v in bymetric.values())
        s=registry[cells[0]['source_id']]; rr=original(s)
        headers=[(i+1,list(row)) for i,row in enumerate(rr) if any('单位' in norm(v) for v in row)]
        units=[dict(row=i,column=j+1,raw=v) for i,row in headers for j,v in enumerate(row) if '单位' in norm(v) and '千元' in norm(v)]
        title=norm(rr[0][0]) if rr and rr[0] else ''
        # Do not let a misclassified budget/subsidy title enter the all-source layer.
        actual_title='|'.join(norm(v) for row in rr[:5] for v in row[:1])
        title_ok='支出' in actual_title and not any(t in actual_title for t in ['预算','补助'])
        matches=all(str(rr[int(r['source_row'])-1][int(r['source_column'])-1] if rr[int(r['source_row'])-1][int(r['source_column'])-1] is not None else '')==r['raw_value'] for r in cells)
        ns={m:number(v[0]['raw_value']) if len(v)==1 else None for m,v in bymetric.items()}
        difference=ns['E']-ns['P']-ns['C']-ns['K'] if all(v is not None for v in ns.values()) else None
        # Four integer-valued displayed cells permit at most 2 original units of rounding.
        tolerance=sum(min(Decimal('.5'),Decimal(10)**number(v[0]['raw_value']).as_tuple().exponent/2) for v in bymetric.values()) if unique and all(v is not None for v in ns.values()) else Decimal(0)
        numeric_ok=bool(units) and title_ok and matches and unique and difference is not None and abs(difference)<=tolerance and ns['P']>0 and ns['C']>0 and ns['K']>=0
        component_checks={}
        for m in ['P','C']:
            if int(year)<2007 or len(bymetric[m])!=1: continue
            r=bymetric[m][0]; ri=int(r['source_row'])-1; ci=int(r['source_column'])-1
            component_headers=headeridx.get(r['source_id'],rr[:6])
            observed=[]
            for j in [ci+1,ci+2]:
                v=rr[ri][j] if len(rr[ri])>j else None
                label='|'.join(norm(row[j]) for row in component_headers if len(row)>j and norm(row[j]))
                observed.append(dict(row=ri+1,column=j+1,label=label,raw=v,numeric='' if v is None or number(v) is None else str(number(v))))
            valid=ns[m] is not None and all(c['numeric'] for c in observed)
            delta=ns[m]-sum((Decimal(c['numeric']) for c in observed),Decimal(0)) if valid else None
            expected=['工资福利','对个人和家庭'] if m=='P' else ['商品和服务','资本性']
            semantic=all(t in c['label'].replace('|','') for t,c in zip(expected,observed))
            component_checks[m]=dict(cells=observed,difference='' if delta is None else str(delta),headers_verified=semantic,passed=semantic and delta is not None and abs(delta)<=Decimal('1.5'))
        # Approve P/C through their own components without asserting a blank K is zero.
        pc_only=bool(units) and title_ok and matches and unique and ns['P'] is not None and ns['C'] is not None and ns['P']>0 and ns['C']>0 and all(component_checks.get(m,{}).get('passed',False) for m in ['P','C'])
        eid='pc_'+hashlib.sha256('|'.join(key).encode()).hexdigest()[:24]
        evidence=dict(evidence_id=eid,year=year,stage=stage,province=province,archive=archive,table=table,sheet=sheet,source_sha256=s['table_sha256'],unit_cells=units,title=actual_title,cells=cells,PC_component_checks=component_checks)
        evidences.append(evidence)
        result.append(dict(evidence_id=eid,year=year,province=province,stage=stage,school_scope=scope,unit='千元' if units else 'unit_pending',source_ids='|'.join(sorted({r['source_id'] for r in cells})),source_record_ids='|'.join(r['record_id'] for r in cells),E='' if ns['E'] is None else str(ns['E']),P='' if ns['P'] is None else str(ns['P']),C='' if ns['C'] is None else str(ns['C']),K='' if ns['K'] is None else str(ns['K']),difference='' if difference is None else str(difference),tolerance=str(tolerance),original_coordinates_verified=matches,all_source_title_verified=title_ok,classification_segment='old_classification' if int(year)<=2006 else 'post_2007_definition_needs_annual_bridge',numeric_status='accepted_source_internal_only' if numeric_ok else 'accepted_PC_components_EK_pending' if pc_only else 'pending',model_eligible=False))
    write('PC_original_numeric_checks.csv',result)
    (OUT/'PC_original_evidence.json').write_text(json.dumps(evidences,ensure_ascii=False,indent=2),encoding='utf8')
    selected=defaultdict(list)
    for r in result:
        if r['school_scope'] in ['all_affiliations_candidate','all_affiliations'] and r['province'] in PROVS and r['numeric_status'].startswith('accepted'):selected[(r['year'],r['province'],r['stage'])].append(r)
    students={(r['data_year'],r['province'],r['stage']):r for r in read(inputs[2]) if r['province'] in PROVS}
    revenues={(r['year'],r['province']):r for r in read(inputs[3])}
    matched=[]
    for y in range(1995,2025):
        for p in PROVS:
            for stage in ['primary','junior']:
                k=(str(y),p,stage); fs=selected[k]; student=students.get(k); revenue=revenues[(str(y),p)]
                values={(r['E'],r['P'],r['C'],r['K']) for r in fs}
                fin=fs[0] if len(values)==1 else None
                historical=p=='重庆' and y<1997
                present=bool(fin and student and student['adjudicated_value'] and revenue['R_adjudicated_yi']) and not historical
                reason='historically_inapplicable' if historical else 'school_organizer_type_timing_funding_revenue_price_scope_pending' if present else 'numeric_field_missing_or_conflicting'
                matched.append(dict(year=y,province=p,stage=stage,S_numeric=student['adjudicated_value'] if student else '',P_thousand_yuan=fin['P'] if fin else '',C_thousand_yuan=fin['C'] if fin else '',E_thousand_yuan=fin['E'] if fin and fin['numeric_status']=='accepted_source_internal_only' else '',finance_numeric_status=fin['numeric_status'] if fin else 'pending_or_unavailable',R_yi_yuan=revenue['R_adjudicated_yi'],finance_source_ids='|'.join(r['source_ids'] for r in fs),finance_evidence_ids='|'.join(r['evidence_id'] for r in fs),student_record_id=student['record_id'] if student else '',R_source_ids=revenue['source_ids'],numeric_fields_present=present,finance_numeric_conflict=len(values)>1,classification_segment='old_classification' if y<=2006 else 'post_2007_definition_needs_annual_bridge',model_eligible=False,reason=reason))
    write('SPCR_numeric_availability.csv',matched)
    coverage=[]
    for y in range(1995,2025):
        for stage in ['primary','junior']:
            rs=[r for r in matched if r['year']==y and r['stage']==stage]
            coverage.append(dict(year=y,stage=stage,applicable=30 if y<1997 else 31,student_numeric=sum(bool(r['S_numeric']) and r['reason']!='historically_inapplicable' for r in rs),all_school_PC_numeric=sum(bool(r['P_thousand_yuan']) for r in rs),SPCR_numeric_present=sum(r['numeric_fields_present'] for r in rs),model_ready=0))
    write('SPCR_annual_coverage.csv',coverage)
    protected=json.loads((BASE/'build_receipt.json').read_text(encoding='utf8'))['protected_hashes']
    checks=dict(original_cells_all_match=all(r['original_coordinates_verified'] for r in result),matching_1860_unique=len(matched)==len({(r['year'],r['province'],r['stage']) for r in matched})==1860,no_model_admission=all(not r['model_eligible'] for r in matched),no_finance_conflicting_numeric_selection=all(not r['finance_numeric_conflict'] for r in matched),inputs_unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items()),protected_outputs_unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items()))
    receipt=dict(source_workbook_sheets=len(cache),original_groups=len(result),numeric_statuses=dict(Counter(r['numeric_status'] for r in result)),all_school_PC_positions=sum(bool(r['P_thousand_yuan']) for r in matched),SPCR_numeric_positions=sum(r['numeric_fields_present'] for r in matched),model_ready=0,checks=checks,input_hashes=hashes)
    (OUT/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8'); assert all(checks.values()), checks
    print(json.dumps({k:v for k,v in receipt.items() if k!='input_hashes'},ensure_ascii=False))

if __name__=='__main__': main()
