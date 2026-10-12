"""Reconstruct historical school finance with explicit accounting regimes; no raw edits."""
from pathlib import Path
import sys,json,zipfile,hashlib
import pandas as pd
import build_historical_income as h

OUT=h.ROOT/'research/data/早期财政重建_20261011'
OUT.mkdir(parents=True,exist_ok=True)
evidence=[];checks=[];records=[]

def read(z,prefix):
    candidates=[i for i in z.infolist() if h.decoded(i).replace('\\','/').split('/')[-1].startswith(prefix+'_')]
    assert len(candidates)==1,(prefix,len(candidates))
    i=candidates[0];b=z.read(i);rows=h.rows_from(b)
    evidence.append(dict(archive=str(Path(z.filename).relative_to(h.ROOT)),table=h.decoded(i),sha256=hashlib.sha256(b).hexdigest(),rows=rows))
    return rows

def row(rs,s):
    matches=[(k,r) for k,r in enumerate(rs) if r and (h.clean(r[0])=='总计' if s=='all' else h.stage(r[0])==s) and (s!='all' or (h.num(h.clean(r[1])) or 0)>1000)]
    assert len(matches)==1,(s,len(matches))
    return matches[0][1]

def n(r,c):
    # OCR exports sometimes embed spaces inside integer digits.
    v=h.num(h.clean(r[c]));assert v is not None,(r[0],c,r[c]);return v

original=pd.read_csv(h.OUT/'national_income_original_series.csv')
national={}
for y in range(1995,2007):
    z=zipfile.ZipFile(next((h.ROOT/'中国教育经费统计年鉴').glob(f'*{y+1}*.zip')))
    agg=read(z,'1-1')
    ar=row(agg,'all');fr=next(r for r in agg if r and h.clean(r[0]).startswith('一、国家财政性'))
    national[y]={'total':n(ar,1),'fiscal':n(fr,1)}
    if y<=1997:
        budget=read(z,'1-3');tax=read(z,'1-8');ent=read(z,'1-11');ind=read(z,'1-14');priv=read(z,'1-17');non=read(z,'1-18')
        for s in ['all','primary','junior']:
            b,t,e,d,p,o=[row(rs,s) for rs in [budget,tax,ent,ind,priv,non]]
            # The source's bank expenditure column, not actual expenditure including
            # offsets financed by non-budget sources, matches national budget totals.
            B=n(b,2)+n(b,16)+n(b,17)
            F=B+n(t,1)+n(e,6)+n(d,1)+n(d,7)
            T=F+n(p,6)+n(o,1)+n(o,7)+n(o,13)
            if s=='all':
                assert F==national[y]['fiscal'] and T==national[y]['total'],(y,F,T,national[y])
                checks.append(dict(year=y,test='national_expenditure_components',fiscal_residual=F-national[y]['fiscal'],total_residual=T-national[y]['total']))
            else:
                records.append(dict(year=y,stage=s,fiscal_thousand_yuan=F,total_thousand_yuan=T,budget_thousand_yuan=B,accounting='expenditure',status='reconstructed_observed_components',formula='budget_bank + budget_capital + budget_special + tax + enterprise_expenditure + industry + other_fiscal',source_volume=y+1))
    elif y<=2004:
        dept=read(z,'1-17');ent=read(z,'1-13');priv=read(z,'1-16')
        # National aggregate establishes whether enterprise total income or only
        # enterprise appropriation and industry revenue enters the fiscal measure.
        ar=row(dept,'all');er=row(ent,'all');base=sum(n(ar,c) for c in [2,6,12,16])
        alternatives={'enterprise_total':n(er,6),'enterprise_appropriation_plus_industry':n(er,7)+n(er,8)}
        matches=[k for k,v in alternatives.items() if abs(base+v-national[y]['fiscal'])<=1]
        assert len(matches)==1,(y,base,alternatives,national[y])
        rule=matches[0]
        for s in ['all','primary','junior']:
            a,e,p=[row(rs,s) for rs in [dept,ent,priv]]
            E=n(e,6) if rule=='enterprise_total' else n(e,7)+n(e,8)
            B=n(a,2)+n(a,16);F=B+n(a,6)+n(a,12)+E;T=n(a,1)+n(e,6)+n(p,6)
            if s=='all':
                assert abs(F-national[y]['fiscal'])<=1 and abs(T-national[y]['total'])<=1,(y,F,T,national[y])
                checks.append(dict(year=y,test='national_income_components',enterprise_rule=rule,fiscal_residual=F-national[y]['fiscal'],total_residual=T-national[y]['total']))
            else:
                records.append(dict(year=y,stage=s,fiscal_thousand_yuan=F,total_thousand_yuan=T,budget_thousand_yuan=B,accounting='income',status='reconstructed_observed_components',formula='department_budget + department_capital + department_tax + department_industry + '+rule,source_volume=y+1))
    else:
        dept=read(z,'1-17');ent=read(z,'1-13');priv=read(z,'1-16');full=read(z,'1-2')
        for s in ['all','primary','junior']:
            a,e,p,f=[row(rs,s) for rs in [dept,ent,priv,full]]
            F=sum(n(a,c) for c in [2,6,12,16])+n(e,7)+n(e,8)
            T=n(a,1)+n(e,6)+n(p,6)
            assert abs(F-n(f,2))<=1 and abs(T-n(f,1))<=1,(y,s,F,T,f)
            checks.append(dict(year=y,stage=s,test='bridge_to_published_stage_fiscal',fiscal_residual=F-n(f,2),total_residual=T-n(f,1)))
    z.close()

# Published 2001 NBS yearbook retains an extra decimal in 1994 totals (万元).
N94={'fiscal':117473956.,'total':148878126.}
early=pd.DataFrame(records)
backtests=[]
for s in ['primary','junior']:
    r=early[(early.stage==s)&(early.year<=1997)].set_index('year')
    estimate=dict(year=1994,stage=s,accounting='expenditure',status='model_backcast',source_volume=0,formula='1995_stage_share_of_national * official_1994_national',budget_thousand_yuan=None)
    for metric in ['fiscal','total']:
        shares={y:r.loc[y,metric+'_thousand_yuan']/national[y][metric] for y in [1995,1996,1997]}
        estimate[metric+'_thousand_yuan']=shares[1995]*N94[metric]
        estimate[metric+'_scenario_low_thousand_yuan']=min(shares.values())*N94[metric]
        estimate[metric+'_scenario_high_thousand_yuan']=max(shares.values())*N94[metric]
        for target,anchor in [(1995,1996),(1996,1997)]:
            pred=shares[anchor]*national[target][metric];actual=r.loc[target,metric+'_thousand_yuan']
            backtests.append(dict(stage=s,metric=metric,target_year=target,anchor_year=anchor,prediction=pred,actual=actual,error_pct=100*(pred/actual-1)))
    estimate['share_scenario_low_pct']=100*estimate['fiscal_scenario_low_thousand_yuan']/estimate['total_scenario_high_thousand_yuan']
    estimate['share_scenario_high_pct']=100*estimate['fiscal_scenario_high_thousand_yuan']/estimate['total_scenario_low_thousand_yuan']
    records.append(estimate)

for r in original[original.year>=2005].to_dict('records'):
    records.append(dict(year=int(r['year']),stage=r['stage'],fiscal_thousand_yuan=r['national_fiscal_thousand_yuan'],total_thousand_yuan=r['income_total_thousand_yuan'],budget_thousand_yuan=r['budget_thousand_yuan'],accounting='income',status='published_cross_source_unit_confirmed' if r['year']==2006 else 'published',formula='original_national_stage_income_table',source_volume=int(r['year'])+1))
result=pd.DataFrame(records).sort_values(['stage','year'])
result['fiscal_yi']=result.fiscal_thousand_yuan/100000
result['total_yi']=result.total_thousand_yuan/100000
result['fiscal_share_pct']=100*result.fiscal_thousand_yuan/result.total_thousand_yuan
assert len(result)==62 and not result.duplicated(['year','stage']).any()
assert result.fiscal_share_pct.between(0,100).all()
result.to_csv(OUT/'national_fiscal_1994_2024_segmented.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(backtests).to_csv(OUT/'backcast_validation.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(checks).to_csv(OUT/'accounting_reconciliation.csv',index=False,encoding='utf-8-sig')
(OUT/'source_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
unit={'year':2006,'unit_original':'unit_pending','unit_resolved':'千元','status':'cross_source_confirmed','nbs_url':'https://www.stats.gov.cn/sj/ndsj/2012/html/U2039C.HTM','local_total_raw':981530865,'nbs_total_wan':98153087,'local_fiscal_raw':634836475,'nbs_fiscal_wan':63483648,'total_residual_thousand':-5,'fiscal_residual_thousand':-5,'budget_raw':579561380,'nbs_budget_wan':57956138,'budget_residual_thousand':0,'note':'万元×10=千元；全国两项相差5千元，在整万元四舍五入容差内。'}
(OUT/'unit_resolution_2006.json').write_text(json.dumps(unit,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'build_receipt.json').write_text(json.dumps({'rows':62,'national_reconciliation_checks':checks,'1994_national_anchors':N94,'1994_source':'https://www.stats.gov.cn/sj/ndsj/2001c/t2036c.htm','regime_breaks':[1998,2002,2007],'original_inputs_unchanged':True,'uncertainty':'1994 envelopes are allocation scenarios, not confidence intervals; only two adjacent-year backtests per stage and metric'},ensure_ascii=False,indent=2),encoding='utf8')
print(result[result.year<=2006][['year','stage','fiscal_yi','fiscal_share_pct','accounting','status']].to_string(index=False))
print(pd.DataFrame(backtests).to_string(index=False))
