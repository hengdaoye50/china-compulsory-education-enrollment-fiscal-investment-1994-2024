"""Use explicitly unit-labelled provincial final-revenue summary tables as separate sources."""
import csv,json,re,hashlib,collections
from decimal import Decimal
from pathlib import Path
from inspect_bridge_evidence import CAT,sheets,getbytes
from repair_wrapped_R_checks import proposed,norm,read,write,OUT,BASE,ROOT
def main():
 panel=read(OUT/'R_province_year_numeric_panel.csv');idx={(r['year'],r['province']):r for r in panel};provinces={r['province'] for r in panel}
 compiled={(r['data_year'],r['province']):r for r in read(ROOT/'research/data/长期财政数据建设_20261010/supplement_original_candidates.csv') if r['metric']=='R'}
 sources=[];checks=[];added=0
 for a in CAT:
  if a['family']!='中国财政年鉴' or '财政收入完成预算情况' not in a['table'] or '国有资产管理' in a['table']:continue
  matches=re.findall(r'(?:19|20)\d{2}',Path(a['table']).name)
  if len(set(matches))!=1:continue
  year=matches[0]
  if not 1995<=int(year)<=2024:continue
  digest=hashlib.sha256(getbytes(a)).hexdigest();sid='annual_R_'+digest[:20]
  ss=sheets(a)
  sources.append(dict(**a,source_id=sid,sha256=digest,sheets=[dict(sheet=n,rows=rs) for n,rs in ss]))
  for name,rr in ss:
   headers=rr[:10];unit=[dict(row=i,column=j,raw=v) for i,x in enumerate(headers,1) for j,v in enumerate(x,1) if '单位' in norm(v) and '亿元' in norm(v)]
   finalcols={j for x in headers for j,v in enumerate(x) if norm(v) in ['决算数','决算数FinalAccount']}
   if len(finalcols)!=1:continue
   col=next(iter(finalcols))
   for row,x in enumerate(rr,1):
    if not x:continue
    names=[p for p in provinces if norm(x[0]).startswith(p)]
    if len(names)!=1 or len(x)<=col:continue
    p=names[0];v,fmt=proposed(x[col]);c=compiled.get((year,p));cv=proposed(c['raw_value'])[0] if c else None
    current=idx[(year,p)];old=Decimal(current['R_adjudicated_yi']) if current['R_adjudicated_yi'] else None
    agree=v is not None and cv is not None and abs(v-cv)<=Decimal('.005')
    old_agree=v is not None and old is not None and abs(v-old)<=Decimal('.005')
    accepted=bool(unit) and v is not None and v>0 and agree and old is None and current['numeric_status']!='inapplicable_pre_1997_province'
    state='new_numeric_approval' if accepted else ('confirms_existing_selected' if unit and old_agree else ('unit_missing' if not unit else 'retained_comparison'))
    checks.append(dict(year=year,province=p,source_id=sid,table=a['table'],sheet=name,source_row=row,source_column=col+1,raw_value=x[col],numeric_yi='' if v is None else str(v),unit_status='explicit_亿元' if unit else 'missing',unit_cell_evidence=json.dumps(unit,ensure_ascii=False),final_column=col+1,compiled_R='' if cv is None else str(cv),previous_selected_R='' if old is None else str(old),state=state,model_eligible=False))
    if accepted:
     added+=1;current['R_adjudicated_yi']=str(v);current['numeric_status']='accepted_annual_summary_crosscheck';current['source_ids']+='|'+sid;current['source_record_ids']+=f'|{sid}:{name}:{row}:{col+1}';current['selection_basis']='annual province final-revenue summary; explicit 亿元 and 决算数 column; compiled independent agreement; own detailed table status retained separately'
 write('annual_summary_R_checks.csv',checks);write('R_province_year_numeric_panel_with_summaries.csv',panel)
 (OUT/'annual_summary_R_original_evidence.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf8')
 coverage=[]
 for y in range(1995,2025):
  rs=[r for r in panel if r['year']==str(y)];coverage.append(dict(year=y,applicable=30 if y<1997 else 31,selected=sum(bool(r['R_adjudicated_yi']) for r in rs),pending_provinces='|'.join(r['province'] for r in rs if not r['R_adjudicated_yi'] and r['numeric_status']!='inapplicable_pre_1997_province')))
 write('coverage_with_summaries.csv',coverage)
 receipt=dict(summary_tables=len(sources),summary_province_rows=len(checks),new_accepted=added,total_selected=sum(bool(r['R_adjudicated_yi']) for r in panel),summary_statuses=dict(collections.Counter(r['state'] for r in checks)),panel_statuses=dict(collections.Counter(r['numeric_status'] for r in panel)))
 (OUT/'summary_crosscheck_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(receipt,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
