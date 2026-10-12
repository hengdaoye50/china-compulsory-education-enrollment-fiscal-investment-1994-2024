"""Screen literature against verified CSSCI source journals; full texts still pending."""
import json,hashlib,re,html
from parse import ROOT,save_csv,decode,read
import pdfplumber
DATA=ROOT/'data'
sources=json.loads((ROOT/'literature_cssci_sources.json').read_text(encoding='utf-8'))+json.loads((ROOT/'literature_cssci_membership_sources.json').read_text(encoding='utf-8'))
lookup={s['key']:s for s in sources}
for s in sources:
 assert s['status']=='downloaded'
 assert hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest()==s['sha256']
save_csv(DATA/'literature_cssci_source_registry.csv',[{k:v for k,v in s.items() if k!='links'} for s in sources])
copy=lookup['literature_cssci_text_copy']
with pdfplumber.open(ROOT/copy['path']) as pdf:
 assert '177 教育研究 教育学' in pdf.pages[9].extract_text()
 assert '350 西南民族大学学报(人文社会科学版)' in pdf.pages[18].extract_text()
primary=lookup['literature_cssci_2025_2026']
journals=[dict(journal='教育研究',cssci_edition='2025-2026',membership='CSSCI source journal; not extension',official_directory_copy_url=primary['url'],official_copy_sha256=primary['sha256'],official_copy_visual_locator='PDF page 6, row 221; edition page 1',university_compilation_url=copy['url'],compilation_locator='PDF page 10, row 177',limit='official directory reproduced on university library host; not a live CSSCI individual article record'),dict(journal='西南民族大学学报（人文社会科学版）',cssci_edition='2025-2026',membership='CSSCI source journal; not extension',official_directory_copy_url=primary['url'],official_copy_sha256=primary['sha256'],official_copy_visual_locator='PDF page 13, row 484; edition page 1',university_compilation_url=copy['url'],compilation_locator='PDF page 19, row 350',limit='official directory reproduced on university library host; not a live CSSCI individual article record')]
save_csv(DATA/'literature_cssci_journal_checks.csv',journals)
content=decode((ROOT/lookup['literature_education_research_index']['path']).read_bytes())
entries=[]
for m in re.finditer(r'onclick="[^"]*"',content):
 value=html.unescape(m.group())
 if value.startswith('onclick="toJournal('):
  start=value.find('{');end=value.rfind('}')
  if start>=0:
   try:obj=json.loads(value[start:end+1])
   except json.JSONDecodeError:continue
   if obj.get('id') in [6516,6517]:entries.append(obj)
assert len(entries)==2
(DATA/'literature_education_research_public_metadata.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
papers=[]
for obj in entries:
 title=obj['title'].replace(' ——','——')
 papers.append(dict(paper_id='L01' if obj['id']==6516 else 'L02',title=title,authors='梁文艳；孙雨婷；杜育红' if obj['id']==6516 else '蔺海沣；马玲',journal='教育研究',year=2026,issue=2,pages='',cssci_edition='2025-2026',qualification='source journal verified',bibliography_source=lookup['literature_education_research_index']['url'],raw_path=lookup['literature_education_research_index']['path'],locator=f'public index item {obj["id"]}; chapter_name second issue; issue_at year 2026',available_evidence='publisher public title/authors/issue metadata only',full_text_obtained=False,selection_status='priority candidate; content-level inclusion pending full-text review',intended_use='teacher adjustment and stage/region differences' if obj['id']==6516 else 'population structure and public expenditure relationship; inspect reviewed studies and heterogeneity',forbidden_inference='do not infer sample, effect direction, effect size or methods from title'))
chen=lookup['literature_chen_qin_2026'];li=lookup['literature_li_huang_2025']
assert '8省16县' in ''.join(read(ROOT/chen['path']).text)
assert '2025年第5期' in ''.join(read(ROOT/li['path']).text)
papers+= [dict(paper_id='L03',title='学龄人口减少对乡村小规模学校发展的影响及其疏解——基于东北地区人口负增长省份的调查',authors='李涛；黄嘉欣',journal='教育研究',year=2025,issue=5,pages='',cssci_edition='2025-2026',qualification='source journal verified',bibliography_source=li['url'],raw_path=li['path'],locator='author institution publication announcement dated 2026-03-18; article year/issue explicitly 2025/5',available_evidence='author institution research summary; no journal full text',full_text_obtained=False,selection_status='candidate; content-level inclusion pending full-text review',intended_use='school scale, teacher structure and service-space alternatives',forbidden_inference='do not generalize selected schools to all provinces or certify publication-page details from unrelated mirrors'),dict(paper_id='L04',title='人口变动趋势下基础教育师资配置机制研究——基于8省16县（区）的调查',authors='陈坤；秦玉友',journal='西南民族大学学报（人文社会科学版）',year=2026,issue=5,pages='229-240',cssci_edition='2025-2026',qualification='source journal verified',bibliography_source=chen['url'],raw_path=chen['path'],locator='publisher article page, volume 47 issue 5, dated 2026-05-29; abstract',available_evidence='publisher abstract and bibliography',full_text_obtained=False,selection_status='candidate; content-level inclusion pending full-text review',intended_use='distinguish teacher quantity, structure and coordination; inspect fieldwork and institutional explanations',forbidden_inference='abstract is not full-text review; do not claim mechanism established for current province-stage panel')]
papers=sorted(papers,key=lambda r:r['paper_id'])
save_csv(DATA/'literature_cssci_candidate_ledger.csv',papers)
protected=json.loads((DATA/'province_finance_next_protected_baseline.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
audit=dict(sources_saved_and_hash_verified=len(sources),qualified_source_journals=2,candidates=4,candidate_full_texts_obtained=0,content_level_formal_inclusions=0,publisher_metadata_only=2,publisher_abstract_only=1,author_institution_summary_only=1,cssci_extension_accepted=False,new_models=False,charts_updated=False,protected_files_unchanged=True)
(DATA/'literature_cssci_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
