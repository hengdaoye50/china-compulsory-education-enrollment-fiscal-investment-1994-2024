from parse import *
import math,statistics
data=json.loads((ROOT/'data/panel.json').read_text(encoding='utf-8'))
idx={(r['year'],r['province'],r['stage']):r for r in data}
fiscal=list(csv.DictReader(open(ROOT/'data/fiscal_2024_manual.csv',encoding='utf-8')))
for r in fiscal:
    for k in ['revenue_100m','expenditure_100m','nbs_education_expenditure_100m']:r[k]=float(r[k])
    r['revenue_expenditure_ratio']=r['revenue_100m']/r['expenditure_100m']
    r['year']=2024;r['source_revenue']='https://www.stats.gov.cn/sj/ndsj/2025/html/C07-05.jpg';r['source_expenditure']='https://www.stats.gov.cn/sj/ndsj/2025/html/C07-06.jpg'
    r['method']='人工转录已保存官方图表；分省合计对表头总数；收入/支出为结构代理'
for field,expected in [('revenue_100m',119272.24),('expenditure_100m',243885.39),('nbs_education_expenditure_100m',40414.50)]:
    actual=round(sum(r[field] for r in fiscal),2);print('fiscal check',field,actual,expected,actual-expected)
    assert abs(actual-expected)<0.06
save_csv(ROOT/'data/fiscal_2024.csv',fiscal)
fm={r['province']:r for r in fiscal}
changes=[];decomp=[];national=[];phase=[];finance_changes=[]
for st in ['primary','junior']:
    for y in range(2013,2025):
        r=idx[y,'全国',st];b=idx[2013,'全国',st]
        for metric,label in [('students','在校生'),('entrants','招生'),('teachers','专任教师'),('classes','班级')]:national.append(dict(year=y,stage=st,series=label,index=100*r[metric]/b[metric],value=r[metric],source=r[('students' if metric in ['students','entrants'] else metric)+'_source']))
    for p in fm:
        a=idx[2023,p,st];b=idx[2024,p,st]
        changes.append(dict(province=p,stage=st,year=2024,student_change=b['students_growth_pct'],teacher_change=b['teachers_growth_pct'],class_change=b['classes_growth_pct'],entrant_change=b['entrants_growth_pct'],students_2024=b['students'],teachers_2024=b['teachers'],classes_2024=b['classes'],fiscal_ratio_pct=100*fm[p]['revenue_expenditure_ratio'],source_students=b['students_source'],source_teachers=b['teachers_source'],source_classes=b['classes_source'],source_revenue=fm[p]['source_revenue'],source_expenditure=fm[p]['source_expenditure']))
        ct=100*math.log(b['teachers']/a['teachers']);cs=-100*math.log(b['students']/a['students'])
        decomp.append(dict(province=p,stage=st,teacher_contribution_logpoints=ct,student_denominator_contribution_logpoints=cs,total_logpoints=ct+cs,teacher_density_before=100*a['teachers']/a['students'],teacher_density_after=100*b['teachers']/b['students']))
    for ph in ['收缩','增长']:
        rows=[r for r in data if r['province']!='全国' and r['stage']==st and r.get('demand_phase')==ph]
        phase.append(dict(stage=st,phase=ph,n=len(rows),median_student_growth=statistics.median(r['students_growth_pct'] for r in rows),median_teacher_growth=statistics.median(r['teachers_growth_pct'] for r in rows),median_class_growth=statistics.median(r['classes_growth_pct'] for r in rows),teacher_rise_count=sum(r['teachers_growth_pct']>0 for r in rows),class_rise_count=sum(r['classes_growth_pct']>0 for r in rows)))
    for p in fm:
        a=idx[2022,p,st];b=idx[2023,p,st]
        finance_changes.append(dict(province=p,stage=st,student_change=b['students_growth_pct'],budget_per_student_change=100*(b['budget_per_student']/a['budget_per_student']-1),career_per_student_change=100*(b['career_per_student']/a['career_per_student']-1),public_per_student_change=100*(b['public_per_student']/a['public_per_student']-1),budget_per_student_2023=b['budget_per_student'],public_per_student_2023=b['public_per_student'],source=b['budget_per_student_source'],source_students=b['students_source'],source_previous_budget=a['budget_per_student_source']))
def corr(xs,ys):
    ax=statistics.mean(xs);ay=statistics.mean(ys);return sum((x-ax)*(y-ay) for x,y in zip(xs,ys))/math.sqrt(sum((x-ax)**2 for x in xs)*sum((y-ay)**2 for y in ys))
summary={'phase':phase,'2024':{},'fiscal_associations':{}}
for st in ['primary','junior']:
    rs=[r for r in changes if r['stage']==st];a=idx[2023,'全国',st];b=idx[2024,'全国',st]
    summary['2024'][st]={m:b[m+'_growth_pct'] for m in ['students','entrants','teachers','classes']}
    summary['2024'][st].update(student_shrink_provinces=sum(r['student_change']<0 for r in rs),teacher_rise_with_shrink=sum(r['student_change']<0 and r['teacher_change']>0 for r in rs),class_rise_with_shrink=sum(r['student_change']<0 and r['class_change']>0 for r in rs),teacher_density_change_pct=100*((b['teachers']/b['students'])/(a['teachers']/a['students'])-1),density_teacher_logpoints=100*math.log(b['teachers']/a['teachers']),density_denominator_logpoints=-100*math.log(b['students']/a['students']))
    summary['fiscal_associations'][st]={'n':len(rs),'correlation_fiscal_ratio_teacher_change':corr([r['fiscal_ratio_pct'] for r in rs],[r['teacher_change'] for r in rs]),'correlation_student_teacher_change':corr([r['student_change'] for r in rs],[r['teacher_change'] for r in rs])}
for name,rows in [('national_index',national),('changes_2024',changes),('teacher_density_decomposition',decomp),('growth_shrink_phase',phase),('finance_changes_2023',finance_changes)]:save_csv(ROOT/'data'/f'{name}.csv',rows)
(ROOT/'data/findings.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
