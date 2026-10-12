"""Descriptive spell summaries and policy evidence locators; no causal attribution."""
import csv,json,hashlib
from decimal import Decimal as D
from parse import ROOT,save_csv,read
import pdfplumber

DATA=ROOT/'data'
def rows(name):return list(csv.DictReader((DATA/name).open(encoding='utf-8-sig',newline='')))
protected=json.loads((DATA/'province_finance_next_protected_baseline.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
spells=[r for r in rows('persistent_decline_spells.csv') if int(r['consecutive_decline_changes'])>=2]
metrics=['teachers_cumulative_pct','classes_cumulative_pct','spending_total_thousand_yuan_cumulative_pct','spending_cpi_adjusted_2017_thousand_yuan_cumulative_pct']
summary=[]
for stage in ['primary','junior']:
 subset=[r for r in spells if r['stage']==stage]
 for metric in metrics:
  summary.append(dict(stage=stage,metric=metric,observed_spells=len(subset),province_stages=len({r['province'] for r in subset}),increase=sum(D(r[metric])>0 for r in subset),decrease=sum(D(r[metric])<0 for r in subset),unchanged=sum(D(r[metric])==0 for r in subset),limit='descriptive spell counts; spells may repeat within province-stage'))
save_csv(DATA/'persistent_decline_direction_summary.csv',summary)
fund=rows('persistent_decline_fund_sensitivity.csv'); fs=[]
for stage in ['primary','junior']:
 for scope in ['all_affiliations','local_affiliation']:
  for f in ['all_source','fiscal_subsidy','general_budget']:
   subset=[r for r in fund if r['stage']==stage and r['affiliation_scope']==scope and r['fund']==f]
   fs.append(dict(stage=stage,affiliation_scope=scope,fund=f,spells=len(subset),total_increase=sum(D(r['cpi_adjusted_total_cumulative_pct'])>0 for r in subset),career_increase=sum(D(r['cpi_adjusted_career_cumulative_pct'])>0 for r in subset)))
save_csv(DATA/'persistent_decline_fund_summary.csv',fs)
manifest=json.loads((ROOT/'adjustment_policy_sources.json').read_text(encoding='utf-8'))+json.loads((ROOT/'adjustment_policy_attachment_sources.json').read_text(encoding='utf-8'))
sources={r['key']:r for r in manifest}
for r in manifest:
 assert r['status']=='downloaded'
 assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256']
specs=[
 ('2018_efficiency','国务院办公厅关于进一步调整优化结构提高教育经费使用效益的意见','国办发〔2018〕82号','2018-08-17','规范性文件','优先保障，加大投入。','教育总量及生均投入保障要求与教师待遇保障并存，不能将支出增幅直接等同效率损失。','不是各省各学段实际支出必然增长的预测，也不直接要求CPI调整后金额增长。'),
 ('2018_efficiency','国务院办公厅关于进一步调整优化结构提高教育经费使用效益的意见','国办发〔2018〕82号','2018-08-17','规范性文件','（七）不断提高教师队伍建设保障水平','教师工资保障、待遇联动可能影响人员支出变化。','个人支出不等于教师工资；没有本省工资与执行证据，不能认定其贡献。'),
 ('2015_guarantee','国务院关于进一步完善城乡义务教育经费保障机制的通知','国发〔2015〕67号','2015-11-25','规范性文件','（一）从2016年春季学期开始','小规模学校保底及寄宿、特殊教育补助说明公用经费并非对省级学生总量简单等比例。','2016标准不能沿用为全窗口不变标准；学校类型和受益人数未分省桥接。'),
 ('2019_responsibility','教育领域中央与地方财政事权和支出责任划分改革方案','国办发〔2019〕27号','2019-05-24','规范性文件','1.公用经费保障。','全国基准及中央地方分担构成财政制度背景。','支出总额不是本级财力负担；不得由金额增长判断地方财政压力增加。'),
 ('2022_staffing','中央编办四局：十年来中小学教职工编制保障工作有关情况介绍','','2022-09-06','官方发布会材料','2019年，针对中小学在校生','官方材料介绍编制调整和人员流动政策，可作为动态调整问题的证据入口。','不是2019政策意见全文；教职工编制不等于专任教师实际人数，不能断言编制冻结。'),
]
ledger=[]
for suffix,title,number,date,kind,needle,claim,limit in specs:
 s=sources['adjustment_policy_'+suffix]
 text=read(ROOT/s['path']).text
 matched=[(i+1,t.strip()) for i,t in enumerate(text) if needle in t]
 assert len(matched)==1,(suffix,needle,len(matched))
 ordinal,paragraph=matched[0]
 ledger.append(dict(title=title,document_number=number,document_date=date,evidence_kind=kind,url=s['url'],raw_path=s['path'],sha256=s['sha256'],locator=f'HTMLParser data segment {ordinal}; starts {needle}',supported_interpretation=claim,limit=limit))
s=sources['adjustment_policy_2023_standard_attachment']
with pdfplumber.open(ROOT/s['path']) as pdf:text=pdf.pages[8].extract_text()
assert all(x in text for x in ['720','940','300','100','6000'])
ledger.append(dict(title='国家基本公共服务标准（2023年版）',document_number='发改社会〔2023〕1072号附件',document_date='2023-07-30',evidence_kind='规范性文件附件',url=s['url'],raw_path=s['path'],sha256=s['sha256'],locator='PDF page 9, printed page 7; obligation education public funding service standard; rendered page visually checked',supported_interpretation='小学720元、初中940元公用经费基准；寄宿增加300元；农村不足100人按100人；特殊教育6000元。',limit='基准定额不是年鉴实际生均支出；标准不构成对应年度执行效果的因果证据。'))
save_csv(DATA/'adjustment_policy_evidence_ledger.csv',ledger)
assert sum(r['increase']+r['decrease']+r['unchanged'] for r in summary)==23*4
assert len(fund)==23*6 and len(fs)==12
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
(DATA/'persistent_decline_policy_audit.json').write_text(json.dumps(dict(source_documents=len(manifest),evidence_rows=len(ledger),direction_summary_rows=len(summary),fund_summary_rows=len(fs),all_source_hashes_verified=True,pdf_page_visually_checked=9,protected_files_unchanged=True,scope='observed enrollment spells and policy context; no demographic or causal claim'),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(fs,ensure_ascii=False))
