"""Read wrapped flat revenue columns; preserve every contributing source cell."""
import csv,json,re,collections,hashlib
from decimal import Decimal
from pathlib import Path
from inspect_bridge_evidence import sheets
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'教育资源试做/data/财政收入核准_20261010'
OUT=ROOT/'教育资源试做/data/财政收入补核_20261010'
OUT.mkdir(exist_ok=True)
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(n,rs):
 with (OUT/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def norm(v):return re.sub(r'\s+','',str(v or ''))
def proposed(v):
 t=str(v).strip() if v is not None else ''
 if not t:return None,'blank'
 if re.fullmatch(r'[-+—−–]?\d[\d \u00a0]*(?:\.\d+)?',t):
  s=re.sub(r'[ \u00a0]+','',t);s=re.sub(r'^[—−–]','-',s)
  return Decimal(s),'format_proposal' if s!=t else 'plain_numeric'
 return None,'unparsed_nonblank'
def main():
 records=read(BASE/'R_numeric_verification.csv');sources={r['source_id']:r for r in read(ROOT/'教育资源试做/data/长期财政数据建设_20261010/source_registry.csv')}
 prior={r['evidence_id']:r for r in json.loads((BASE/'R_original_header_component_evidence.json').read_text(encoding='utf8'))}
 panel=read(BASE/'R_province_year_numeric_panel.csv');pmap={(r['year'],r['province']):r for r in panel}
 results=[];details=[]
 for r in records:
  if r['numeric_status'] not in ['component_closure_pending','numeric_format_pending']:continue
  e=prior[r['record_id']];unit=r['verified_unit']
  if unit not in ['万元','亿元'] or r['final_column_header_verified']!='True':continue
  rr=dict(sheets(sources[r['source_id']]))[sources[r['source_id']]['sheet']]
  row=int(re.search(r'\d+',r['cell']).group());col=int(re.match(r'([A-Z]+)',r['cell']).group().encode()[0])-65
  start=e['block_start_row']-1;income=rr[start:row-1]
  # Flat historical tax lists only: skip grouped tax/non-tax tables and any left-column expenditure section.
  grouped=any(re.search(r'^[一二三四五六七八九十]+[、.．，,](?:税收收入|非税收入)$',norm(x[0])) for x in income if x)
  expense=any(norm(x[0]).startswith('支出') for x in income if x)
  numbered=sum(bool(re.match(r'^\d+[、.．]',norm(x[0]))) for x in income if x)
  if grouped or expense or numbered<10:continue
  components=[];invalid=[]
  for i,x in enumerate(income,start+1):
   if len(x)<=col:continue
   v,status=proposed(x[col]);raw=x[col]
   if v is None:
    if raw is not None and str(raw).strip() and re.search(r'\d',str(raw)):invalid.append(dict(row=i,raw=raw))
    continue
   components.append(dict(row=i,column=col+1,label=x[0],raw=raw,proposed=str(v),format=status))
  total,fmt=proposed(r['raw_value']);component_sum=sum((Decimal(c['proposed']) for c in components),Decimal(0))
  normalized=total/10000 if total is not None and unit=='万元' else total
  compiled=Decimal(r['compiled_R']) if r['compiled_R'] else None
  diff=normalized-compiled if normalized is not None and compiled is not None else None
  closure=not invalid and total is not None and total==component_sum
  approved=closure and diff is not None and abs(diff)<=Decimal('.005') and r['province_year_candidate_count']=='1' and total>0
  status='accepted_wrapped_column_numeric_only' if approved else 'pending'
  results.append(dict(record_id=r['record_id'],year=r['year'],province=r['province'],cell=r['cell'],raw_total=r['raw_value'],proposed_total='' if total is None else str(total),unit=unit,observed_numeric_cells=len(components),format_proposal_cells=sum(c['format']=='format_proposal' for c in components),unparsed_digit_cells=len(invalid),observed_column_sum=str(component_sum),exact_closure=closure,compiled_R=r['compiled_R'],difference_yi='' if diff is None else str(diff),adjudicated_R_yi=str(normalized) if approved else '',status=status,model_eligible=False))
  details.append(dict(record_id=r['record_id'],source_id=r['source_id'],table=sources[r['source_id']]['table'],sheet=sources[r['source_id']]['sheet'],source_sha256=sources[r['source_id']]['table_sha256'],components=components,invalid_cells=invalid,basis='sum observed numeric income-column cells; wrapped labels not mapped or repaired; format proposals are not individual publisher-cell approvals'))
  if approved:
   p=pmap[(r['year'],r['province'])];assert p['R_adjudicated_yi']==''
   p['R_adjudicated_yi']=str(normalized);p['numeric_status']=status;p['selection_basis']='original units and final header; exact flat income-column sum; independent compiled agreement; detailed cells in wrapped_R_evidence.json'
 write('wrapped_R_adjudications.csv',results);write('R_province_year_numeric_panel.csv',panel)
 (OUT/'wrapped_R_evidence.json').write_text(json.dumps(details,ensure_ascii=False,indent=2),encoding='utf8')
 receipt=dict(checked=len(results),new_accepted=sum(r['status'].startswith('accepted') for r in results),total_selected=sum(bool(r['R_adjudicated_yi']) for r in panel),statuses=dict(collections.Counter(r['numeric_status'] for r in panel)),baseline_sha256=hashlib.sha256((BASE/'R_province_year_numeric_panel.csv').read_bytes()).hexdigest())
 (OUT/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(receipt,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
