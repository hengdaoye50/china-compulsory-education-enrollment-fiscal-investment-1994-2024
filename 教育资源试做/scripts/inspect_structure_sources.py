"""Inventory existing official files for structural analysis, without fitting models."""
import json,re,hashlib
from parse import ROOT,read,decode,save_csv
sources={}
for manifest in ROOT.glob('*.json'):
    obj=json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(obj,list):continue
    for src in obj:
        if not isinstance(src,dict) or src.get('status')!='downloaded':continue
        if src.get('path','').endswith('.html'):sources.setdefault(src['path'],src)
inventory=[];details=[]
for path,src in sources.items():
    raw=ROOT/path
    html=decode(raw.read_bytes())
    match=re.search(r'<meta\s+name=["\']ArticleTitle["\']\s+content=["\'](.*?)["\']',html,re.I)
    title=match[1] if match else ''
    if not any(k in title for k in ['小学','初中','民办','城乡']):continue
    year_match=re.search(r'20\d{2}',src.get('key',''))
    if not year_match:continue
    parsed=read(raw)
    rows=[row for table in parsed.tables for row in table]
    relevant=[row for row in rows if any(term in ' '.join(row) for term in ['城区','镇区','乡村','城市','县镇','农村','举办者','教育部门','民办','一年级','Grade 1'])]
    inv={'year':int(year_match[0]),'key':src['key'],'title':title,'source':src['url'],'path':path,
         'sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
         'digest_matches_manifest':hashlib.sha256(raw.read_bytes()).hexdigest()==src.get('sha256'),
         'tables':len(parsed.tables),'urban_rural_terms':any(any(t in ' '.join(r) for t in ['城区','镇区','乡村','城市','县镇','农村']) for r in rows),
         'provider_terms':any(any(t in ' '.join(r) for t in ['举办者','教育部门','民办','教育部门办','地方企业']) for r in rows),
         'grade_terms':any('Grade 1' in ' '.join(r) or '一年级' in ' '.join(r) for r in rows)}
    inventory.append(inv)
    details.append({**inv,'first_rows':parsed.tables[0][:8] if parsed.tables else [],'classification_rows':relevant[:30]})
save_csv(ROOT/'data/structure_source_inventory.csv',inventory)
(ROOT/'data/structure_source_headers.json').write_text(json.dumps(details,ensure_ascii=False,indent=2),encoding='utf-8')
directory_links=[]
for src in sources.values():
    if 'region' not in src.get('key','') or not any(x in src['key'] for x in ['index','page']):continue
    for link in src.get('links',[]):
        label=link.get('label','')
        if any(x in label for x in ['小学','初中']) and any(x in label for x in ['城乡','城区','镇区','乡村','城市','县镇','农村','民办','举办者']):
            directory_links.append({'directory_key':src['key'],'directory_source':src['url'],'link_title':label,'link_source':link.get('url')})
save_csv(ROOT/'data/structure_directory_candidates.csv',directory_links)
scope={'saved_html_inspected':len(sources),'education_structure_files':len(inventory),
       'digest_mismatches':sum(not r['digest_matches_manifest'] for r in inventory),
       'saved_province_files_with_classification_terms':sum('region' in r['key'] and (r['urban_rural_terms'] or r['provider_terms']) for r in inventory),
       'saved_province_directory_classification_candidates':directory_links,
       'scope':'Existing downloaded files and retained directory links only; not a claim that no finer public data exists elsewhere.'}
(ROOT/'data/structure_availability_validation.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2),encoding='utf-8')
print('Files inspected:',len(inventory),'digest mismatches:',sum(not r['digest_matches_manifest'] for r in inventory))
print('Province classification directory candidates:',len(directory_links))
