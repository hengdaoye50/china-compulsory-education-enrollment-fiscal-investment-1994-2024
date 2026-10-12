from html.parser import HTMLParser
from pathlib import Path
import json,re,csv
ROOT=Path(__file__).resolve().parents[1]
def decode(b):
    try:return b.decode('utf-8')
    except UnicodeDecodeError:return b.decode('gb18030',errors='replace')
class Tables(HTMLParser):
    def __init__(self):super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None;self.text=[]
    def handle_starttag(self,t,a):
        if t=='table':self.table=[]
        if t=='tr':self.row=[]
        if t in ['td','th']:self.cell=''
    def handle_data(self,d):
        self.text.append(d)
        if self.cell is not None:self.cell+=d
    def handle_endtag(self,t):
        if t in ['td','th'] and self.cell is not None:
            if self.row is not None:self.row.append(' '.join(self.cell.split()))
            self.cell=None
        if t=='tr' and self.row is not None:
            if self.table is not None:self.table.append(self.row)
            self.row=None
        if t=='table' and self.table is not None:self.tables.append(self.table);self.table=None
def read(path):
    p=Tables();p.feed(decode(Path(path).read_bytes()));return p
def save_csv(path,rows):
    if not rows:return
    with open(path,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
if __name__=='__main__':
    for p in sorted((ROOT/'converted').glob('*.html')):
        t=read(p);print(p.name,len(t.tables))
        for i,table in enumerate(t.tables):print(i,table[:3])
