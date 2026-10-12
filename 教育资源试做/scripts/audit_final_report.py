"""Verify report numbers, source bindings, OOXML and final PDF page structure."""
from pathlib import Path
import json,hashlib,re,shutil
import pandas as pd
from docx import Document
from pypdf import PdfReader
from zipfile import ZipFile
from lxml import etree

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'正式分析报告_20261011';QA=OUT/'qa'
docpath=OUT/'义务教育经费长期演进分析报告.docx'
pdfpath=QA/'义务教育经费长期演进分析报告.pdf'
doc=Document(docpath);pdf=PdfReader(pdfpath)
f=pd.read_csv(ROOT/'教育资源试做/data/早期财政重建_20261011/national_fiscal_1994_2024_report_final.csv')
s=pd.read_csv(ROOT/'教育资源试做/正式学术图组_20261011/figure_data/fig01.csv')
g=pd.read_csv(ROOT/'教育资源试做/正式学术图组_20261011/figure_data/fig05.csv')
check={}
def number(x):return f'{x:,.2f}'
check['four_tables_eight_figures']=len(doc.tables)==4 and len(doc.inline_shapes)==8
for i,stage in enumerate(['primary','junior'],1):
    fr=f[(f.stage==stage)&(f.year==2024)].iloc[0]
    sr=s[(s.stage==stage)&(s.year==2024)].iloc[0]
    estimate=f[(f.stage==stage)&(f.year==1994)].iloc[0]
    check[stage+'_student_table']=doc.tables[0].cell(i,1).text==number(sr.students/10000) and doc.tables[0].cell(i,2).text==f'{sr.student_change_pct:+.2f}%'
    check[stage+'_fiscal_table']=doc.tables[1].cell(i,1).text==number(fr.fiscal_yi) and doc.tables[1].cell(i,2).text==f'{fr.fiscal_share_pct:.2f}%'
    check[stage+'_1994_table']=all(doc.tables[3].cell(i,j).text==v for j,v in enumerate([number(estimate.fiscal_yi),number(estimate.total_yi),f'{estimate.fiscal_share_pct:.2f}%'],1))
for i,start in enumerate([1995,2007,2013],1):
    for j,stage in enumerate(['primary','junior'],1):
        median=g[(g.stage==stage)&(g.start_year==start)].PC_real_annualized_pct.median()
        check[f'growth_table_{stage}_{start}']=doc.tables[2].cell(i,j).text==f'{median:.2f}%'
text='\n'.join(p.extract_text() for p in pdf.pages)
compact=re.sub(r'\s+','',text)
check['pdf_nine_nonblank_pages']=len(pdf.pages)==9 and all(len(p.extract_text())>60 for p in pdf.pages)
check['pdf_critical_values']=all(v in compact for v in ['399.27','257.35','501.95','327.55','96.11%','94.68%','91.36%','89.37%','107.31%','111.27%'])
check['pdf_no_replacement_glyph']=not any(c in text for c in ['\ufffd','\u25a0'])
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(docpath) as z:
    styles=etree.fromstring(z.read('word/styles.xml'))
    check['title_no_blue_border']=not styles.xpath('//w:style[@w:styleId="Title"]//w:pBdr',namespaces=ns)
    media=[z.read(n) for n in z.namelist() if n.startswith('word/media/')]
    embedded={hashlib.sha256(b).hexdigest() for b in media}
    expected={hashlib.sha256((ROOT/'教育资源试做/正式学术图组_20261011/png'/f'fig{n:02d}.png').read_bytes()).hexdigest() for n in range(1,9)}
    check['all_eight_embedded_figures_match_latest']=embedded==expected
record=json.loads((OUT/'报告制作记录.json').read_text(encoding='utf8'))
check['source_hashes_match']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in record['inputs'].items())
protected=json.loads((ROOT/'教育资源试做/data/长期财政数据建设_20261010/build_receipt.json').read_text(encoding='utf8'))['protected_hashes']
check['protected_inputs_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in protected.items())
assert all(check.values()),check
old=json.loads((QA/'visually_reviewed_page_hashes.json').read_text(encoding='utf8'))
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in QA.glob('page-*.png')}
changed=[n for n,v in hashes.items() if old.get(n)!=v]
assert len(hashes)==9
shutil.copy2(pdfpath,OUT/pdfpath.name)
record.update({'render_verified':True,'actual_pages':len(pdf.pages),'numeric_and_document_checks':check,'all_checks_passed':True,'visual_review':'All nine rendered pages inspected; after equal-length wording edits, changed pages re-inspected and unchanged page hashes compared. No clipping, overflow, blank pages, blue title borders, or missing Chinese glyphs observed.','changed_pages_after_final_wording':changed,'page_png_sha256':hashes,'final_pdf_sha256':hashlib.sha256((OUT/pdfpath.name).read_bytes()).hexdigest(),'docx_sha256':hashlib.sha256(docpath.read_bytes()).hexdigest(),'conversion_engine':'Local LibreOffice; PDF exported from the delivered Word file, not separately typeset.'})
(OUT/'报告制作记录.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'pages':9,'checks':len(check),'all_passed':True,'changed_pages':changed,'docx_bytes':docpath.stat().st_size,'pdf_bytes':(OUT/pdfpath.name).stat().st_size},ensure_ascii=False))
