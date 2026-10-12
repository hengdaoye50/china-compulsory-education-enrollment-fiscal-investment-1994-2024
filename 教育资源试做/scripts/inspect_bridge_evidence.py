from pathlib import Path
import csv,io,json,zipfile,sys,re,hashlib
import openpyxl,pdfplumber
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'教育资源试做/data/口径核准_20261010'
OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'教育资源试做/.tmp/yearbook_read_deps'))
sys.stdout.reconfigure(encoding='utf8')
def readcsv(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
CAT=readcsv(ROOT/'教育资源试做/data/年鉴资料核查_20261010/all_archive_tables.csv')
ZS={}
def getbytes(s):
 archive=s['archive']
 if archive not in ZS:
  z=zipfile.ZipFile(ROOT/archive);idx={}
  for i in z.infolist():
   n=i.filename
   if not i.flag_bits&0x800:
    try:n=n.encode('cp437').decode('gbk')
    except UnicodeError:pass
   idx[n]=i
  ZS[archive]=(z,idx)
 z,idx=ZS[archive];return z.read(idx[s['table']])
def sheets(s):
 b=getbytes(s)
 if b[:2]==b'PK':
  w=openpyxl.load_workbook(io.BytesIO(b),read_only=True,data_only=True)
  result=[(s.title,list(s.iter_rows(values_only=True))) for s in w];w.close();return result
 import xlrd
 w=xlrd.open_workbook(file_contents=b);return [(s.name,[s.row_values(i) for i in range(s.nrows)]) for s in w.sheets()]
def norm(v):return re.sub(r'\s+','',str(v or ''))
def main():
 tables=[]
 for a in CAT:
  y=int(a['volume_year']);name=Path(a['table']).name
  if a['family']!='中国教育统计年鉴' or not a['table'].endswith('.xlsx'):continue
  keep=(y==2005 and '普通初中学生数' in name and any(t in name for t in ['农村','县镇','城市'])) or (y==2006 and name=='小学学生数.xlsx') or (y in [2005,2006,2007,2008,2013] and (name=='普通初中学生数.xlsx' or name=='初中学生数.xlsx' or name=='小学学生数.xlsx'))
  if not keep:continue
  ss=sheets(a)
  record=dict(**a,sha256=hashlib.sha256(getbytes(a)).hexdigest(),sheets=[{'sheet':n,'rows':r} for n,r in ss]);tables.append(record)
  print('TABLE',y,a['table'])
  for n,r in ss:
   for i,row in enumerate(r,1):
    if i<=17 or any('贵州' in norm(v) for v in row[:2]):print(n,i,row)
 (OUT/'student_cross_table_evidence.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2),encoding='utf8')
 notes=[]
 for a in CAT:
  if a['family']!='中国教育经费统计年鉴' or int(a['volume_year']) not in [1996,2001,2007,2008,2012,2015,2017,2021,2023] or not re.search('说明.*pdf$',a['table']):continue
  b=getbytes(a);p=OUT/f'经费{a["volume_year"]}_统计说明.pdf';p.write_bytes(b)
  with pdfplumber.open(io.BytesIO(b)) as pdf:pages=[page.extract_text() or '' for page in pdf.pages]
  note=dict(**a,sha256=hashlib.sha256(b).hexdigest(),pages=pages,path=str(p.relative_to(ROOT)));notes.append(note)
  (OUT/f'经费{a["volume_year"]}_说明文本.txt').write_text('\n\n'.join(f'PAGE {i+1}\n{t}' for i,t in enumerate(pages)),encoding='utf8')
  print('PDF',a['volume_year'],len(pages),'chars',sum(map(len,pages)))
 (OUT/'finance_note_evidence.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()
