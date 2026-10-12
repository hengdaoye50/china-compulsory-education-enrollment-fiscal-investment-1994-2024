"""Reconcile numerator components without imputing unreported pre-2007 funds."""
import hashlib,json,zipfile
import pandas as pd
import build_historical_income as h
OUT=h.ROOT/'教育资源试做/data/经费断点再核查_20261012'
def pick(rs,s):
    xs=[r for r in rs if r and (h.clean(r[0])=='总计' if s=='all' else h.stage(r[0])==s)]
    assert len(xs)==1
    return xs[0]
def num(r,c):
    x=h.num(h.clean(r[c]));assert x is not None
    return x
records=[];sources=[]
path=next((h.ROOT/'中国教育经费统计年鉴').glob('*2008*.zip'))
with zipfile.ZipFile(path) as z:
    tables=[]
    for prefix in ['1-2','1-5','1-8','1-11']:
        xs=[i for i in z.infolist() if h.decoded(i).replace('\\','/').split('/')[-1].startswith(prefix+'_')]
        assert len(xs)==1
        raw=z.read(xs[0]);tables.append(h.rows_from(raw))
        sources.append(dict(archive=str(path.relative_to(h.ROOT)),table=h.decoded(xs[0]),sha256=hashlib.sha256(raw).hexdigest()))
    for stage in ['all','primary','junior']:
        f,a,e,p=[pick(t,stage) for t in tables]
        budget=num(a,2)+num(e,2)+num(p,2)
        tax=num(a,7)+num(e,6)+num(p,6)
        industry=num(a,12)+num(e,12)
        assert budget==num(f,3) and tax==num(f,8)
        assert industry==num(f,12) and num(e,9)==num(f,11)
        fiscal=budget+tax+industry+num(e,9)
        assert fiscal==num(f,2)
        old_components=num(a,2)+num(a,7)+num(a,12)+num(e,9)+num(e,12)
        additional=num(e,2)+num(e,6)+num(p,2)+num(p,6)
        assert fiscal-old_components==additional
        records.append(dict(year=2007,stage=stage,total_yi=num(f,1)/100000,published_fiscal_yi=fiscal/100000,old_components_fiscal_yi=old_components/100000,enterprise_budget_yi=num(e,2)/100000,enterprise_tax_yi=num(e,6)/100000,private_budget_yi=num(p,2)/100000,private_tax_yi=num(p,6)/100000,additional_identified_yi=additional/100000,additional_pct_of_fiscal=100*additional/fiscal,published_share_pct=100*fiscal/num(f,1),old_components_share_pct=100*old_components/num(f,1),share_difference_pp=100*additional/num(f,1),private_industry_yi=num(p,12)/100000,fiscal_residual_thousand_yuan=fiscal-num(f,2),status='component_identity_confirmed_pre2007_sector_public_funds_unobserved'))
df=pd.DataFrame(records)
df.to_csv(OUT/'2007财政性分子逐项核对.csv',index=False,encoding='utf-8-sig')
(OUT/'2007财政性分子来源.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf8')
print(df.to_string(index=False))
