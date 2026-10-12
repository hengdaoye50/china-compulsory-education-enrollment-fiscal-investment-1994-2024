from collect import *
records=[]
for name in ['catalogs','indexes','extra_indexes','selected_sources','legacy_pages','legacy_tables','supplemental_catalogs','supplemental_tables']:
    p=ROOT/(name+'.json')
    if p.exists():records+=json.loads(p.read_text(encoding='utf-8'))
index=next(r for r in records if r['key']=='moe_index_2024' and r['status']=='downloaded')
print('2024 directory branches',[(a['label'],a['url']) for a in index['links'] if a['label'] in ['全国基本情况','各地基本情况']])
audit=[]
for y in range(2010,2025):
    fs=[r for r in records if r['key']==f'finance_{y}' and r['status']=='downloaded']
    attachments=[r for r in records if r['key'].startswith(f'finance_{y}_') and r['status']=='downloaded' and Path(r.get('path','')).suffix in ['.doc','.docx']]
    audit.append({'year':y,'announcement_saved':bool(fs),'attachment_saved':bool(attachments),'announcement_url':fs[0]['url'] if fs else '', 'attachment_url':attachments[0]['url'] if attachments else '', 'attachment_file':attachments[0]['path'] if attachments else ''})
assert all(r['announcement_saved'] and r['attachment_saved'] for r in audit)
(ROOT/'data/finance_download_recheck.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('finance announcements and original attachments verified',len(audit))
batch([('beijing_finance_2019_refiling_note','https://jw.beijing.gov.cn/cwc/cwzd/202204/P020220428602833339063.pdf')],'recheck_sources')
