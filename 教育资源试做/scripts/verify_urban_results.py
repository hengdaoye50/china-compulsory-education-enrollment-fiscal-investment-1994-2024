import csv,json,hashlib,math,re
from parse import ROOT,decode,save_csv
from lxml import html

def load(name):return list(csv.DictReader((ROOT/'data'/name).open(encoding='utf-8-sig')))
tables={};source_checks=[]
for cell in load('national_urban_rural_cells.csv')+load('urban_grade1_cells.csv'):
    path=cell['path']
    if path not in tables:
        tree=html.fromstring(decode((ROOT/path).read_bytes()))
        # Select each tr once: some legacy pages nest the data table in layout tables.
        tables[path]=[[[' '.join(td.text_content().split()) for td in tr.xpath('./td|./th')] for tr in tree.xpath('//tr')]]
    # lxml repairs omitted HTML row endings, so row positions need not match HTMLParser.
    # Select native category labels and numeric data, without using the expected value.
    labels=('总计','合计') if cell['category']=='全国' else (cell['category'],)
    matches=[row for tab in tables[path] for row in tab if row and ''.join(row[0].split()).startswith(labels) and (cell['category']!='全国' or re.match(r'^(总计|合计)(Total|$)',''.join(row[0].split()),re.I)) and len(row)>int(cell['column_index']) and row[int(cell['column_index'])].replace(',','').isdigit() and int(row[int(cell['column_index'])].replace(',',''))>1000]
    assert len(matches)==1,(cell['year'],cell['stage'],cell['metric'],cell['category'])
    raw=matches[0][int(cell['column_index'])]
    value=int(raw.replace(',',''))
    assert value==int(cell['value'])
    source_checks.append({'year':cell['year'],'stage':cell['stage'],'category':cell['category'],'metric':cell['metric'],'value':value,'matches':True,'path':path})
panel={(int(r['year']),r['stage'],r['category']):r for r in load('national_urban_rural_panel.csv')}
decomp=load('urban_ratio_decomposition.csv');ratio_checks=[]
for r in decomp:
    if r['category']!='全国':continue
    y=int(r['year']);s=r['stage'];metric=r['metric'];na,nb=panel[y-1,s,'全国'],panel[y,s,'全国']
    # Average the two exact endpoint-order decompositions, independent of main formula.
    wa=[];wb=[];ra=[];rb=[]
    for c in ['城区','镇区','乡村']:
        a,b=panel[y-1,s,c],panel[y,s,c]
        wa.append(int(a['students'])/int(na['students']));wb.append(int(b['students'])/int(nb['students']))
        ra.append(100*int(a[metric])/int(a['students']));rb.append(100*int(b[metric])/int(b['students']))
    cross_ab=sum(w*x for w,x in zip(wa,rb));cross_ba=sum(w*x for w,x in zip(wb,ra))
    start=100*int(na[metric])/int(na['students']);end=100*int(nb[metric])/int(nb['students'])
    within=((cross_ab-start)+(end-cross_ba))/2
    share=((end-cross_ab)+(cross_ba-start))/2
    err=max(abs(within-float(r['within_category_component'])),abs(share-float(r['student_share_component'])))
    assert err<1e-12
    ratio_checks.append({'year':y,'stage':s,'metric':metric,'maximum_difference':err})
grade=load('urban_grade_contributions.csv')
assert all(abs(float(r['total_growth_pct'])-float(r['grade1_contribution_pp'])-float(r['remainder_contribution_pp']))<1e-12 for r in grade)
visual=ROOT/'教育资源试做.html'
visual_hash=hashlib.sha256(visual.read_bytes()).hexdigest()
assert visual_hash=='51b2140d8576491cf1c1629f628278edf6e65674b3b352ec4569fe6ba3d7ed06'
save_csv(ROOT/'data/urban_source_reparse_checks.csv',source_checks)
save_csv(ROOT/'data/urban_ratio_alternative_checks.csv',ratio_checks)
validation={'alternative_html_parser_cells':len(source_checks),'distinct_source_files':len(tables),'source_value_mismatches':0,'alternative_ratio_checks':len(ratio_checks),'maximum_ratio_difference':max(r['maximum_difference'] for r in ratio_checks),'grade_decomposition_checks':len(grade),'visual_sha256_unchanged':visual_hash,'review_type':'Alternative parsers and formulas checked by the same analyst; not independent human review.'}
(ROOT/'data/urban_results_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(validation,ensure_ascii=False))
