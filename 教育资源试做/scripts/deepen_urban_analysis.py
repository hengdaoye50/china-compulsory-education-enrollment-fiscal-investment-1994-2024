"""Temporal robustness and fixed-composition descriptive standardization."""
import csv,json,math,hashlib
from parse import ROOT,save_csv
rows=list(csv.DictReader((ROOT/'data/national_urban_rural_panel.csv').open(encoding='utf-8-sig')))
data={}
for r in rows:
    data[int(r['year']),r['stage'],r['category']]={m:int(r[m]) if r[m] else None for m in ['students','teachers','classes']}
cats=['城区','镇区','乡村']
def ratio(year,stage,cat,metric):
    r=data[year,stage,cat]
    return 100*r[metric]/r['students'] if r[metric] is not None else None
def weights(year,stage):
    return [data[year,stage,c]['students']/data[year,stage,'全国']['students'] for c in cats]
def sign(x):return 0 if abs(x)<1e-12 else 1 if x>0 else -1

annual=[];standard=[];periods=[];identities=[];persist=[]
for stage in ['primary','junior']:
    for metric in ['teachers','classes']:
        for year in range(2018,2025):
            actual=ratio(year,stage,'全国',metric)
            for base in range(2018,2025):
                fixed=sum(w*ratio(year,stage,c,metric) for w,c in zip(weights(base,stage),cats))
                standard.append({'year':year,'stage':stage,'metric':metric,'weight_year':base,'actual_ratio':actual,'fixed_composition_ratio':fixed,'difference':actual-fixed,'unit':metric+' per 100 students'})
        for year in range(2019,2025):
            a,b=year-1,year;wa,wb=weights(a,stage),weights(b,stage)
            ra=[ratio(a,stage,c,metric) for c in cats];rb=[ratio(b,stage,c,metric) for c in cats]
            within=sum((x+y)/2*(v-u) for x,y,u,v in zip(wa,wb,ra,rb))
            composition=sum((u+v)/2*(y-x) for x,y,u,v in zip(wa,wb,ra,rb))
            actual=ratio(b,stage,'全国',metric)-ratio(a,stage,'全国',metric)
            changes=[v-u for u,v in zip(ra,rb)]
            annual.append({'year':year,'stage':stage,'metric':metric,'actual_change':actual,'within_component':within,'composition_component':composition,'urban_change':changes[0],'town_change':changes[1],'rural_change':changes[2],'national_vs_within_opposite':sign(actual)*sign(within)<0,'all_category_same_direction':len(set(sign(x) for x in changes))==1,'unit':metric+' per 100 students'})
            identities.append(abs(actual-within-composition))
        for a,b in [(2018,2023),(2018,2024),(2023,2024)]:
            wa,wb=weights(a,stage),weights(b,stage);ra=[ratio(a,stage,c,metric) for c in cats];rb=[ratio(b,stage,c,metric) for c in cats]
            actual=ratio(b,stage,'全国',metric)-ratio(a,stage,'全国',metric)
            within=sum((x+y)/2*(v-u) for x,y,u,v in zip(wa,wb,ra,rb))
            composition=sum((u+v)/2*(y-x) for x,y,u,v in zip(wa,wb,ra,rb))
            sel=[r for r in annual if r['stage']==stage and r['metric']==metric and a<int(r['year'])<=b]
            aw=sum(r['within_component'] for r in sel);ac=sum(r['composition_component'] for r in sel)
            periods.append({'begin':a,'end':b,'stage':stage,'metric':metric,'actual_change':actual,'endpoint_within':within,'endpoint_composition':composition,'annual_sum_within':aw,'annual_sum_composition':ac,'endpoint_composition_share_of_total_pct':100*composition/actual if actual else None,'annual_composition_share_of_total_pct':100*ac/actual if actual else None,'unit':metric+' per 100 students'})
            identities.extend([abs(actual-within-composition),abs(actual-aw-ac)])
        for c in cats:
            for a,b in [(2018,2023),(2018,2024)]:
                ds=[];dr=[]
                for y in range(a+1,b+1):
                    ds.append(sign(data[y,stage,c]['students']-data[y-1,stage,c]['students']))
                    dr.append(sign(data[y,stage,c][metric]-data[y-1,stage,c][metric]))
                persist.append({'begin':a,'end':b,'stage':stage,'category':c,'metric':metric,'years':b-a,'student_increase_years':ds.count(1),'student_decrease_years':ds.count(-1),'resource_increase_years':dr.count(1),'resource_decrease_years':dr.count(-1),'opposite_direction_years':sum(x*y<0 for x,y in zip(ds,dr))})
assert max(identities)<1e-12
save_csv(ROOT/'data/urban_fixed_composition.csv',standard)
save_csv(ROOT/'data/urban_temporal_ratio_changes.csv',annual)
save_csv(ROOT/'data/urban_period_decomposition.csv',periods)
save_csv(ROOT/'data/urban_direction_persistence.csv',persist)
summary={'periods':periods,'national_vs_within_opposite':[r for r in annual if r['national_vs_within_opposite']],'maximum_identity_error':max(identities),'fixed_weight_years':list(range(2018,2025)),'classification_scope':'Annual published category membership, not fixed geography. Fixed weights hold only category student shares constant.','status':'Descriptive standardization, not an estimate of policy counterfactuals or migration.'}
(ROOT/'data/urban_temporal_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
