from pathlib import Path
from pypdf import PdfReader
from lxml import etree as E
import zipfile, re, json, sys
base=Path(sys.argv[1]) if len(sys.argv)>1 else Path('义务教育趋势分析报告_结论与政策启示修订版_20261012')
docx=next(base.glob('*.docx'))
pdf=next((base/'排版核验').glob('*.pdf'))
texts=[re.sub(r'\s+','',p.extract_text()) for p in PdfReader(pdf).pages]
with zipfile.ZipFile(docx) as z:
 xml=E.fromstring(z.read('word/document.xml'))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
mapping={}
for p in xml.findall('w:body/w:p',ns):
 text=''.join(p.itertext()) if False else ''.join(p.xpath('.//w:t/text()',namespaces=ns))
 tabs=p.xpath('.//w:tab',namespaces=ns)
 if not tabs:continue
 ts=p.xpath('.//w:t',namespaces=ns)
 if not ts or not (ts[-1].text or '').isdigit():continue
 title=''.join((t.text or '') for t in ts[:-1])
 key=re.sub(r'\s+','',title)
 matches=[i+1 for i,t in enumerate(texts) if key in t[:230] and '目录' not in t[:80]]
 assert len(matches)==1,(title,matches)
 ts[-1].text=str(matches[0]);mapping[title]=matches[0]
temp=base/'toc_updated.docx'
with zipfile.ZipFile(docx) as a,zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED) as b:
 for info in a.infolist(): b.writestr(info,E.tostring(xml,xml_declaration=True,encoding='UTF-8',standalone=True) if info.filename=='word/document.xml' else a.read(info.filename))
temp.replace(docx)
(base/'目录页码核验.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
print(mapping)
