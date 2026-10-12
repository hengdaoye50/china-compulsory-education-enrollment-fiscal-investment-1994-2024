"""Recheck Tibet source totals and representative holdout fits via QR."""
import csv,json,math,re,hashlib,statistics
from pathlib import Path
import numpy as np
from parse import ROOT,read,save_csv
DATA=ROOT/'data'
schemas=json.loads((DATA/'resource_schemas.json').read_text(encoding='utf-8'))
raw=list(csv.DictReader(open(DATA/'education_resource_panel.csv',encoding='utf-8-sig')))
checks=[];trajectory=[]
for year in range(2013,2025):
    r=next(r for r in raw if r['stage']=='primary' and r['province']=='西藏' and r['year']==str(year))
    out={'stage':'primary','province':'西藏','year':year}
    for kind in ['students','teachers','classes']:
        s=next(s for s in schemas if s['year']==year and s['stage']=='primary' and s['kind']==kind)
        table=read(ROOT/s['path'])
        row=next(row for t in table.tables for row in t if row and re.sub(r'\s','',row[0]).startswith('西藏'))
        value=int(row[s['columns'][kind]])
        assert value==int(r[kind])
        out[kind]=value;out[kind+'_source']=s['source']
        checks.append({'year':year,'stage':'primary','province':'西藏','metric':kind,'raw_value':row[s['columns'][kind]],
                       'column_index':s['columns'][kind],'panel_value':int(r[kind]),'equal':True,
                       'source':s['source'],'path':s['path'],'sha256':hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest()})
    if year>2013:
        prev=trajectory[-1]
        for kind in ['students','teachers','classes']:out[kind+'_change_pct']=100*(out[kind]-prev[kind])/prev[kind]
    trajectory.append(out)
save_csv(DATA/'tibet_primary_source_checks.csv',checks);save_csv(DATA/'tibet_primary_trajectory.csv',trajectory)
rows=list(csv.DictReader(open(DATA/'full_grade_model_inputs.csv',encoding='utf-8-sig')))
preds=list(csv.DictReader(open(DATA/'grade_holdout_predictions.csv',encoding='utf-8-sig')))
PROVINCES=['北京','天津','河北','山西','内蒙古','辽宁','吉林','黑龙江','上海','江苏','浙江','安徽','福建','江西','山东','河南','湖北','湖南','广东','广西','海南','重庆','四川','贵州','云南','西藏','陕西','甘肃','青海','宁夏','新疆']
qr_checks=[]
for stage in ['primary','junior']:
    rr=[r for r in rows if r['stage']==stage]
    ps=[p for p in PROVINCES if any(r['province']==p for r in rr)];ys=sorted({int(r['year']) for r in rr})
    # Reconstruct fold 0 of partition 0 from input keys, not saved train matrices.
    def fold(r):return ((int(r['year'])-2015)//2+PROVINCES.index(r['province']))%5
    train=[r for r in rr if fold(r)!=0];test=[r for r in rr if fold(r)==0]
    count=6 if stage=='primary' else 4
    fs=['students_change_pct','students_lag_change_pct']+[period+'_grade'+str(i)+'_contribution_pp' for period in ['current','previous'] for i in range(1,count)]
    def matrix(rs):return np.array([[1]+[int(r['province']==p) for p in ps[1:]]+[int(int(r['year'])==t) for t in ys[1:]]+[float(r[f]) for f in fs] for r in rs],dtype=float)
    x=matrix(train);xt=matrix(test);q,upper=np.linalg.qr(x,mode='reduced')
    for target in ['teachers','classes']:
        y=np.array([float(r[target+'_change_pct']) for r in train]);coef=np.linalg.solve(upper,q.T@y)
        predicted=xt@coef
        saved={(r['province'],int(r['year'])):float(r['predicted_change_pct']) for r in preds if r['stage']==stage and r['scenario']=='main' and r['split']=='block_offset_0' and r['fold']=='0' and r['resource']==target and r['model']=='full_grade_added'}
        diffs=[abs(float(p)-saved[r['province'],int(r['year'])]) for r,p in zip(test,predicted)]
        assert max(diffs)<1e-10
        qr_checks.append({'stage':stage,'resource':target,'split':'block_offset_0','fold':0,'n':len(test),'max_prediction_difference':max(diffs),'pass':True})
audit=json.loads((DATA/'grade_deep_validation.json').read_text(encoding='utf-8'))
audit['tibet_source_totals_checked']=len(checks)
audit['tibet_source_checks']='12 years × primary students, teachers, classes; all local official-file values match panel.'
audit['representative_independent_solver_checks']={'method':'QR solve; four full-grade heldout fits (two stages × two resources), reconstructed from input keys','checks':qr_checks}
# Report-layout checks belong to the separate local report workflow.
(DATA/'grade_deep_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'source_checks':len(checks),'qr_checks':qr_checks,'tibet_trajectory':trajectory},ensure_ascii=False,indent=2))
