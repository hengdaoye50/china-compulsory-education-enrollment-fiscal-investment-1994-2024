"""Validate the separate fourth-stage revenue layer against retained evidence."""
import csv, json, hashlib
from pathlib import Path
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'research/data/财政收入补核_20261010'
BASE = ROOT / 'research/data/财政收入核准_20261010'

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def main():
    panel = read(OUT / 'R_province_year_numeric_panel_with_summaries.csv')
    previous = read(BASE / 'R_province_year_numeric_panel.csv')
    idx = {(r['year'], r['province']): r for r in panel}
    wrapped = read(OUT / 'wrapped_R_adjudications.csv')
    evidence = {r['record_id']: r for r in json.loads((OUT / 'wrapped_R_evidence.json').read_text(encoding='utf8'))}
    summaries = read(OUT / 'annual_summary_R_checks.csv')
    sources = json.loads((OUT / 'annual_summary_R_original_evidence.json').read_text(encoding='utf8'))
    sourceidx = {r['source_id']: r for r in sources}
    checks = {}
    checks['unique_930_positions'] = len(panel) == len(idx) == 930
    checks['historical_inapplicability'] = {(r['year'], r['province']) for r in panel if r['numeric_status'] == 'inapplicable_pre_1997_province'} == {('1995', '重庆'), ('1996', '重庆')}
    checks['all_selected_positive'] = all(Decimal(r['R_adjudicated_yi']) > 0 for r in panel if r['R_adjudicated_yi'])
    checks['all_model_admission_false'] = all(r['model_eligible'] == 'False' for r in panel)
    checks['previous_662_values_preserved'] = all(idx[(r['year'], r['province'])]['R_adjudicated_yi'] == r['R_adjudicated_yi'] for r in previous if r['R_adjudicated_yi'])
    waccepted = [r for r in wrapped if r['status'] == 'accepted_wrapped_column_numeric_only']
    checks['wrapped_97_evidence_recomputed'] = len(waccepted) == 97 and all(
        sum((Decimal(c['proposed']) for c in evidence[r['record_id']]['components']), Decimal(0)) == Decimal(r['proposed_total'])
        and not evidence[r['record_id']]['invalid_cells']
        and abs(Decimal(r['adjudicated_R_yi']) - Decimal(r['compiled_R'])) <= Decimal('.005')
        and idx[(r['year'], r['province'])]['R_adjudicated_yi'] == r['adjudicated_R_yi']
        for r in waccepted)
    saccepted = [r for r in summaries if r['state'] == 'new_numeric_approval']
    def summary_valid(r):
        source = sourceidx[r['source_id']]
        sheet = next(s for s in source['sheets'] if s['sheet'] == r['sheet'])
        raw = sheet['rows'][int(r['source_row']) - 1][int(r['source_column']) - 1]
        units = json.loads(r['unit_cell_evidence'])
        return (str(raw) == r['raw_value'] and units
                and all(sheet['rows'][u['row'] - 1][u['column'] - 1] == u['raw'] and '亿元' in str(u['raw']) for u in units)
                and abs(Decimal(r['numeric_yi']) - Decimal(r['compiled_R'])) <= Decimal('.005')
                and idx[(r['year'], r['province'])]['R_adjudicated_yi'] == r['numeric_yi'])
    checks['summary_94_original_coordinates_verified'] = len(saccepted) == 94 and all(summary_valid(r) for r in saccepted)
    baseline_hash = json.loads((OUT / 'receipt.json').read_text(encoding='utf8'))['baseline_sha256']
    checks['third_stage_panel_unchanged'] = hashlib.sha256((BASE / 'R_province_year_numeric_panel.csv').read_bytes()).hexdigest() == baseline_hash
    protected = json.loads((ROOT / 'research/data/长期财政数据建设_20261010/build_receipt.json').read_text(encoding='utf8'))['protected_hashes']
    checks['four_protected_outputs_unchanged'] = all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in protected.items())
    coverage = read(OUT / 'coverage_with_summaries.csv')
    checks['annual_coverage_recomputed'] = all(int(r['selected']) == sum(bool(p['R_adjudicated_yi']) for p in panel if p['year'] == r['year']) for r in coverage)
    selected = sum(bool(r['R_adjudicated_yi']) for r in panel)
    checks['selected_853_pending_75'] = selected == 853 and 928 - selected == 75
    receipt = dict(checks=checks, selected=selected, pending_applicable=928-selected, passed=all(checks.values()))
    (OUT / 'validation_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    assert receipt['passed'], receipt
    print(json.dumps(receipt, ensure_ascii=False))

if __name__ == '__main__':
    main()
