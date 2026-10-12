"""Strict number-format proposals with source headers and non-overlapping revenue checks."""
import csv,json,re,hashlib,collections
from decimal import Decimal,InvalidOperation
from pathlib import Path
from inspect_bridge_evidence import sheets
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'research/data/长期财政数据建设_20261010'
OUT=ROOT/'research/data/财政收入核准_20261010'
OUT.mkdir(exist_ok=True)
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def numeric(v):
 if v is None or str(v).strip()=='':return None,'blank'
 t=str(v).strip()
 if re.fullmatch(r'[+-]?\d+(?:\.\d+)?',t):return Decimal(t),'plain_numeric'
 if re.fullmatch(r'[+-]?\d{1,3}(?:[ \u00a0]+\d{3})+(?:\.\d+)?',t):return Decimal(re.sub(r'[ \u00a0]+','',t)),'strict_thousands_spacing'
 return None,'invalid_format'
def norm(v):return re.sub(r'\s+','',str(v or ''))
def write(n,rows):
 with (OUT/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 originals=[r for r in read(SRC/'fiscal_original_candidates.csv') if r['metric']=='R_fiscal_candidate']
 sources={r['source_id']:r for r in read(SRC/'source_registry.csv')}
 compiled={(r['data_year'],r['province']):r for r in read(SRC/'supplement_original_candidates.csv') if r['metric']=='R'}
 decisions={r['original_record_id']:r for r in read(ROOT/'research/data/口径核准_20261010/fiscal_R_adjudications.csv')}
 counts=collections.Counter((r['data_year'],r['province']) for r in originals)
 grouped=collections.defaultdict(list)
 for r in originals:grouped[r['source_id']].append(r)
 results=[];evidence=[]
 for index,(sid,records) in enumerate(grouped.items(),1):
  spec=sources[sid];ss=dict(sheets(spec));rr=ss[spec['sheet']]
  for r in sorted(records,key=lambda r:int(r['source_row'])):
   row=int(r['source_row']);col=int(r['source_column'])-1
   # Start at the nearest bilingual account title, or sheet beginning.
   starts=[i for i,x in enumerate(rr[:row-1]) if any('FINALACCOUNT' in norm(v).upper() and 'REVENUE' in norm(v).upper() for v in x)]
   start=starts[-1] if starts else 0
   # Do not reuse a previous province's header if no bilingual title exists.
   chinese_starts=[i for i,x in enumerate(rr[:row-1]) if any('收支决算总表' in norm(v) or '财政预算、决算收支' in norm(v) for v in x)]
   if chinese_starts and abs(chinese_starts[-1]-start)<=4:start=min(start,chinese_starts[-1])
   elif chinese_starts and chinese_starts[-1]>start:start=chinese_starts[-1]
   next_titles=[i for i,x in enumerate(rr[row:],row) if any(('FINALACCOUNT' in norm(v).upper() and 'REVENUE' in norm(v).upper()) or ('收支决算总表' in norm(v) and re.search(r'\d{4}',norm(v))) for v in x)]
   end=next_titles[0] if next_titles else len(rr)
   block=rr[start:end];header=block[:10]
   income_end=next((i for i,x in enumerate(block) if x and norm(x[0]).startswith('支出')),len(block))
   income=block[:income_end]
   unit_hits=[]
   chinese_categories=any(x and re.match(r'^[一二三四五六七八九十百]+[、.．，,]',norm(x[0])) for x in income)
   for i,x in enumerate(block,start+1):
    for j,v in enumerate(x,1):
     if '单位' in norm(v):
      unit='亿元' if '亿元' in norm(v) else ('万元' if '万元' in norm(v) else '')
      if unit:unit_hits.append(dict(row=i,column=j,raw=v,unit=unit))
   found={x['unit'] for x in unit_hits};unit=next(iter(found)) if len(found)==1 else ''
   final_headers=[dict(row=start+i+1,column=col+1,raw=x[col]) for i,x in enumerate(header) if len(x)>col and ('决算' in norm(x[col]) or 'FINAL' in norm(x[col]).upper())]
   value,fmt=numeric(r['raw_value']);components=[];tax=[];non_tax=[]
   for i,x in enumerate(income,start+1):
    if len(x)<=col:continue
    label=norm(x[0]);v,f=numeric(x[col])
    # Chinese enumerated categories are the top level. Arabic subcategories and '其中' are excluded.
    category=re.match(r'^[一二三四五六七八九十百]+[、.．，,]',label) if chinese_categories else re.match(r'^\d+[、.．，,]',label)
    if category:components.append(dict(row=i,column=col+1,label=x[0],raw=x[col],value='' if v is None else str(v),format=f))
    if re.fullmatch(r'[一二三四五六七八九十]+[、.．，,]税收收入',label):tax.append(v)
    if re.fullmatch(r'[一二三四五六七八九十]+[、.．，,]非税收入',label):non_tax.append(v)
   nonblank=[c for c in components if c['format']!='blank'];all_components_valid=all(c['value']!='' for c in nonblank)
   total=sum((Decimal(c['value']) for c in nonblank),Decimal(0)) if nonblank and all_components_valid else None
   # Blank categories are not filled; partial sum is evidence, not proof of missing=zero.
   max_quantum=Decimal('.01') if unit=='亿元' else Decimal(1)
   rounding_tolerance=sum((min(max_quantum,Decimal(10)**Decimal(c['value']).as_tuple().exponent)/2 for c in nonblank if c['value']!=''),Decimal(0))+(min(max_quantum,Decimal(10)**value.as_tuple().exponent)/2 if value is not None else Decimal(0))
   closure= value is not None and total is not None and abs(value-total)<=rounding_tolerance
   ty= value/Decimal(10000) if value is not None and unit=='万元' else (value if unit=='亿元' else None)
   s=compiled.get((r['data_year'],r['province']));sv=numeric(s['raw_value'])[0] if s else None
   diff=ty-sv if ty is not None and sv is not None else None
   agree=diff is not None and abs(diff)<=Decimal('.005')
   status='pending'
   if r['province']=='重庆' and int(r['data_year'])<1997:status='inapplicable_pre_1997_province'
   elif not unit:status='unit_pending'
   elif value is None:status='numeric_format_pending'
   elif not final_headers:status='final_column_header_pending'
   elif not closure:status='component_closure_pending'
   elif not agree:status='source_version_or_value_pending'
   elif counts[(r['data_year'],r['province'])]>1:status='multiple_blocks_pending_selection'
   else:status='accepted_source_internal_numeric'
   approved=str(ty) if status=='accepted_source_internal_numeric' else ''
   if r['record_id'] in decisions:
    d=decisions[r['record_id']]
    if d['adjudication_status'].startswith('approved'):
     approved=d['adjudicated_yi'];status=d['adjudication_status']
    else:status=d['adjudication_status'];approved=''
   eid=r['record_id']
   evidence.append(dict(evidence_id=eid,source_id=sid,table=spec['table'],sheet=spec['sheet'],table_sha256=spec['table_sha256'],block_start_row=start+1,headers=header,unit_cells=unit_hits,final_column_headers=final_headers,top_level_components=components,observed_components_sum='' if total is None else str(total),component_rounding_tolerance=str(rounding_tolerance),raw_total=r['raw_value'],tax_and_non_tax_values=[str(v) if v is not None else '' for v in tax+non_tax]))
   results.append(dict(record_id=eid,source_id=sid,year=r['data_year'],province=r['province'],cell=r['cell'],raw_value=r['raw_value'],format_status=fmt,parsed_candidate='' if value is None else str(value),original_registered_unit=r['unit'],verified_unit=unit,normalized_candidate_yi='' if ty is None else str(ty),observed_component_count=len(nonblank),blank_component_count=len(components)-len(nonblank),component_closure=('pass_exact' if value==total else 'pass_rounding') if closure else 'pending',final_column_header_verified=bool(final_headers),compiled_R='' if sv is None else str(sv),difference_yi='' if diff is None else str(diff),numeric_status=status,adjudicated_R_yi=approved,province_year_candidate_count=counts[(r['data_year'],r['province'])],scope_status='whole_province_scope_pending; own_revenue_separate_from_transfers',model_eligible=False,evidence_id=eid))
  if index%100==0:print('source sheets checked',index,flush=True)
 write('R_numeric_verification.csv',results)
 (OUT/'R_original_header_component_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
 receipt=dict(records=len(results),statuses=dict(collections.Counter(r['numeric_status'] for r in results)),formats=dict(collections.Counter(r['format_status'] for r in results)),verified_unit_count=sum(bool(r['verified_unit']) for r in results),original_inputs_sha256={n:hashlib.sha256((SRC/n).read_bytes()).hexdigest() for n in ['fiscal_original_candidates.csv','supplement_original_candidates.csv','source_registry.csv']})
 (OUT/'numeric_verification_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(receipt,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
