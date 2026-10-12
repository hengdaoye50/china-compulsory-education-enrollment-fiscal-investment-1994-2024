import csv,json,hashlib
from fractions import Fraction
from parse import ROOT,read,save_csv
def load(name):return list(csv.DictReader((ROOT/'data'/name).open(encoding='utf-8-sig')))
panel={(int(r['year']),r['stage'],r['category']):r for r in load('national_urban_rural_panel.csv')}
fixed=load('urban_fixed_composition.csv');checks=[]
for r in fixed:
    y=int(r['year']);base=int(r['weight_year']);s=r['stage'];metric=r['metric']
    fraction=sum(Fraction(int(panel[base,s,c]['students']),int(panel[base,s,'全国']['students']))*Fraction(100*int(panel[y,s,c][metric]),int(panel[y,s,c]['students'])) for c in ['城区','镇区','乡村'])
    error=abs(float(fraction)-float(r['fixed_composition_ratio']))
    assert error<1e-12
    if base==y:assert abs(float(fraction)-float(r['actual_ratio']))<1e-12
    checks.append({'year':y,'stage':s,'metric':metric,'weight_year':base,'difference':error})
cells=load('national_urban_rural_cells.csv');raw_checks=[]
for cell in cells:
    if cell['year'] not in ['2018','2019','2020','2021','2022'] or cell['stage']!='primary' or cell['metric'] not in ['students','classes']:continue
    table=read(ROOT/cell['path']).tables[int(cell['table_index'])]
    actual=int(table[int(cell['row_index'])][int(cell['column_index'])].replace(',',''))
    assert actual==int(cell['value'])
    raw_checks.append({'year':cell['year'],'category':cell['category'],'metric':cell['metric'],'value':actual,'source':cell['source'],'path':cell['path'],'digest_matches':hashlib.sha256((ROOT/cell['path']).read_bytes()).hexdigest()==cell['sha256']})
sign_checks=[]
for y in [2019,2021,2022]:
    for c in ['全国','城区','镇区','乡村']:
        a,b=panel[y-1,'primary',c],panel[y,'primary',c]
        numerator=int(b['classes'])*int(a['students'])-int(a['classes'])*int(b['students'])
        expected=-1 if c=='全国' else 1
        actual=1 if numerator>0 else -1 if numerator<0 else 0
        assert actual==expected
        sign_checks.append({'year':y,'category':c,'exact_integer_numerator':numerator,'ratio_change_sign':actual})
save_csv(ROOT/'data/urban_fixed_weight_checks.csv',checks)
save_csv(ROOT/'data/urban_reversal_source_checks.csv',raw_checks)
save_csv(ROOT/'data/urban_reversal_exact_signs.csv',sign_checks)
validation={'fraction_standardization_checks':len(checks),'max_difference':max(r['difference'] for r in checks),'raw_cells_rechecked':len(raw_checks),'exact_sign_checks':len(sign_checks),'source_digest_mismatches':sum(not r['digest_matches'] for r in raw_checks),'limitations':'Alternative arithmetic check by same analyst; category membership remains annual, not fixed geography.'}
(ROOT/'data/urban_temporal_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(validation,ensure_ascii=False))
