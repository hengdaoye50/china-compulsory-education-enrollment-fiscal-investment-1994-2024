import urllib.request, urllib.parse, concurrent.futures, json, hashlib, re, time
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'raw'; RAW.mkdir(parents=True,exist_ok=True)
class Links(HTMLParser):
    def __init__(self): super().__init__(); self.items=[]; self.href=None; self.label=''
    def handle_starttag(self,tag,attrs):
        if tag=='a': self.href=dict(attrs).get('href'); self.label=''
    def handle_data(self,data):
        if self.href: self.label+=data
    def handle_endtag(self,tag):
        if tag=='a' and self.href: self.items.append((self.href,self.label.strip())); self.href=None
def fetch(job):
    key,url=job; ext=Path(urllib.parse.urlsplit(url).path).suffix.lower(); path=RAW/(key+(ext if ext in ['.doc','.docx','.xls','.xlsx','.pdf','.jpg'] else '.html'))
    try:
        if path.exists(): b=path.read_bytes()
        else:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35) as r:b=r.read()
            path.write_bytes(b)
        p=Links()
        if path.suffix=='.html':
            try:s=b.decode('utf-8')
            except UnicodeDecodeError:s=b.decode('gb18030',errors='replace')
            p.feed(s)
        return dict(key=key,url=url,status='downloaded',bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),path=str(path.relative_to(ROOT)),links=[dict(url=urllib.parse.urljoin(url,h),label=t) for h,t in p.items])
    except Exception as e: return dict(key=key,url=url,status='failed',error=str(e))
def batch(jobs,name):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex: rows=list(ex.map(fetch,jobs))
    (ROOT/(name+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    for r in rows:
        print(r['key'],r['status'],r.get('bytes',r.get('error')))
    return rows
if __name__=='__main__':
    jobs=[(f'moe_index_{y}',f'https://hudong.moe.gov.cn/jyb_sjzl/moe_560/{y}/') for y in range(2010,2025)]
    jobs += [('finance_index','https://hudong.moe.gov.cn/jyb_sjzl/sjzl_jfzxgg/'),('nbs_index_2024','https://www.stats.gov.cn/sj/ndsj/2024/left.htm'),('nbs_index_2025','https://www.stats.gov.cn/sj/ndsj/2025/left.htm')]
    rows=batch(jobs,'catalogs')
    for r in rows:
        for a in r.get('links',[]):
            if any(x in a['label'] for x in ['小学','经费','分地区','居民消费价格','地方一般公共预算']):print(r['key'],a['label'],a['url'])
