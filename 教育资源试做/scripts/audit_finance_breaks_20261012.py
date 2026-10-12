"""Re-read source components and test an enterprise-definition bridge separately."""
import hashlib,json,zipfile
from pathlib import Path
import pandas as pd
import build_historical_income as h
ROOT=h.ROOT
OUT=ROOT/'教育资源试做/data/经费断点再核查_20261012'
OUT.mkdir(exist_ok=True)
oldpath=ROOT/'教育资源试做/data/早期财政重建_20261011/national_fiscal_1994_2024_report_final.csv'
oldhash=hashlib.sha256(oldpath.read_bytes()).hexdigest()
old=pd.read_csv(oldpath)
evidence=json.loads((oldpath.parent/'source_evidence.json').read_text(encoding='utf8'))
records=[];checks=[];sources=[]
def row(rs,stage):
    xs=[r for r in rs if r and (h.clean(r[0])=='总计' if stage=='all' else h.stage(r[0])==stage)]
    assert len(xs)==1,(stage,len(xs))
    return xs[0]
def n(r,c):
    v=h.num(h.clean(r[c]));assert v is not None,(r[0],c,r[c]);return v
for year in range(1998,2007):
    path=next((ROOT/'中国教育经费统计年鉴').glob(f'*{year+1}*.zip'))
    with zipfile.ZipFile(path) as z:
        tables={}
        full_prefix='1-1' if year<=2004 else '1-2'
        for prefix in [full_prefix,'1-17','1-13','1-16']:
            xs=[i for i in z.infolist() if h.decoded(i).replace('\\','/').split('/')[-1].startswith(prefix+'_')]
            assert len(xs)==1
            item=xs[0];raw=z.read(item);digest=hashlib.sha256(raw).hexdigest()
            ev=[e for e in evidence if e['archive']==str(path.relative_to(ROOT)) and e['table']==h.decoded(item)]
            if year<=2004:
                assert len(ev)==1 and digest==ev[0]['sha256']
            checks.append(dict(check=f'{year}_{prefix}_original_file_hash',passed=True))
            tables[prefix]=h.rows_from(raw)
            sources.append(dict(year=year,archive=str(path.relative_to(ROOT)),table=h.decoded(item),sha256=digest))
        for stage in ['all','primary','junior']:
            a,e,p=[row(tables[k],stage) for k in ['1-17','1-13','1-16']]
            total=n(a,1)+n(e,6)+n(p,6)
            base=sum(n(a,c) for c in [2,6,12,16])
            reported=base+(n(e,6) if year<2002 else n(e,7)+n(e,8))
            adjusted=base+n(e,7)+n(e,8)
            excluded=n(e,6)-n(e,7)-n(e,8)
            assert abs(excluded-n(e,9)-n(e,10))<=2
            if stage=='all':
                ar=row(tables[full_prefix],stage)
                if year<=2004:
                    fr=next(r for r in tables[full_prefix] if r and h.clean(r[0]).startswith('一、国家财政性'))
                    fiscal_target=n(fr,1)
                else:
                    fiscal_target=n(ar,2)
                assert abs(reported-fiscal_target)<=1 and abs(total-n(ar,1))<=1
            else:
                r=old[(old.year==year)&(old.stage==stage)].iloc[0]
                assert reported==r.fiscal_thousand_yuan and total==r.total_thousand_yuan
            checks.append(dict(check=f'{year}_{stage}_published_reconciliation_and_enterprise_sum',passed=True))
            records.append(dict(year=year,stage=stage,reported_fiscal_yi=reported/100000,enterprise_definition_adjusted_fiscal_yi=adjusted/100000,adjustment_yi=(adjusted-reported)/100000,published_share_pct=100*reported/total,adjusted_share_pct=100*adjusted/total,total_yi=total/100000,enterprise_total=n(e,6),enterprise_appropriation=n(e,7),enterprise_industry=n(e,8),enterprise_fees=n(e,9),enterprise_other=n(e,10),status='component_bridge_candidate_not_full_scope_certification'))
pd.DataFrame(records).to_csv(OUT/'企业来源统一口径候选.csv',index=False,encoding='utf-8-sig')
assert hashlib.sha256(oldpath.read_bytes()).hexdigest()==oldhash
checks.append(dict(check='original_final_series_unchanged',passed=True))
pd.DataFrame(checks).to_csv(OUT/'原表回读与候选桥接检查.csv',index=False,encoding='utf-8-sig')
(OUT/'来源与处理记录.json').write_text(json.dumps(dict(sources=sources,checks=len(checks),original_sha256=oldhash,notes='Only enterprise definition is harmonized; 1998 accounting and 2007 private-source scope remain separate questions. No old figures or reports replaced.'),ensure_ascii=False,indent=2),encoding='utf8')
print(pd.DataFrame(records).query("year==2001 and stage!='all'")[['stage','reported_fiscal_yi','enterprise_definition_adjusted_fiscal_yi','adjustment_yi','published_share_pct','adjusted_share_pct']].to_string(index=False))
print('checks',len(checks),'rows',len(records))
