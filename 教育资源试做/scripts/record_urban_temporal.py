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
visual_hash=hashlib.sha256((ROOT/'教育资源试做.html').read_bytes()).hexdigest()
assert visual_hash=='51b2140d8576491cf1c1629f628278edf6e65674b3b352ec4569fe6ba3d7ed06'
text='''

## 15. 城乡分类深化：逐年方向、固定构成与财政衔接边界（2026年10月7日）

用户授权在第14节基础上继续分析。共同窗口仍为2018—2024年，两学段、三个按学校所在地汇总的公布类别；不增加模型、不新增可视化、不更换研究对象。重点检验第14节结论是否依赖最新一年，并区分不同期间及构成控制下的比值变化。

### 15.1 城区小学持续增长、乡村小学持续收缩，初中不能简单照搬

2018—2023五次年度变化中，城区小学学生、教师、班级每年均增加；乡村小学三者每年均减少。加入2024年后仍是六年均如此。这补充了端点累计比较：两个类别相反的数量方向并非仅由个别年造成。但这是公布类别中的净变化，不能识别真实人员调动或地域重分类。

镇区小学五次变化中学生4次增、1次减；教师5次增，班级4次增、1次减，班级与学生方向一致。乡村初中五次学生变化4次减、1次增，而教师5次减；班级4次减、1次增。这意味着教师、班级、学段仍不能合并为同一种“资源响应”。计数仅说明观察方向，不给统计显著性、调整弹性或滞后年限。

### 15.2 三个类别都提高，全国比值却下降

下表均为小学“班级数/百名学生”的当年减上年差值，而不是班级数同比。方向由原始整数交叉相乘核验，未靠四舍五入判定。

{reversal}

2019、2021、2022年，三个类别内部的比值均提高，全国却下降。全国比值是以学生份额加权的类别比值，权重变化可以产生这种相反方向。由全国比值下降直接断言“各地班级配置压缩”会与分类内观察不符。相反，也不能因类别内比值上升断言班级绝对数全部增加：乡村学生与班级数量可能同时减少，但学生下降更快。

### 15.3 长期分解：2024年的94.09%不是通用解释率

下表使用第14节相同的对称恒等分解，并另将每次年度分解的项累计。每百名学生的比值变化为单位。端点分解只看期初期末，年度累计保留中间变化路径；总变化相同，但两项分配未必相同，二者不应混用。

{periods}

2018—2023小学班级/学生比全国下降0.04683，而端点分类内部项为+0.09081，分类构成项为−0.13764；2018—2024同样是内部项为正、构成项为负且绝对值更大。长期全国下降与内部加权项提高并存。因此2024年两个项均为负、构成项占94.09%的说法不能外推到全期。长期若以“构成项÷全国净变化”计算，会超过100%，原因是两项相互抵消；不把这种比例解释为贡献份额、因果解释率或模型拟合度。

初中教师也依时期不同：2018—2023全国教师/学生比小幅下降，分类构成项约−0.03403，内部项接近零（−0.00082）；2023—2024下降则以内部项（−0.07354）为主。第14节“初中分类内部项占主要部分”只指2024年当年，不是整个2018年以来。年度累计分解方向与上述端点判断一致，但数值分配存在路径差异；例如2018—2024小学班级构成项端点−0.16188，年度累计−0.16360。

### 15.4 七套固定份额核验：小学班级长期方向保持相反

将全国比值按固定的三个学生分类份额重新加权，分别采用2018—2024每一年的份额，共七套，而非仅选有利的基期。各年类别内部资源/学生比保留实际值。该标准化只固定类别权重，不固定类别所包含的学校或地域，也不是“学生不迁移时”的政策反事实，不生成虚构学生数或班级数。

{standard}

2018—2023及2018—2024小学班级/学生比在七套固定份额下均提高，而实际全国比值均下降，方向判断不依赖选择哪一年作权重。2023—2024小学班级固定份额变化较小，但七套均为负（−0.00244至−0.00156），不能把长期正向判断移到这一年。初中教师2018—2023的固定份额变化范围跨零，不能据全国轻微下降认为各类别内部存在统一的减师密度方向；2018—2024及2023—2024的固定份额变化则均为负。

### 15.5 与财政的可衔接层级：全国同年并列，暂不做城乡投入解释

本轮使用既有已核验2022、2023经费公告，不宣称这是截至今日全部可用年份。按全国同学段并列2023年资源变化与已发布生均指标，六项经费同比复算与公告四舍五入值一致；无同口径调整标记。原件来源及年末资源来源保留在新增底表。

{finance}

两学段2023年末学生都增加，而名义生均一般公共预算教育经费也增加，不能将这一年的生均上升写为“年末学生减少带来的分母红利”。这只是排除一个不符合当年年末观察的叙述，不证明真实财政统计的分母增加，也不能推出总支出增速。已核查的小学财政生均分母说明涉及年初/年末加权，但完整权重及覆盖未核准；初中的完整分母说明仍未核准，不能由小学答复外推。学生分类份额也不能视为财政分母的城乡构成。

现有经费长表的观察键为年×省份/全国×学段×指标，没有城区、镇区、乡村维度，不能把同一全国生均数复制给三个类别，不能用省级指标解释全国城乡差异；两类资料无法形成城乡支出面板。教育事业费、公用经费仍不是可相加或相减的互斥分项，不用它们推算“人员费”。本节无CPI调整、无城乡经费总额重构、无财政机制回归。

### 15.6 核验、成果与下一步判断

固定份额标准化共196项，以有理数重新计算，最大差异约8.88×10⁻¹⁶；28项当年权重下标准化值等于全国实际比值。12项方向反转用原始整数验证；对应2018—2022小学学生/班级40个总量单元格回查原件及SHA256均一致。12组时期端点和年度累计分解总和均还原比值差，最大恒等误差约7.77×10⁻¹⁶。计算复核由同一分析者完成，不称独立评审。原件、既有主体、空白及可视化均未改动。

新增 `urban_direction_persistence.csv`、`urban_temporal_ratio_changes.csv`、`urban_fixed_composition.csv`、`urban_period_decomposition.csv`、`urban_standardized_period_changes.csv`、`urban_temporal_summary.json`；核验 `urban_fixed_weight_checks.csv`、`urban_reversal_source_checks.csv`、`urban_reversal_exact_signs.csv`、`urban_temporal_validation.json`；财政并列 `national_finance_resource_parallel_2023.csv`。复现：`deepen_urban_analysis.py` → `verify_urban_temporal.py` → `record_urban_temporal.py`。最后一步记录本节，已存在则拒绝重复。

当前叙事可以形成“学段不同步—同学段分类内方向不同—全国平均受分类构成影响—真实投入调整仍需同口径财政证据”的连续逻辑。人口变化仍是原研究问题，现有在校生及分类数量只是生源观察；构成核验不能代替人口或财政机制。继续增加全国分类描述的边际价值已下降，下一步优先核验同学段支出总额和完整财政分母、能识别地域分类变化的资料。常规来源查找可继续；如转县域/学校个案或实质收窄研究对象，应先准备资料覆盖与选择依据并汇报，不凭全国分类数字擅自选择“错配地区”。
'''.replace('{reversal}','\n'.join(reversal_table)).replace('{periods}','\n'.join(period_table)).replace('{standard}','\n'.join(standard_table)).replace('{finance}','\n'.join(finance_table))
report=ROOT/'试做报告.md';old=report.read_text(encoding='utf-8');assert '## 15. 城乡分类深化' not in old
notice='最新分析进度：第14—15节已补充全国城乡分类、逐年及固定构成核验（2026年10月7日）；下述开篇保留第一轮判断，不能据此忽略后续对全国平均与财政解释边界的修订。原题及未完成人口/财政资料缺口保持，新增结果尚未进入旧交互图。\n\n'
old=old.replace('## 结论与选题判断\n\n','## 结论与选题判断\n\n'+notice,1)
report.write_text(old+text,encoding='utf-8')
handoff=ROOT.parent/'选题试做交接_教育资源与财政投入.md'
note='''

### 2026年10月7日城乡深化：逐年与固定构成核验
用户要求继续，已完成报告第15节，不新增可视化。2019、2021、2022小学三个类别班级/百学生比均提高，全国却下降，原始整数方向及相关40个总量单元格回查一致。2018—2023、2018—2024小学班级比的分类内部项为正、构成项为负；七套固定份额标准化均提高而实际全国降低。2024的94.09%只限当年该对称分解，不作长期因果解释率；长期两项抵消可导致比例超过100%。初中教师2018—2023内部项接近零、构成项占主要部分，2024当年则内部项主要，解释须保留期间。
196项固定份额有理数核验、12项精确方向检查、12组时期分解通过。2023全国资源与六项生均财政指标并列，复算匹配公告；小学/初中当年年末学生及生均一般预算教育经费均增，不能说由年末学生减少带来生均增长，更不能用不明加权分母反推总额。城乡没有对应财政分类，不复制全国生均值制造城乡经费面板。成果与复现顺序见第15.6节。
下一步优先财政真实总额/分母及地域分类桥接来源核验；常规任务继续获授权。改变为县校个案或收窄核心对象应先提出资料及选择依据，待用户决断。适龄人口、财政总额、完整分母仍未完成，原题不变。
'''
handoff.write_text(handoff.read_text(encoding='utf-8')+note,encoding='utf-8')
print(json.dumps({'standardized_periods':standard_changes,'finance_parallel_rows':len(parallel),'visual_sha256_unchanged':visual_hash},ensure_ascii=False))
