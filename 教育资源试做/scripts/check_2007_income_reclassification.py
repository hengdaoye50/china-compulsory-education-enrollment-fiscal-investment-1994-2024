"""Check whole-school totals separately from a renamed source category."""
import json,hashlib,zipfile
import pandas as pd
import build_historical_income as h
OUT=h.ROOT/'教育资源试做/data/经费断点再核查_20261012'
rows=[];sources=[]
def pick(rs,s):
    xs=[r for r in rs if r and (h.clean(r[0])=='总计' if s=='all' else h.stage(r[0])==s)]
    assert len(xs)==1;return xs[0]
def num(r,c):
    x=h.num(h.clean(r[c]));assert x is not None;return x
for year in [2006,2007]:
    path=next((h.ROOT/'中国教育经费统计年鉴').glob(f'*{year+1}*.zip'))
    prefixes=['1-2','1-17','1-13','1-16'] if year==2006 else ['1-2','1-5','1-8','1-11']
    with zipfile.ZipFile(path) as z:
        tables=[]
        for prefix in prefixes:
            xs=[i for i in z.infolist() if h.decoded(i).replace('\\','/').split('/')[-1].startswith(prefix+'_')]
            assert len(xs)==1
            b=z.read(xs[0]);tables.append(h.rows_from(b))
            sources.append(dict(year=year,table=h.decoded(xs[0]),sha256=hashlib.sha256(b).hexdigest()))
        for stage in ['all','primary','junior']:
            f,a,e,p=[pick(t,stage) for t in tables]
            cols=[1,6,6] if year==2006 else [1,1,1]
            parts=[num(r,c) for r,c in zip([a,e,p],cols)]
            diff=sum(parts)-num(f,1)
            assert abs(diff)<=1,(year,stage,diff)
            rows.append(dict(year=year,stage=stage,total_thousand_yuan=num(f,1),department_income=parts[0],enterprise_income=parts[1],private_total_income=parts[2],reconciliation_residual=diff,private_founder_input=num(p,9) if year==2007 else None,private_government_budget=num(p,2) if year==2007 else None,private_education_tax=num(p,6) if year==2007 else None,status='total_sector_identity_confirmed_not_full_crossyear_scope_certification'))
pd.DataFrame(rows).to_csv(OUT/'2006_2007学校总收入与来源分类核对.csv',index=False,encoding='utf-8-sig')
(OUT/'2007回读来源.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf8')
print(pd.DataFrame(rows)[['year','stage','reconciliation_residual','private_total_income','private_founder_input']].to_string(index=False))
