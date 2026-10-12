"""Audit 1994 external anchors and conditional conversions, preserving the main series."""
from pathlib import Path
import json,sys,hashlib
import pandas as pd
import build_historical_income as h

OUT=h.ROOT/'教育资源试做/data/早期财政重建_20261011'
E=json.loads((OUT/'source_evidence.json').read_text(encoding='utf8'))
MAIN=OUT/'national_fiscal_1994_2024_segmented.csv'
before=hashlib.sha256(MAIN.read_bytes()).hexdigest()
KEYS=['budget','other_fiscal','private','donation','tuition','other_nonfiscal']
N94=dict(zip(KEYS,[88397947.,29076009.,1077952.,9744871.,14692281.,5889066.]))
assert sum(N94.values())==148878126
assert N94['budget']+N94['other_fiscal']==117473956

def read(year,prefix,stage):
    a=next(a for a in E if str(year+1) in a['archive'] and a['table'].replace('\\','/').split('/')[-1].startswith(prefix+'_'))
    matches=[r for r in a['rows'] if r and (h.clean(r[0])=='总计' if stage=='all' else ('特殊教育学校' in h.clean(r[0]) if stage=='special' else h.stage(r[0])==stage))]
    assert len(matches)==1,(year,prefix,stage)
    return matches[0]

def n(row,c):
    value=h.num(h.clean(row[c]));assert value is not None
    return value

def components(year,stage):
    b,t,e,d,p,o=[read(year,k,stage) for k in ['1-3','1-8','1-11','1-14','1-17','1-18']]
    budget=sum(n(b,c) for c in [2,16,17])
    return dict(zip(KEYS,[budget,n(t,1)+n(e,6)+n(d,1)+n(d,7),n(p,6),n(o,1),n(o,7),n(o,13)]))

def special_budget(year):
    r=read(year,'1-3','special')
    return sum(n(r,c) for c in [2,16,17])

N={y:components(y,'all') for y in [1995,1996,1997]}
S={(y,s):components(y,s) for y in N for s in ['primary','junior']}
rows=[];parts=[];tests=[]
for anchor in N:
    for stage in ['primary','junior']:
        estimated={k:N94[k]*S[anchor,stage][k]/N[anchor][k] for k in KEYS}
        for k in KEYS:
            parts.append(dict(stage=stage,anchor_year=anchor,component=k,national_1994_thousand_yuan=N94[k],stage_anchor_thousand_yuan=S[anchor,stage][k],national_anchor_thousand_yuan=N[anchor][k],stage_share=S[anchor,stage][k]/N[anchor][k],estimated_1994_thousand_yuan=estimated[k],status='conditional_component_allocation'))
        for model in ['six_source_allocation','compulsory_budget_constraint']:
            values=estimated.copy()
            if model=='compulsory_budget_constraint':
                # 53.41% is a rounded historical report statistic, not a stage share.
                obligation_budget=N94['budget']*.5341
                obligation_anchor=sum(S[anchor,s]['budget'] for s in ['primary','junior'])+special_budget(anchor)
                values['budget']=obligation_budget*S[anchor,stage]['budget']/obligation_anchor
            fiscal=values['budget']+values['other_fiscal'];total=sum(values.values())
            rows.append(dict(year=1994,stage=stage,model=model,anchor_year=anchor,budget_yi=values['budget']/1e5,fiscal_yi=fiscal/1e5,total_yi=total/1e5,fiscal_share_pct=100*fiscal/total,status='conditional_estimate_not_observed'))

for target,anchor in [(1995,1996),(1996,1997)]:
    for stage in ['primary','junior']:
        pred={k:N[target][k]*S[anchor,stage][k]/N[anchor][k] for k in KEYS}
        for metric,cols in [('fiscal',KEYS[:2]),('total',KEYS)]:
            actual=sum(S[target,stage][k] for k in cols);prediction=sum(pred[k] for k in cols)
            tests.append(dict(stage=stage,target_year=target,anchor_year=anchor,metric=metric,prediction_thousand_yuan=prediction,actual_thousand_yuan=actual,error_pct=100*(prediction/actual-1),model='six_source_allocation'))

result=pd.DataFrame(rows)
result.to_csv(OUT/'1994_conversion_scenarios.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(parts).to_csv(OUT/'1994_conversion_components.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(tests).to_csv(OUT/'1994_component_backtests.csv',index=False,encoding='utf-8-sig')
sources=[
 dict(id='NBS2001',title='中国统计年鉴2001，20-36表',url='https://www.stats.gov.cn/sj/ndsj/2001c/t2036c.htm',locator='1994行；单位万元',facts=dict(total_wan=14887812.6,fiscal_wan=11747395.6,budget_wan=8839794.7,private_wan=107795.2,donation_wan=974487.1,tuition_wan=1469228.1,other_wan=588906.6),use='1994年全国来源锚点，非分学段观察值'),
 dict(id='announcement1994',title='1994年全国教育经费执行情况统计公告',url='https://www.edu.cn/edu/tjsj/zhsj/jiao_yu_jing_fei/200603/t20060323_11713.shtml',locator='第二部分第2项；第3项',facts=dict(primary_budget_recurrent_per_student_yuan=236.06,junior_budget_recurrent_per_student_yuan=450.37,primary_budget_public_per_student_yuan=17.73),use='当年生均预算内事业费及公用费，不能等同于财政性经费；平均人数和举办者范围需匹配'),
 dict(id='annual_report1996',title='中国教育经费投入的“八五”回顾与“九五”展望',url='https://www.cnsaes.org.cn/homepage/Upfile/2010612/2010061208642783.pdf',locator='PDF第5页表1-4，印刷页码5；脚注注明1996年撰写的年度报告部分内容',facts=dict(compulsory_budget_share_1994_pct=53.41,compulsory_budget_share_1995_pct=53.24),use='义务教育包括小学、初中及特殊教育；只约束预算内部分；比例经舍入'),
 dict(id='children_whitepaper',title='中国的儿童状况',url='https://www.fmprc.gov.cn/ziliao_674904/zt_674979/ywzt_675099/wzzt_675579/2296_675789/200207/t20020705_7961975.shtml',locator='儿童教育部分',facts=dict(primary_1994_total_yi=594,ordinary_middle_1994_total_yi=435,primary_recurrent_public_per_student_yuan=89.47),use='确认官方文本确实载有594亿元；未分列财政性来源，普通中学包括高中，不能转为初中金额'),
 dict(id='migration_report_lead',title='李人庆：中国城市化过程中流动人口子女义务教育问题的对策研究报告，2003年3月；存档页面2006年10月30日',url='https://nodebe4.github.io/opinion/2006-10-30/中国城市化过程中流动人口子女义务教育问题的对策研究报告/',original_url='https://unirule.cloud/index.php?c=article&id=3019',facts=dict(national_1994_total_wan_as_transcribed=14166398,compulsory_1994_total_wan_as_transcribed=7826531.7),use='仅保留检索线索，不入换算：原站本次不可达；全国总量与官方14887812.6万元差异且网页表中多处小数点缺失')
]
(OUT/'1994_external_source_ledger.json').write_text(json.dumps(dict(checked_on='2026-10-11',sources=sources,national_1994_components_thousand_yuan=N94,main_series_unchanged=True,assumption='Each stage share within each funding source is borrowed from 1995, 1996, or 1997. Contemporaneous national composition is observed, stage allocation is estimated.'),ensure_ascii=False,indent=2),encoding='utf8')
assert hashlib.sha256(MAIN.read_bytes()).hexdigest()==before
print(result[result.anchor_year==1995].to_string(index=False))
print(pd.DataFrame(tests).to_string(index=False))
print('Compulsory budget 1994 (yi):',N94['budget']*.5341/1e5)
print('1995 budget textbook share reconstructed:',100*(sum(S[1995,s]['budget'] for s in ['primary','junior'])+special_budget(1995))/N[1995]['budget'])
print('Main series unchanged:',before)
