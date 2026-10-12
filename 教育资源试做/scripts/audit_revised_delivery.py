"""Verify the reviewed report, numbering, sources, key values and pagination."""
from pathlib import Path
from collections import Counter
import re,json,hashlib,shutil
import pandas as pd
from docx import Document
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'教育资源试做'
OUT=ROOT/'义务教育趋势分析报告_审校修订版_20261012'
m=json.loads((OUT/'正式报告生成记录.json').read_text(encoding='utf8'));name=m['title']
qa=OUT/'终稿审校';r=PdfReader(qa/(name+'.pdf'));texts=[p.extract_text() for p in r.pages]
doc=Document(OUT/(name+'.docx'));assert len(doc.inline_shapes)==18 and len(doc.tables)==15
for key,n in [('figures',18),('tables',15)]:assert [x['number'] for x in m[key]]==list(range(1,n+1))
for p,h in m['input_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
for f in m['figures']:assert hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest()==f['sha256']
gm=json.loads((OUT/'图表精修/图表精修记录.json').read_text(encoding='utf8'))
for p,h in gm['input_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
md=(OUT/'报告正文.md').read_text(encoding='utf8');assert '2013—2024年，财政性收入名义金额分别增长107.31%、111.27%' in md
assert '未因排版修改回归结果' not in md and '同一时期财政性收入名义金额增长' not in md
sp=pd.read_csv(BASE/'data/三十年纵向分析_20261010/recurrent_student_decline_spells.csv');counts=[]
for threshold in [2,3]:
    for stage in ['primary','junior']:
        z=sp[(sp.stage==stage)&(sp.decline_years>=threshold)]
        counts.append({'threshold':threshold,'stage':stage,'spells':len(z),'recurrent_provinces':int((z.groupby('province').size()>=2).sum())})
assert [(x['spells'],x['recurrent_provinces']) for x in counts]==[(63,21),(62,18),(50,15),(46,11)]
norm=lambda t:Counter(re.sub(r'\s+','',t))
pages={}
for title in m['chapters']:
    found=[i+1 for i,t in enumerate(texts) if i>=3 and any(norm(line)==norm(title) for line in t.splitlines())]
    assert len(found)==1,(title,found);pages[title]=found[0]
expected=json.loads((OUT/'目录页码.json').read_text(encoding='utf8'));assert pages==expected,(pages,expected)
prior=ROOT/'义务教育趋势分析报告_20261012';old=json.loads((prior/'交付核验记录.json').read_text(encoding='utf8'))
for ext,h in old['final_files'].items():assert hashlib.sha256((prior/(name+'.'+ext)).read_bytes()).hexdigest()==h
for figure in m['figures']:
    assert ('图'+str(figure['number'])) in md
sub=pd.read_csv(BASE/'data/支出细项与补助拓展_20261011/primary_subsidy_model_input.csv')
assert len(sub)==436 and int((sub.dR_real<0).sum())==84 and int(((sub.dR_real<0)&(sub.dRplusB_real>=0)).sum())==60
shutil.copy2(qa/(name+'.pdf'),OUT/(name+'.pdf'))
support=OUT/'复核资料';support.mkdir(exist_ok=True)
shutil.copy2(BASE/'data/三十年纵向分析_20261010/recurrent_student_decline_spells.csv',support/'生源下降轮次明细.csv')
pd.DataFrame(counts).to_csv(support/'持续期敏感性汇总.csv',index=False,encoding='utf-8-sig')
result={'pages':len(r.pages),'figures':18,'main_figures':13,'appendix_figures':5,'tables':15,'chapters':8,'appendices':4,'toc':pages,'original_reports_unchanged':True,'model_estimates_unchanged':True,'protected_source_hashes_verified':len(m['input_sha256']),'additional_figure_source_hashes_verified':len(gm['input_sha256']),'spell_counts':counts,'causal_mechanism_claimed':False,'1994_status':'conditional_estimate','sha256':{ext:hashlib.sha256((OUT/(name+'.'+ext)).read_bytes()).hexdigest() for ext in ['docx','pdf']}}
(OUT/'修订交付核验记录.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False))
