from collect import *
indexes=json.loads((ROOT/'indexes.json').read_text(encoding='utf-8'))+json.loads((ROOT/'extra_indexes.json').read_text(encoding='utf-8'))
jobs=[]
for r in indexes:
    if r['key'].startswith('legacy_index'):
        for a in r.get('links',[]):
            if any(x in a['label'] for x in ['各地基本','全国基本']):jobs.append((r['key']+'_'+('region' if '各地' in a['label'] else 'national'),a['url']))
    for i,a in enumerate(r.get('links',[])):
        t=a['label']
        if ('finance_' in r['key'] and ('统计表' in t or re.search(r'\.(docx?|xlsx?|pdf)$',a['url'],re.I))) or ('finance_' not in r['key'] and ('小学' in t or '初中' in t) and '.html' in a['url']):
            jobs.append((r['key']+'_'+str(i),a['url']))
jobs=list(dict(jobs).items())
batch(jobs,'selected_sources')
