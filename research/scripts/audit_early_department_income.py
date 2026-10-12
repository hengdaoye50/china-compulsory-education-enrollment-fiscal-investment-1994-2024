"""Check a secondary historical lead against original department-income tables."""
import json,hashlib,zipfile
import pandas as pd
import build_historical_income as h
OUT=h.ROOT/'research/data/经费断点再核查_20261012'
# Wang Rong draft, table 15, PDF pages 15-16. Excludes enterprise/private schools.
quoted={1995:(60703782,39302023),1996:(72603440,47933640),1997:(78936047,51719939),1998:(85973543,47243161),1999:(93418000,51144559),2000:(101764254,56995819),2001:(120278295,68116650),2002:(137169706,79385004)}
records=[];sources=[]
for year in range(1995,2003):
    path=next((h.ROOT/'中国教育经费统计年鉴').glob(f'*{year+1}*.zip'))
    prefix='1-27' if year<1998 else '1-17'
    with zipfile.ZipFile(path) as z:
        xs=[i for i in z.infolist() if h.decoded(i).replace('\\','/').split('/')[-1].startswith(prefix+'_')]
        assert len(xs)==1
        raw=z.read(xs[0]);rs=h.rows_from(raw)
        sources.append(dict(year=year,archive=str(path.relative_to(h.ROOT)),table=h.decoded(xs[0]),sha256=hashlib.sha256(raw).hexdigest()))
        for j,stage in enumerate(['primary','junior']):
            matches=[r for r in rs if r and h.stage(r[0])==stage]
            assert len(matches)==1
            r=matches[0]
            def n(c):
                val=h.num(h.clean(r[c]));assert val is not None;return val
            total=n(1)
            assert total==quoted[year][j]
            budget=n(2)+(n(16) if year>=1998 else 0)
            fiscal=sum(n(c) for c in ([2,5,8,9] if year<1998 else [2,6,12,16]))
            sumcols=[2,5,8,9,10,11,13] if year<1998 else [2,6,10,12,13,15,16]
            assert abs(total-sum(n(c) for c in sumcols))<=1
            records.append(dict(year=year,stage=stage,department_total_thousand_yuan=total,department_budget_thousand_yuan=budget,department_fiscal_components_thousand_yuan=fiscal,budget_share_pct=100*budget/total,paper_total_residual=total-quoted[year][j],source_status='original_table_confirmed',scope='education_and_other_department_schools_excluding_enterprise_and_private',cross_1998_comparability='accounting_change_not_resolved'))
pd.DataFrame(records).to_csv(OUT/'1995_2002部门学校收入原表与论文核验.csv',index=False,encoding='utf-8-sig')
# A draft is a retrieval lead, not an approved replacement for original 1994 data.
pd.DataFrame([dict(year=1994,stage=s,department_total_thousand_yuan=t,budget_share_pct=b,fees_share_pct=f,source_status='secondary_draft_retrieval_lead_not_formal_series') for s,t,b,f in [('primary',48304624,60.20,8.18),('junior',29960693,59.28,8.10)]]).to_csv(OUT/'1994部门学校收入检索线索.csv',index=False,encoding='utf-8-sig')
(OUT/'早期部门收入核验来源.json').write_text(json.dumps(dict(original_tables=sources,lead_url='https://iee.gse.pku.edu.cn/__local/F/17/07/EA022D36A72365971CEE0D45518_C9BF9A39_47837.pdf',lead_title='王蓉：教育水平的差异与公共教育资源分配的不平等',lead_table='表15，PDF第15—16页',lead_warning='初稿，请勿引用；仅作原始数据检索线索。1994年尚无本地原表。',checks='16 income totals agree exactly; 16 component sums agree within 1 thousand yuan'),ensure_ascii=False,indent=2),encoding='utf8')
print('16 original income totals confirmed; 1994 leads retained separately.')
