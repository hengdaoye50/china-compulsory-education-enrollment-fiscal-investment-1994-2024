"""Record authorized grade analysis and the next decision point; no visuals."""
import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'
def load(n):return list(csv.DictReader(open(DATA/n,encoding='utf-8-sig')))
labels={'primary':'小学','junior':'初中','teachers':'教师','classes':'班级'}
national=[r for r in load('grade_contributions.csv') if r['province']=='全国' and r['year']=='2024']
national_table=[]
for stage in ['primary','junior']:
    r=next(r for r in national if r['stage']==stage)
    for kind,label in [('students','在校生'),('classes','班级')]:
        national_table.append('|'+ '|'.join([labels[stage],label,*[f"{float(r[k]):+.3f}" for k in [kind+'_change_pct',kind+'_first_grade_contribution_pp',kind+'_remainder_contribution_pp']]])+'|')
first=load('grade_structure_model_increment.csv');full=load('full_grade_model_increment.csv');influence=load('full_grade_increment_influence.csv')
first_table=[];full_table=[]
for r in first:
    if r['scenario']!='main_2015_2024':continue
    first_table.append('|'+ '|'.join([labels[r['stage']],labels[r['resource']],r['n'],f"{float(r['delta_within_r_squared']):+.4f}",f"{float(r['delta_within_adjusted_r_squared']):+.4f}"])+ '|')
for r in full:
    if r['scenario']!='main_2015_2024':continue
    vals=[float(x['delta_within_adjusted_r_squared']) for x in influence if x['stage']==r['stage'] and x['resource']==r['resource']]
    excluded=next(x for x in full if x['stage']==r['stage'] and x['resource']==r['resource'] and x['scenario']=='exclude_2024')
    full_table.append('|'+ '|'.join([labels[r['stage']],labels[r['resource']],r['n'],f"{float(r['delta_within_adjusted_r_squared']):+.4f}",f"{float(excluded['delta_within_adjusted_r_squared']):+.4f}",f'{min(vals):+.4f}至{max(vals):+.4f}'])+'|')
section='''## 12. 年级结构分析结果与第二个待决策节点（2026年10月6日）

用户已授权沿第11节路径A继续。本轮完成年级贡献、总量模型与结构模型的同样本比较、完整年级敏感性和逐省影响检查，未新增可视化。原选题不变。下文区分算术构成与解释模型的增益，不把二者等同。

### 12.1 无需填补空白的主分解

定义一年级学生为原表一年级在校生，非一年级学生为同口径总在校生减一年级人数。后者是由两个已发布总量计算的合计，不是把空白四年级或六年级填零，也不分别推定空白年级人数。班级作相同分解；小学“其余班级”明确包含复式班，不把它等同于二至六年级单年级班数。

年度变化贡献（百分点）=100×本类别本年与上年人数之差÷上年本学段总人数。两类贡献之和精确等于总人数同比，班级使用上年本学段总班数作分母。两类贡献共用分母，可相加；不是各类别自身的增长率，也不是对总量变化的因果贡献。

2014—2024年31省两学段的682条年度观察均可作该分解，另有22条全国年度观察。全部704条学生、班级分解的恒等式核验通过。逐年级分解另保留空白：小学学生338/341条、班级308/341条，初中学生267/341条、班级271/341条具有完整相邻两年字段；不完整观察仅不作全等级求和，仍可进入一年级与总量剩余的主分解。

|学段|指标|2024年总量变化（%）|一年级贡献（百分点）|其余部分贡献（百分点）|
|---|---|---:|---:|---:|
'''+ '\n'.join(national_table)+'''

小学在校生总量减少，但非一年级学生合计略增，说明总量方向不能代表所有年级。2024年小学26个学生总量下降地区中，12个非一年级学生合计增加、14个减少；31个地区一年级学生均减少。初中27个总量增长地区中，23个一年级与其余年级同时增加，4个一年级增加而其余合计减少；4个总量下降地区中，3个一年级仍增加。上述是完整31省的方向统计，不是选择个别案例。

“非一年级合计增加”也不能理解为所有高年级都增加。2024年全国小学二年级贡献+1.616个百分点、六年级+0.020，三至五年级贡献分别为−0.760、−0.212、−0.578，合计抵消后才得到非一年级+0.086个百分点。年级结构具有描述价值，但新入学人数、在校一年级人数和适龄人口仍是不同指标。

### 12.2 一年级区分的增益有限

以2015—2024年每学段31省×10年=310条相同观察比较两个模型：基线包含当年和上年总学生同比、省份固定项、年份固定项；扩展加入当年和上年一年级对总学生变化的贡献。教师、班级同比分别为结果变量。加入一年级贡献但不同时加入其余贡献，避免“总量=一年级+其余”引起完全共线。

本轮统一使用普通同比百分比与算术贡献，第10节用的是对数变化；二者并非同一模型。本轮所有基线与扩展比较使用相同变化定义、样本、固定项和结果变量，不跨第10节的R²作增益比较。

新增系数表示总学生同比相同时，变化更多来自一年级而更少来自其余年级的条件关联，不表示一年级人数的独立因果作用。由于加入变量通常增加样本内R²，同时报告扣除模型自由度的调整后增益。调整后R²按去除固定项后的方差计算，增益单位为R²数值，不是学生或资源增长的百分点，也不是总体规模解释率。

|学段|资源|样本数|样本内R²增益|调整后R²增益|
|---|---|---:|---:|---:|
'''+ '\n'.join(first_table)+'''

小学班级有小幅正向增益，教师及初中两资源的主样本调整后增益为负。分时段后也不呈现统一改善，因此“一年级与其余”的粗分组尚不能承担主要资源解释。

### 12.3 完整年级模型没有消除主要限制

为避免因粗分组过早否定结构作用，使用当年和上年的所有单年级贡献作补充模型，只纳入三个连续年度所需字段均有原值的观察。小学剩306条、初中233条，共539条，排除81条，其中小学4条、初中77条。排除集中于部分早期省—年，不能把完整年级结果直接与主样本31省310条视为同一观察总体。

完整年级贡献之和等于总学生同比，故保留总同比并将小学六年级、初中四年级作为参照，分别只加入其余5个或3个年级的当年和上年贡献。系数是相对参照年级的条件差异，不能将某系数排序写为各年级的治理重要性。基线与扩展仍在完全相同的完整观察上比较。样本不平衡，使用显式省份和年份固定项求解，不使用仅适用于平衡面板的简单双重去均值。

|学段|资源|主样本数|调整后R²增益|剔除2024年后的增益|逐省删除后的增益范围|
|---|---|---:|---:|---:|---:|
'''+ '\n'.join(full_table)+'''

小学班级的附加拟合在逐省删除和剔除2024年后维持正值，是可继续核查的关联线索。小学教师主样本增益为+0.0290，但删除西藏观察后为−0.0148，说明该拟合改善依赖样本构成；这不表示西藏资料错误，也不授权以结果不合预期为由删除它。初中教师调整后增益为负，班级增益接近零且在逐省删除时跨零。

年级之间及当年、上年指标高度相关。控制固定项后，小学四年级当年贡献与三年级上年贡献相关约0.990，初中二年级当年与一年级上年贡献约0.981。模型可以求解不代表各系数具有稳定的独立解释。当前所有拟合增益都是样本内结果，没有样本外预测验证，没有显著性检验，也未证明“年级结构导致资源调整”。

### 12.4 核验与交付状态

主分解704条恒等式通过；全等级完整观察求和通过。主模型32次、逐省删除248次，全部检查样本平衡、设计矩阵秩，并以显式固定项核对去均值模型系数，最大差异约8.31×10⁻¹⁵。完整年级模型及逐省删除共264次，检查相同基线/扩展样本、设计秩和最小二乘方程。上述属于计算核验，不是独立研究者审查。

新增数据和复现：

- `grade_contributions.csv`、`grade_detailed_contributions.csv`：一年级/其余分解和逐年级贡献，保留来源。
- `grade_structure_analysis_coverage.csv`：可用观察覆盖。
- `grade_structure_model_inputs.csv`、`grade_structure_models.csv`、`grade_structure_model_increment.csv`及对应`*_influence.csv`：主结构模型与敏感性。
- `full_grade_model_inputs.csv`、`full_grade_model_exclusions.csv`、`full_grade_models.csv`、`full_grade_model_increment.csv`及对应`*_influence.csv`：完整年级比较与排除清单。
- `grade_structure_analysis_validation.json`、`full_grade_model_validation.json`：来源文件校验与计算核验。

复现顺序：`analyze_grade_structure.py` → `check_full_grade_models.py` → `record_grade_results.py`，需NumPy。既有资源主体、原件与空白未修改；交互报告未更新，不能据旧图声称展示了本节结果。

### 12.5 新的关键节点：下一阶段如何分配分析工作

已获得较稳的需求结构描述，以及值得保留的小学班级关联线索；尚未获得能统一解释两个学段、两种资源的年级机制。原题保留人口变化与财政投入，不能因年级拟合局部增加而把原题改写为年级配置研究，也不能把结构分解当人口变化的直接测量。

建议下一轮优先转向**全国城乡分类的口径核验与描述比较**，保留本轮年级结果作为需求结构部分。理由是继续增加相关年级变量的解释收益不确定，而已有全国城乡原件可能补充新的结构维度；仍需先验证分类与教师覆盖，不预先声称城乡差异解释了省级结果。

另一条选择是继续深化省级年级路径，重点检查小学班级关联的时期稳定性、教师模型的省份影响及样本外表现；目前不据此收窄研究对象为小学，也不把西藏默认移出主样本。

依用户的关键节点汇报要求，**本轮止于上述结果与建议，等待用户决定下一阶段优先方向后再执行。** 不开展城乡分析、不继续增加结构模型或制作可视化来绕过这个等待点。财政总额、完整加权分母和适龄人口未完成状态保持，下一阶段不能以这些尚缺资料作为实证结论。
'''
report=ROOT/'试做报告.md';old=report.read_text(encoding='utf-8');marker='## 12. 年级结构分析结果'
if marker in old:old=old[:old.index(marker)].rstrip()
report.write_text(old.rstrip()+'\n\n'+section,encoding='utf-8')
handoff=ROOT.parent/'选题试做交接_教育资源与财政投入.md';old=handoff.read_text(encoding='utf-8');marker='### 2026年10月6日年级分析：第二个待决策节点'
if marker in old:old=old[:old.index(marker)].rstrip()
handoff.write_text(old.rstrip()+'''\n\n### 2026年10月6日年级分析：第二个待决策节点
用户已批准沿省级年级结构继续，本轮完成，无可视化更新。2024小学总学生−2.322%，一年级贡献−2.409个百分点，其余+0.086；26个总量下降省份中12个非一年级合计增加。年级结构揭示需求内部差异，但资源附加解释有限：一年级粗分组增益弱；完整年级小学班级调整后R²增益+0.0205，在删省检查仍为正；小学教师增益+0.0290，删西藏后−0.0148；初中教师无调整后增益。指标高度相关，不能作独立效应或机制认定。详见报告第12节和grade_*、full_grade_*底表、核验。
待用户决断：建议下一轮先核验全国城乡分类、保留年级为需求结构描述；或继续深化省级年级路径（小学班级关联与教师样本影响）。原题不变，不预先缩窄为小学或删除西藏。依此前关键节点要求，未经新决定不进入城乡分析或增加模型；不更新可视化。财政/适龄人口资料仍未补齐。
''',encoding='utf-8')
audit=json.loads((DATA/'grade_structure_analysis_validation.json').read_text(encoding='utf-8'))
audit['offline_report_sha256']=hashlib.sha256((ROOT/'教育资源试做.html').read_bytes()).hexdigest()
assert audit['offline_report_sha256']=='51b2140d8576491cf1c1629f628278edf6e65674b3b352ec4569fe6ba3d7ed06'
audit['next_stage']='Await user choice: national urban-rural audit or deeper provincial grade analysis.'
(DATA/'grade_structure_analysis_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('Grade findings, limits and next checkpoint recorded; offline report unchanged.')
