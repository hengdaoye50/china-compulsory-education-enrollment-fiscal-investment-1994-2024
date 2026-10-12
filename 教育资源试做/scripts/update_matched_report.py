import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def rows(name):
    rs=list(csv.DictReader(open(ROOT/'data'/name,encoding='utf-8-sig')))
    for r in rs:
        for k,v in r.items():
            try:r[k]=float(v)
            except (ValueError,TypeError):pass
    return rs
pairs=rows('matched_pairs.csv');summary=rows('matched_phase_summary.csv')
links=list(dict.fromkeys(v for r in pairs for k,v in r.items() if 'source' in k))
src={'title':'同省同学段、相近生源变化幅度的描述性配对','provider':'教育部公开教育事业统计；本项目计算','files':[{'name':n,'path':'../data/'+n} for n in ['matched_pairs.csv','matched_phase_summary.csv','matched_sensitivity.csv','matched_validation.json']],'links':[{'label':u.split('/')[-1],'url':u} for u in links],'description':'2026年10月6日基于已核验的2013—2024年资源面板计算；原件下载日期维持原记录。','evidenceFlow':[{'title':'观察定义','detail':'2014—2024年同比；在校生增长≥1%或收缩≤−1%。'},{'title':'配对规则','detail':'同省同学段；绝对幅度差≤1个百分点；年份差≤4年；每条观察最多使用一次。先最大化配对数，再最小化幅度差总和、年份差总和。'},{'title':'复核','detail':'64对、128条不重复观察；约束检查通过；选中变化率由原始两年水平重新计算一致。'}],'caveats':['仅128/539条达到幅度门槛的观察进入主配对样本，不能代表所有地区。','不同年份的政策、人口结构与资源基数仍可能不同；不构成因果识别。','年度在校生变化是生源观察指标，不能直接替代适龄人口变化。','教师在收缩期增减的符号对阈值与2024年敏感。']}
for path in [ROOT/'snapshot.json',ROOT/'visual-report/src/data.json']:
    data=json.loads(path.read_text(encoding='utf-8'))
    data['queries']['matched_phase_summary']={'rows':summary,'source':src}
    data['queries']['matched_pairs']={'rows':pairs,'source':src}
    data['buildStatus']='complete'
    data['asOf']='2026-10-06'
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
p=ROOT/'visual-report/src/content/report/Education.jsx'
s=p.read_text(encoding='utf-8')
s=s.replace(" const sums=national", " const matched=reviewedRows('matched_phase_summary').filter(r=>r.stage===stage);\n const matchedRows=matched.flatMap(r=>[['在校生',r.median_students_pct],['专任教师',r.median_teachers_pct],['班级',r.median_classes_pct]].map(([series,value])=>({phase:`${r.phase}（${r.n}对，${r.provinces}省）`,series,'变化中位数 (%)':value})));\n const sums=national")
s=s.replace('公开数据试做 · 下载核验日期 2026年10月4日','公开数据试做 · 原件下载核验 2026年10月4日 · 配对分析更新 2026年10月6日')
anchor="  {text('denominator-copy'"
addition="""  {text('matched-copy','### 相近幅度下，同一地区的两种阶段\n同省、同学段内，学生增长≥1%与收缩≤−1%的观察按绝对幅度配对：幅度差≤1个百分点、年份差≤4年，每条观察只用一次。小学29对覆盖18省，初中35对覆盖22省；共128条观察进入配对，占539条达到幅度门槛观察的23.7%。比较的是选中样本的变化率中位数。\n\n小学教师增长期中位数+2.29%，收缩期−0.05%；班级分别+1.59%、−1.53%。剔除2024年后，小学收缩期教师中位数变为+0.48%；初中收缩期教师的增减方向也随门槛变化。这提示班级与教师应分别考察，但尚不能确认稳定的调整不对称机制。不同年份的政策和资源基数仍未控制。')}
  <EvidenceChart id="matched-phase-medians" queryId="matched_phase_summary" title={`${label}同省相近幅度配对：增长与收缩观察`} spec={{type:'bar',x:'phase',y:'变化中位数 (%)',series:'series',stackable:false,colors,valueDecimals:2,yLabel:'同比变化中位数（%）'}} rows={matchedRows} sourceRows={matched} height={340}/>
"""
# Preserve JS string escaping for multiline prose.
addition=addition.replace('### 相近幅度下，同一地区的两种阶段\n','### 相近幅度下，同一地区的两种阶段\\n').replace('变化率中位数。\n\n','变化率中位数。\\n\\n')
s=s.replace(anchor,addition+anchor)
old='建议保留方向，收窄为**生源变化下，师资与班级调整路径为何不同，小学与初中为何不同步**。下一步核实城乡、举办者、经费分母，再比较同一地区相近幅度的增长与收缩期。'
new='保留原选题**人口变化下的教育资源与财政投入调整**。本轮资源子问题以在校生变化观察生源变化，尚未直接测量适龄人口。已完成同省相近幅度配对；下一步补充适龄人口、城乡与举办者口径，以及财政支出总额和完整分母说明。'
s=s.replace(old,new)
s=s.replace('经费分母与事业统计学生的完整覆盖一致性尚未确证','教育部2023年答复说明，小学生均预算经费采用年初、年末在校生加权平均分母；权重与完整覆盖一致性尚未确证')
p.write_text(s,encoding='utf-8')
audit=json.loads((ROOT/'data/matched_validation.json').read_text(encoding='utf-8'))
text='''

## 9. 第二轮探索：同省相近生源幅度配对（2026年10月6日）

原选题仍为“人口变化下的教育资源与财政投入调整”。本轮仅处理资源子问题：以在校生年度变化观察生源变化，不能直接替代适龄人口。未补齐分学段财政总额及完整分母说明，因此未开展财政总投入分解。

配对范围为2014—2024年，同省、同学段的增长（≥1%）与收缩（≤−1%）观察，绝对幅度差不超过1个百分点、年份差不超过4年；观察不重复使用。算法依次最大化配对数、最小化幅度差总和、最小化年份差总和，完全并列时按年度顺序确定。主样本64对、128条观察，仅占539条达到幅度门槛观察的23.7%；小学18省29对，初中22省35对。没有两种阶段或无法满足约束的地区不进入配对。

|学段|阶段|学生变化中位数|教师变化中位数|班级变化中位数|
|---|---|---:|---:|---:|
|小学|增长|+1.73%|+2.29%|+1.59%|
|小学|收缩|−1.78%|−0.05%|−1.53%|
|初中|增长|+2.44%|+0.80%|+2.26%|
|初中|收缩|−2.29%|−0.17%|−0.88%|

将幅度差改为0.5或2个百分点、年份差改为3年，或剔除2024年后，小学增长期教师中位数均高于收缩期；但收缩期教师是否减少不稳定：剔除2024年，小学变为+0.48%，初中变为+0.02%。所有这四种敏感性方案下，两个学段班级变化中位数均表现为增长期为正、收缩期为负。以上仅说明选中样本的描述模式，不能证明教师调整迟滞、资源错配或效率损失。

配对减少地区构成和变化幅度差异，但仍跨年份，未控制同期政策、资源基数、城乡结构等。同省可以出现多对，观察之间并非独立；本轮不提供显著性检验，也不将组中位数差视作因果效应。

新增底表：`data/matched_pairs.csv`（含两期与前期逐字段官方来源）、`data/matched_phase_summary.csv`、`data/matched_sensitivity.csv`。`data/matched_validation.json`记录配对约束、去重与原始水平复算核验，均通过。交互报告新增可切换学段的配对图，来源菜单提供上述资料。
'''
report=ROOT/'试做报告.md'
report.write_text(report.read_text(encoding='utf-8')+text,encoding='utf-8')
handoff=ROOT.parent/'选题试做交接_教育资源与财政投入.md'
handoff.write_text(handoff.read_text(encoding='utf-8')+'\n\n### 2026年10月6日续做\n已完成同省同学段相近生源变化幅度配对，小学29对、初中35对；敏感性分析表明收缩期教师增减方向不稳定。详见试做报告第9节和新增配对底表；原选题保持不变。待补适龄人口与财政细表，不能以事业统计年末学生数直接还原财政总投入。\n',encoding='utf-8')
print('Updated report, handoff, snapshot and reviewed chart data.')
