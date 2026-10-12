"""Recompute approvals and matching counts using the saved cell evidence."""
import json, csv, hashlib
from pathlib import Path
from decimal import Decimal
from build_PC_scope_layer import ROOT, OUT, BASE, read, number

def main():
    checks=read(OUT/'PC_original_numeric_checks.csv')
    evidence={r['evidence_id']:r for r in json.loads((OUT/'PC_original_evidence.json').read_text(encoding='utf8'))}
    panel=read(OUT/'SPCR_numeric_availability.csv')
    receipt=json.loads((OUT/'receipt.json').read_text(encoding='utf8'))
    valid=True
    for r in checks:
        if not r['numeric_status'].startswith('accepted'): continue
        e=evidence[r['evidence_id']]
        assert e['unit_cells'] and r['all_source_title_verified']=='True'
        ns={m:number(next(c['raw_value'] for c in e['cells'] if c['metric']==m)) for m in ['E','P','C','K']}
        if r['numeric_status']=='accepted_source_internal_only':
            valid &= all(v is not None for v in ns.values()) and abs(ns['E']-ns['P']-ns['C']-ns['K'])<=Decimal(r['tolerance'])
        else:
            for m in ['P','C']:
                cc=e['PC_component_checks'][m]
                valid &= cc['headers_verified'] and all(c['numeric'] for c in cc['cells']) and abs(ns[m]-sum(Decimal(c['numeric']) for c in cc['cells']))<=Decimal('1.5')
    pc_only={r['evidence_id'] for r in checks if r['numeric_status']=='accepted_PC_components_EK_pending'}
    validation=dict(approved_numeric_evidence_recomputed=bool(valid),unique_1860_positions=len(panel)==len({(r['year'],r['province'],r['stage']) for r in panel})==1860,all_school_PC_1240=sum(bool(r['P_thousand_yuan']) for r in panel)==1240,SPCR_1216=sum(r['numeric_fields_present']=='True' for r in panel)==1216,no_E_admission_from_PC_only=all(not r['E_thousand_yuan'] for r in panel if any(e in pc_only for e in r['finance_evidence_ids'].split('|'))),all_model_eligibility_false=all(r['model_eligible']=='False' for r in panel),inputs_unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in receipt['input_hashes'].items()))
    output=dict(checks=validation,passed=all(validation.values()))
    (OUT/'validation_receipt.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf8')
    assert output['passed'],output
    print(json.dumps(output,ensure_ascii=False))

if __name__=='__main__':main()
