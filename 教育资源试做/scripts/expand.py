from collect import *
cats=json.loads((ROOT/'catalogs.json').read_text(encoding='utf-8'))
stage=__import__('sys').argv[1]
if stage=='indexes':
    master=next(x for x in cats if x['key']=='moe_index_2024')
    jobs=[]
    for a in master['links']:
        m=re.match(r'(\d{4})年教育统计数据',a['label'])
        if m and 2010<=int(m[1])<=2024:
            y=int(m[1]); jobs += [(f'region_index_{y}',a['url']+'gedi/'),(f'national_index_{y}',a['url']+'quanguo/')]
    jobs=list(dict(jobs).items())
    for a in next(x for x in cats if x['key']=='finance_index')['links']:
        m=re.match(r'(\d{4})年全国教育经费',a['label'])
        if m and 2010<=int(m[1])<=2024:jobs.append((f'finance_{m[1]}',a['url']))
    rows=batch(jobs,'indexes')
elif stage=='tables':
    rows=json.loads((ROOT/'indexes.json').read_text(encoding='utf-8'));jobs=[]
    for r in rows:
        for i,a in enumerate(r.get('links',[])):
            t=a['label']
            if ('index' in r['key'] and any(x in t for x in ['小学','初中','教师数','学校数','班数'])) or ('finance_' in r['key'] and ('统计表' in t or re.search(r'\.(xls|xlsx|pdf)',a['url'],re.I))):
                jobs.append((r['key']+'_'+str(i),a['url']))
    rows=batch(jobs,'tables')
for r in rows:
    for a in r.get('links',[]):
        if any(x in a['label'] for x in ['小学','初中','统计表']):print(r['key'],a)
