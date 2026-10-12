"""Read original workbook cells; retain accounting and fiscal scope limitations."""
import os,sys,json,hashlib,re,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'教育资源试做/data'
OUT=DATA/'支出细项与补助拓展_20261011';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'教育资源试做/.tmp/figure_deps'))
import pandas as pd
import openpyxl
from inspect_bridge_evidence import CAT,getbytes,sheets,norm
PROVS='北京 天津 河北 山西 内蒙古 辽宁 吉林 黑龙江 上海 江苏 浙江 安徽 福建 江西 山东 河南 湖北 湖南 广东 广西 海南 重庆 四川 贵州 云南 西藏 陕西 甘肃 青海 宁夏 新疆'.split()
def save(rows,name):pd.DataFrame(rows).to_csv(OUT/name,index=False,encoding='utf-8-sig')
def num(v):
    t=re.sub(r'[,，\s]','',str(v))
    return float(t) if re.fullmatch(r'-?\d+(\.\d+)?',t) else None
def main():
    availability=pd.read_csv(DATA/'经费共同样本核查_20261010/SPCR_numeric_availability.csv').fillna('')
    evidence={x['evidence_id']:x for x in json.loads((DATA/'经费共同样本核查_20261010/PC_original_evidence.json').read_text(encoding='utf8'))}
    registry=pd.read_csv(DATA/'长期财政数据建设_20261010/source_registry.csv').set_index('source_id').to_dict('index')
    cache={};levels=[];checks=[];sources={}
    for a in availability[availability.year.between(2007,2023)&availability.province.isin(PROVS)].to_dict('records'):
        ids=a['finance_evidence_ids'].split('|');candidates=[]
        for eid in ids:
            e=evidence[eid];s=registry[e['cells'][0]['source_id']];key=(s['archive'],s['table'],s['sheet'])
            if key not in cache:
                b=(ROOT/s['table']).read_bytes() if s['source_quality']=='previously_extracted_user_excel' else getbytes(s)
                h=hashlib.sha256(b).hexdigest();assert h==e['source_sha256']==s['table_sha256']
                if s['source_quality']=='previously_extracted_user_excel':
                    w=openpyxl.load_workbook(io.BytesIO(b),read_only=True,data_only=True);rows=list(w[s['sheet']].iter_rows(values_only=True));w.close()
                else:rows=dict(sheets(s))[s['sheet']]
                cache[key]=rows;sources['|'.join(key)]=h
            rows=cache[key];values={}
            for total,metrics in [('P',['W','A']),('C',['G','X'])]:
                sub=e['PC_component_checks'][total];assert sub['passed'] and sub['headers_verified']
                for m,c in zip(metrics,sub['cells']):
                    v=num(rows[c['row']-1][c['column']-1]);assert v==float(c['numeric'])
                    # Recheck label in the header rows above the selected numeric row.
                    header=''.join(norm(r[c['column']-1]) for r in rows[:c['row']-1] if len(r)>=c['column'])
                    assert norm(c['label']).replace('|','') in header,(key,m,header)
                    values[m]=v;checks.append(dict(year=a['year'],province=a['province'],stage=a['stage'],metric=m,value=v,unit='千元',row=c['row'],column=c['column'],label=c['label'],evidence_id=eid,archive=s['archive'],table=s['table'],sheet=s['sheet'],sha256=e['source_sha256'],exact_reread=True))
            assert abs(values['W']+values['A']-float(a['P_thousand_yuan']))<=1.5
            assert abs(values['G']+values['X']-float(a['C_thousand_yuan']))<=1.5
            candidates.append(values)
        assert candidates and all(x==candidates[0] for x in candidates)
        levels.append(dict(year=a['year'],province=a['province'],stage=a['stage'],**candidates[0],P=float(a['P_thousand_yuan']),C=float(a['C_thousand_yuan']),evidence_ids=a['finance_evidence_ids'],scope_status='all_affiliations_all_source_numeric_verified_cross_year_scope_pending'))
    save(levels,'component_levels.csv');save(checks,'component_original_rereads.csv')
    prior=pd.read_csv(DATA/'财政收入补核_20261010/R_province_year_numeric_panel_with_summaries.csv').set_index(['year','province'])
    candidates=[];accepted=[];rejections=[]
    for s in CAT:
        y=int(s['volume_year'])-1;name=Path(s['table']).name
        if s['family']!='中国财政年鉴' or not 2007<=y<=2023 or not name.endswith(('.xlsx','.xls')):continue
        if not ('收支' in name and ('总表' in name or '总统计' in name)) or any(t in name for t in ['基金','社会','资本','续表','本级','(支出)','（支出）']):continue
        ps=[p for p in PROVS if p in name];
        if len(ps)!=1:continue
        p=ps[0];expected=prior.loc[(y,p),'R_adjudicated_yi']
        if pd.isna(expected):
            rejections.append(dict(year=y,province=p,table=s['table'],reason='prior_own_revenue_not_numeric_verified'));continue
        b=getbytes(s);h=hashlib.sha256(b).hexdigest()
        for sn,rows in sheets(s):
            ownrows=[i for i,r in enumerate(rows) if r and norm(r[0]).startswith('本年收入合计')]
            for i in ownrows:
                # Multiple region tables may be packed in one sheet. Unit/title must be local to this block.
                unitidx=[j for j in range(len(rows)) if '单位' in '|'.join(norm(v) for v in rows[j])]
                if not unitidx:continue
                before=[j for j in unitidx if j<=i];u=before[-1] if before else unitidx[0];unittext='|'.join(norm(v) for v in rows[u]);factor=1 if '亿元' in unittext else .0001 if '万元' in unittext else None
                if factor is None:continue
                start=u if before else 0;headers=rows[start:min(i,start+12)];actual=[j for r in headers for j,v in enumerate(r) if '决算数' in norm(v)]
                actual=[j for j in actual if j<len(rows[i]) and num(rows[i][j]) is not None]
                # Income precedes expenditure; actual column must be explicitly labelled.
                if not actual:continue
                col=min(actual);R=num(rows[i][col])*factor
                stop=next((j for j in unitidx if j>i),len(rows))
                central=[j for j in range(i+1,min(len(rows),i+18,stop)) if rows[j] and norm(rows[j][0]).startswith('中央补助收入')]
                title='|'.join(norm(v) for r in (rows[max(0,u-4):u+1] if before else rows[:4]) for v in r if v is not None)
                for j in central:
                    raw=rows[j][col] if col<len(rows[j]) else None;B=num(raw)
                    rec=dict(year=y,province=p,R=R,B=None if B is None else B*factor,prior_R=float(expected),own_difference=R-float(expected),archive=s['archive'],table=s['table'],sheet=sn,sha256=h,unit_text=unittext,unit_to_yi=factor,own_row=i+1,subsidy_row=j+1,actual_column=col+1,title_context=title,raw_own=rows[i][col],raw_subsidy=raw,scope_status='province_budget_candidate_plan_listed_and_net_settlement_pending')
                    rec['accepted_numeric']=abs(R-float(expected))<=max(.015,abs(float(expected))*1e-6) and B is not None and B>0
                    candidates.append(rec)
                    if rec['accepted_numeric']:accepted.append(rec)
                    else:rejections.append(dict(year=y,province=p,table=s['table'],reason='own_revenue_mismatch_or_subsidy_blank',own_R=R,prior_R=expected))
    grouped={}
    for a in accepted:grouped.setdefault((a['year'],a['province']),[]).append(a)
    final=[]
    for k,v in grouped.items():
        if max(a['B'] for a in v)-min(a['B'] for a in v)>.015:
            rejections.append(dict(year=k[0],province=k[1],reason='conflicting_subsidy_candidates'));continue
        final.append(dict(v[0],duplicate_candidates=len(v)))
    save(candidates,'subsidy_original_candidates.csv');save(final,'subsidy_levels_numeric.csv');save(rejections,'subsidy_exclusions.csv')
    receipt=dict(component_rows=len(levels),component_cells=len(checks),component_source_hashes=sources,subsidy_candidates=len(candidates),subsidy_accepted=len(final),subsidy_year_counts=pd.DataFrame(final).groupby('year').size().to_dict(),scope_approved=False)
    (OUT/'extraction_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in receipt.items() if k!='component_source_hashes'},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
