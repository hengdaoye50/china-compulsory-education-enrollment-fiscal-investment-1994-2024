"""Compare original final-account candidates with compiled R; no automatic overrides."""
from pathlib import Path
from decimal import Decimal,InvalidOperation
import csv,json,collections,hashlib
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'research/data/长期财政数据建设_20261010'
OUT=ROOT/'research/data/口径核准_20261010'
def read(n):
 with (SRC/n).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
 fiscal=[r for r in read('fiscal_original_candidates.csv') if r['metric']=='R_fiscal_candidate']
 supp={(r['data_year'],r['province']):r for r in read('supplement_original_candidates.csv') if r['metric']=='R'}
 source={r['source_id']:r for r in read('source_registry.csv')}
 counts=collections.Counter((r['data_year'],r['province']) for r in fiscal);rows=[]
 for r in fiscal:
  s=supp.get((r['data_year'],r['province']));value=None;difference=None
  if r['numeric_candidate'] and r['unit'] in ['万元','亿元']:
   value=Decimal(r['numeric_candidate'])/(Decimal(10000) if r['unit']=='万元' else Decimal(1))
  if value is None:status='original_numeric_or_unit_pending'
  elif not s or not s['numeric_candidate']:status='compiled_value_missing'
  else:
   difference=value-Decimal(s['numeric_candidate'])
   status='agree_within_0.005_yi' if abs(difference)<=Decimal('.005') else 'difference_requires_scope_or_revision_check'
  src=source[r['source_id']]
  rows.append(dict(year=r['data_year'],province=r['province'],original_record_id=r['record_id'],original_source_id=r['source_id'],archive=src['archive'],table=src['table'],sheet=src['sheet'],cell=r['cell'],label=r['original_label'],raw_value=r['raw_value'],original_unit=r['unit'],normalized_yi='' if value is None else str(value),compiled_record_id='' if not s else s['record_id'],compiled_raw_value='' if not s else s['raw_value'],difference_yi='' if difference is None else str(difference),candidate_blocks_for_province_year=counts[(r['data_year'],r['province'])],comparison_status=status,approval='comparison_only; geography, whole-province scope and source revision pending',model_eligible=False))
 with (OUT/'fiscal_R_crosschecks.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 decisions=[]
 explicit=[('2007','河北','D41','','rejected_wrong_geography','first block English title TIANJIN; revenue 5404390, central transfers 2031835 and remittance 380257 match separate Tianjin table'),
 ('2007','河北','D95','789.1198','approved_own_revenue_numeric','second block title HEBEI; units 万元; final-account column; converted 7891198/10000; compiled 789.12 agrees to rounding'),
 ('2013','云南','D29','1611.30','approved_cell_reconstruction','taxes 1215.66 + non-tax 395.64 = 1611.30; official 2013 audit report: https://audit.yn.gov.cn/html/2014/sjgzbgjjd-zwgk_0725/536.html'),
 ('2013','湖北','D29','2191.22','approved_cell_reconstruction','taxes 1604.85 + non-tax 586.37 = 2191.22; later official statistical yearbook confirms historical value: https://tjj.hubei.gov.cn/tjsj/sjkscx/tjnj/gsztj/ycs/201911/P020250321349385581778.pdf'),
 ('2013','江苏','D29','6568.46','approved_official_final_report_backreference','2014 final-account report page 1: 2014 revenue 7233.14 increased by 664.68 over prior year; derived 2013=6568.46. Same-year official execution report confirms 6568.46; table tax+non-tax differ by 0.01, retained as rounding/component issue. Evidence: https://czt.jiangsu.gov.cn/webpic/P020150902630701696959.pdf')]
 for y,p,c,v,status,basis in explicit:
  matches=[r for r in rows if (r['year'],r['province'],r['cell'])==(y,p,c)];assert len(matches)==1
  d=dict(matches[0]);d.update(adjudicated_yi=v,adjudication_status=status,evidence=basis);decisions.append(d)
 with (OUT/'fiscal_R_adjudications.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(decisions[0]));w.writeheader();w.writerows(decisions)
 receipt=dict(original_candidates=len(rows),province_year_groups=len(counts),multiple_candidate_groups=sum(v>1 for v in counts.values()),comparison_status=dict(collections.Counter(r['comparison_status'] for r in rows)),inputs_sha256={n:hashlib.sha256((SRC/n).read_bytes()).hexdigest() for n in ['fiscal_original_candidates.csv','supplement_original_candidates.csv']})
 (OUT/'fiscal_R_crosscheck_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
