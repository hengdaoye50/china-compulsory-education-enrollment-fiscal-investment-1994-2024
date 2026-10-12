"""Select a unique numeric layer; source conflicts remain visible and no model admission."""
from pathlib import Path
import csv,json,collections,hashlib
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/data/财政收入核准_20261010'
def read(n):
 with (OUT/n).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(n,rows):
 with (OUT/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 rs=read('R_numeric_verification.csv');groups=collections.defaultdict(list)
 for r in rs:groups[(r['year'],r['province'])].append(r)
 provinces=['北京','天津','河北','山西','内蒙古','辽宁','吉林','黑龙江','上海','江苏','浙江','安徽','福建','江西','山东','河南','湖北','湖南','广东','广西','海南','重庆','四川','贵州','云南','西藏','陕西','甘肃','青海','宁夏','新疆']
 panel=[]
 for y in range(1995,2025):
  for p in provinces:
   g=groups.get((str(y),p),[]);selected='';status='pending';basis=''
   accepted=[r for r in g if r['adjudicated_R_yi']!='']
   if p=='重庆' and y<1997:status='inapplicable_pre_1997_province'
   elif not g:status='no_extracted_final_account_candidate'
   elif len(accepted)==1:
    selected=accepted[0]['adjudicated_R_yi'];status='accepted_numeric';basis=accepted[0]['numeric_status']
   elif len(g)>1 and all(r['numeric_status']=='multiple_blocks_pending_selection' for r in g) and len({Decimal(r['normalized_candidate_yi']) for r in g})==1:
    selected=g[0]['normalized_candidate_yi'];status='accepted_numeric_repeated_table_consensus';basis='all candidate tables independently pass units, final headers, component closure and compiled comparison; retain all source IDs'
   elif y==2024 and len(g)==1 and g[0]['numeric_status']=='source_version_or_value_pending':
    r=g[0]
    assert r['component_closure'].startswith('pass_') and r['final_column_header_verified']=='True' and r['verified_unit']
    selected=r['normalized_candidate_yi'];status='accepted_numeric_final_account_variant';basis='original final-account header and component closure verified; compiled alternative retained; not an OCR repair or automatic compiled overwrite'
   if selected:assert Decimal(selected)>0
   panel.append(dict(year=y,province=p,R_adjudicated_yi=selected,numeric_status=status,compiled_R='' if not g else g[0]['compiled_R'],source_record_ids='|'.join(r['record_id'] for r in g),source_ids='|'.join(r['source_id'] for r in g),selection_basis=basis,scope_status='whole_province_scope_and_cross_year_budget_scope_pending',model_eligible=False))
 write('R_province_year_numeric_panel.csv',panel)
 coverage=[]
 for y in range(1995,2025):
  rows=[r for r in panel if r['year']==y]
  coverage.append(dict(year=y,target_slots=31,applicable_slots=sum(r['numeric_status']!='inapplicable_pre_1997_province' for r in rows),numeric_selected=sum(bool(r['R_adjudicated_yi']) for r in rows),pending_provinces='|'.join(r['province'] for r in rows if not r['R_adjudicated_yi'] and r['numeric_status']!='inapplicable_pre_1997_province'),model_admitted=0))
 write('R_numeric_coverage_by_year.csv',coverage)
 checks={'target_930':len(panel)==930,'province_year_unique':len({(r['year'],r['province']) for r in panel})==930,'two_pre_1997_inapplicable':sum(r['numeric_status']=='inapplicable_pre_1997_province' for r in panel)==2,'all_selected_positive':all(Decimal(r['R_adjudicated_yi'])>0 for r in panel if r['R_adjudicated_yi']),'no_model_admission':all(not r['model_eligible'] for r in panel)}
 assert all(checks.values())
 receipt=dict(checks=checks,statuses=dict(collections.Counter(r['numeric_status'] for r in panel)),numeric_selected=sum(bool(r['R_adjudicated_yi']) for r in panel),pending_applicable=sum(not r['R_adjudicated_yi'] and r['numeric_status']!='inapplicable_pre_1997_province' for r in panel),input_sha256=hashlib.sha256((OUT/'R_numeric_verification.csv').read_bytes()).hexdigest())
 (OUT/'R_panel_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
