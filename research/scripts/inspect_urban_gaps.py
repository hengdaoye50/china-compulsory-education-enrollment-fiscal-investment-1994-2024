import json
from parse import ROOT,read
for file in ROOT.glob('*.json'):
    obj=json.loads(file.read_text(encoding='utf-8'))
    if not isinstance(obj,list):continue
    for s in obj:
        if not isinstance(s,dict):continue
        key=s.get('key','')
        if 'national' not in key or not any(str(y) in key for y in range(2013,2018)):continue
        for link in s.get('links',[]):
            title=link.get('label','')
            if '小学' in title and any(w in title for w in ['专任教师','班']):print(key,title,link['url'])
items=json.loads((ROOT/'data/structure_source_headers.json').read_text(encoding='utf-8'))
for s in items:
    if s['year']==2013 and 'national' in s['key'] and '小学' in s['title'] and '班' in s['title']:
        print('2013 CLASS',s['key'],s['title'],s['path'])
        print(read(ROOT/s['path']).tables[0][:12])
urban=json.loads((ROOT/'urban_sources.json').read_text(encoding='utf-8'))
for s in urban:
    if s['key']=='urban_national_2013_directory':
        for l in s['links']:
            if '小学' in l['label']:print(json.dumps(l,ensure_ascii=True))
try:
    from pypdf import PdfReader
    text='\n'.join(p.extract_text() or '' for p in PdfReader(ROOT/'raw/urban_definition_education.pdf').pages)
    (ROOT/'data/urban_definition_education_text.txt').write_text(text,encoding='utf-8')
    for term in ['SZDCXLB','所在地域城乡','城区','学校所在地']:
        pos=text.find(term)
        print(term,repr(text[max(0,pos-150):pos+1100]))
except ImportError as e:print(e)
