"""Build urban standardization summaries and national finance/resource parallels."""
import csv,json,hashlib
from parse import ROOT,save_csv
def load(name):return list(csv.DictReader((ROOT/'data'/name).open(encoding='utf-8-sig')))
periods=load('urban_period_decomposition.csv');fixed=load('urban_fixed_composition.csv')
annual=load('urban_temporal_ratio_changes.csv');persistence=load('urban_direction_persistence.csv')
finance=load('finance_long.csv');core={(int(r['year']),r['province'],r['stage']):r for r in load('education_resource_panel.csv')}
fm={(int(r['year']),r['province'],r['stage'],r['metric']):r for r in finance}
stages={'primary':'小学','junior':'初中'};metrics={'teachers':'教师/百名学生','classes':'班级/百名学生'}
period_table=['|时期|学段|比值|全国实际变化|分类内部项|分类构成项|逐年分解累计的构成项|','|---|---|---|---:|---:|---:|---:|']
for r in periods:
    period_table.append(f"|{r['begin']}—{r['end']}|{stages[r['stage']]}|{metrics[r['metric']]}|{float(r['actual_change']):+.5f}|{float(r['endpoint_within']):+.5f}|{float(r['endpoint_composition']):+.5f}|{float(r['annual_sum_composition']):+.5f}|")
standard_table=['|时期|学段|比值|全国实际变化|七套固定分类份额下变化范围|','|---|---|---|---:|---:|'];standard_changes=[]
for a,b in [(2018,2023),(2018,2024),(2023,2024)]:
    for s in ['primary','junior']:
        for m in ['teachers','classes']:
            changes=[]
            for base in range(2018,2025):
                v={int(r['year']):float(r['fixed_composition_ratio']) for r in fixed if r['stage']==s and r['metric']==m and int(r['weight_year'])==base}
                changes.append(v[b]-v[a])
            actual=next(float(r['actual_change']) for r in periods if int(r['begin'])==a and int(r['end'])==b and r['stage']==s and r['metric']==m)
            standard_changes.append({'begin':a,'end':b,'stage':s,'metric':m,'actual_change':actual,'minimum_standardized_change':min(changes),'maximum_standardized_change':max(changes),'all_positive':all(v>0 for v in changes),'all_negative':all(v<0 for v in changes)})
            standard_table.append(f"|{a}—{b}|{stages[s]}|{metrics[m]}|{actual:+.5f}|{min(changes):+.5f} 至 {max(changes):+.5f}|")
save_csv(ROOT/'data/urban_standardized_period_changes.csv',standard_changes)
reversal_table=['|年份|全国班级/百名学生变化|城区变化|镇区变化|乡村变化|','|---|---:|---:|---:|---:|']
for r in annual:
    if r['stage']=='primary' and r['metric']=='classes' and r['year'] in ['2019','2021','2022']:
        reversal_table.append('|'+r['year']+'|'+'|'.join(f"{float(r[k]):+.5f}" for k in ['actual_change','urban_change','town_change','rural_change'])+'|')
parallel=[];finance_table=['|学段|2023年末学生同比|专任教师同比|班级同比|生均一般公共预算教育经费同比|','|---|---:|---:|---:|---:|']
for s in ['primary','junior']:
    a,b=core[2022,'全国',s],core[2023,'全国',s]
    resource={m:100*(int(b[m])/int(a[m])-1) for m in ['students','teachers','classes']}
    for m in ['budget_per_student','career_per_student','public_per_student']:
        fa,fb=fm[2022,'全国',s,m],fm[2023,'全国',s,m]
        assert fb['scope_break']=='False'
        growth=100*(float(fb['value'])/float(fa['value'])-1)
        assert round(growth,2)==float(fb['published_growth_pct'])
        parallel.append({'year':2023,'stage':s,'metric':m,'previous_value':fa['value'],'value':fb['value'],'growth_pct':growth,'published_growth_pct':fb['published_growth_pct'],'scope_break':fb['scope_break'],'source':fb['source'],'previous_source':fa['source'],**{m+'_growth_pct':v for m,v in resource.items()},'students_source':b['students_source'],'teachers_source':b['teachers_source'],'classes_source':b['classes_source'],'join_scope':'Same published year and nationwide stage only; finance denominator is not year-end enrollment.'})
    bg=next(r['growth_pct'] for r in parallel if r['stage']==s and r['metric']=='budget_per_student')
    finance_table.append(f"|{stages[s]}|{resource['students']:+.2f}%|{resource['teachers']:+.2f}%|{resource['classes']:+.2f}%|{bg:+.2f}%|")
save_csv(ROOT/'data/national_finance_resource_parallel_2023.csv',parallel)

print(json.dumps({'standardized_periods':standard_changes,'finance_parallel_rows':len(parallel)},ensure_ascii=False))
