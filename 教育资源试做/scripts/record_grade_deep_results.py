"""Record deeper grade findings, including correction to in-sample interpretation."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'
def load(n):return list(csv.DictReader(open(DATA/n,encoding='utf-8-sig')))
inc=load('grade_holdout_increment.csv');allocation=load('grade_in_sample_province_gain.csv')
labels={'primary':'小学','junior':'初中','teachers':'教师','classes':'班级'}
table=[]
for stage in ['primary','junior']:
    for resource in ['teachers','classes']:
        rr=[r for r in inc if r['stage']==stage and r['resource']==resource and r['scenario']=='main' and r['model']=='full_grade_added']
        bysplit={r['split']:r for r in rr};a,b=bysplit['block_offset_0'],bysplit['block_offset_2']
        table.append('|'+ '|'.join([labels[stage],labels[resource],a['n'],f"{float(a['baseline_rmse_pp']):.3f} → {float(a['rmse_pp']):.3f}",
                                   f"{float(b['baseline_rmse_pp']):.3f} → {float(b['rmse_pp']):.3f}",
                                   f"{min(-float(r['mae_improvement_pct']) for r in rr):.2f}%至{max(-float(r['mae_improvement_pct']) for r in rr):.2f}%"])+ '|')
tibet=next(r for r in allocation if r['stage']=='primary' and r['resource']=='teachers' and r['province']=='西藏')
section='''## 13. 年级路径深化：留出检验与教师敏感性（2026年10月6日）

用户在第12节节点明确要求“继续深化”。本轮沿年级路径核验已有结果，不新增可视化。重点从样本内拟合转为留出资源结果的检验，并回查西藏原始数值。结果收紧了第12节对小学班级拟合改善的解释：它是可复核的样本内关联，尚未转化为稳定的留出误差降低。

### 13.1 留出设计的用途和边界

比较已经使用的三种模型：总生源当年/上年变化基线、一年级贡献扩展、完整年级扩展；不挑选新的变量、惩罚参数或“最佳”划分。统一使用完整年级可用样本（小学306条、初中233条），三模型样本、结果、固定项和变化定义完全一致。以省份官方顺序与相邻两年时间块建立五折划分，再按预先设定的第二种偏移规则作敏感性检查。每省的连续两年观察同折，年级字段缺失造成的排除仍保留在此前清单。

每折将约五分之一省—年资源结果留出，其余观察估计省份、年份固定项和生源关联系数；确保训练集仍覆盖全部省份及年份。每条入选观察在每种划分、每个模型中恰好被留出一次。训练与留出键不重叠，留出教师/班级结果不参与参数估计。总计180次训练拟合，包括两学段主样本及另行标记的“不含西藏小学”诊断。

这是**给定已观察生源特征的回溯留出检验**，不是未来预测：当年与上年学生数据已知，训练集可以包含更晚年份，年度共同变化由其他训练省份估计。相邻年级与年份仍相关，误差不独立；两种划分差异不是置信区间。它用于检查附加关联在留出结果中是否保持，不检验政策或人口的因果作用。

RMSE为误差平方均值开方，MAE为绝对误差均值，单位均为资源同比变化的百分点。数值越小越好。下表箭头为同样本“总生源基线 → 完整年级模型”；MAE增加列为扩展相对基线的百分比变化，不是资源增长的百分点。省份等权RMSE另保留在底表。

|学段|资源|样本数|划分一RMSE（百分点）|划分二RMSE（百分点）|两划分MAE增加范围|
|---|---|---:|---:|---:|---:|
'''+ '\n'.join(table)+'''

完整年级模型在两个划分、两个学段、两个资源的主样本中RMSE均高于基线。小学班级RMSE相对增加0.27%—0.47%，MAE增加4.39%—4.48%；小学教师RMSE相对增加约1.82%。不能把这种误差变化解读为资源调整效率变化。初中完整模型的MAE略降但RMSE增大，说明不同损失指标并不统一，仍不支持广泛的附加改善。

一年级简化扩展中，小学班级RMSE相对降低0.44%—0.53%，但MAE增加0.99%—1.12%；其他资源的RMSE没有降低。因此也不据简化扩展的单一指标微降认定其具有稳定增益。全部比较为固定既有模型的诊断，不因结果不利反复重分折或增删变量寻找改善。

### 13.2 教师敏感性：统计集中，不等于全国贡献

在小学完整年级模型中，将基线与扩展的样本内残差平方和之差按省份加总分配。西藏10条观察的残差平方和从102.933降至69.454，减少33.479，占模型全部样本内误差平方和减少的'''+f"{float(tibet['share_of_total_sse_reduction_pct']):.2f}%"+'''。各省分配之和已与整体减少数核对。

该百分比只描述**模型样本内拟合改善的集中程度**，不是全国教师增减的份额，也不是年级结构的因果贡献。主分析将省—年变化率作为观察单位，各省不是按学生数或教师数加权；不能把对少数省份的拟合改善写成全国规模解释。部分省份的误差可能反而增加，分配比例也不能当作非负、互斥的政策贡献。

第12节删除西藏后调整后R²增益转负的结果，与这里的统计集中一致。另作不含西藏的留出诊断，完整年级模型小学教师RMSE仍比基线高2.02%—4.33%，小学班级也未降低。这个诊断没有替换主样本，没有从资源主体删除西藏，更没有证明西藏资料错误。

### 13.3 西藏来源回查与尚不能回答的“为什么”

直接读取2013—2024年已保存教育部原表，逐年回查西藏小学学生、教师、班级共36个总量单元格，均与主体面板一致，未发现这36个字段的提取错误。来源列位置、原值、SHA256见 `tibet_primary_source_checks.csv`。该检查覆盖36个总量字段，不能称为全部年级或全部省份的独立复审。

西藏小学教师同比并不平滑：2017年−3.11%，2018年+9.87%，2022年+0.11%，2023年+4.81%；同期学生变化分别+4.04%、+3.56%、+2.75%、+2.10%。数据确认了教师变化与总生源变化的不同步，以及该地区对统计模型的影响；没有确认背后的编制、教师招聘、学制、调动或统计调整原因。不得据此写成已识别的政策机制或将这些年度默认为异常删除。

模型杠杆值和Cook距离另存底表，只用作影响定位，不以经验阈值自动排除观察；因省份、年份固定项也进入设计矩阵，不把高杠杆单独视为数据质量缺陷。

### 13.4 计算核验与结果解释修订

180次留出拟合全部检查训练/留出键分离、固定项训练覆盖、设计矩阵秩和最小二乘方程。每种划分的逐行回推结果与观察总数核对。另对两个学段、两资源共4个完整年级留出拟合，以重新构造的第一划分第一折输入作QR求解，预测值与原SVD求解最大差异约3.20×10⁻¹⁴。这是代表性计算交叉检查，不是全部180次的独立求解复核，也不是独立研究者评审。旧交互报告SHA256与此前交付相同。

第12节“完整年级小学班级样本内改善在删省后仍为正”仍成立；本轮补充表明它未通过留出误差改善这一更严格检查。因此可保留为描述性关联，不提升为稳定的结构解释。年级人数分解及各年级方向统计不依赖这些模型，继续有效。当前结论是**年级结构帮助辨认需求内部变化，现有省级年级模型未显示稳定的附加资源解释增益**；不等于证明年级结构永远不重要。

### 13.5 成果与下一关键节点

新增：`grade_holdout_predictions.csv`、`grade_holdout_summary.csv`、`grade_holdout_increment.csv`、`grade_holdout_province_errors.csv`、`grade_holdout_fold_checks.csv`；`grade_in_sample_province_gain.csv`、`grade_model_leverage.csv`；`tibet_primary_source_checks.csv`、`tibet_primary_trajectory.csv`；`grade_deep_validation.json`。复现：`deepen_grade_validation.py` → `verify_grade_deep_checks.py` → `record_grade_deep_results.py`，需NumPy；不改动图表。

本轮深化已经实质改变下一步判断。建议暂不增加年级模型复杂度，将其保留在需求结构描述中，下一轮核验全国城乡分类及其可比口径，寻找不同于高度相关年级变量的结构证据；原题不变，全国分类不能替代省级解释。另一选择是改用具体省份的政策、编制及教师结构资料深入核查教师路径，但这需要新的个案证据，不能继续由省级数量模型推断原因。

按用户关键节点决断要求，本轮停止在上述建议处，等待用户选择“全国城乡口径核验”或“省份教师路径个案资料核查”（或调整问题）后再进入下一阶段。人口与财政缺失资料保持未完成状态，不以模型检验替代这些数据。
'''
report=ROOT/'试做报告.md';old=report.read_text(encoding='utf-8');marker='## 13. 年级路径深化'
if marker in old:old=old[:old.index(marker)].rstrip()
report.write_text(old.rstrip()+'\n\n'+section,encoding='utf-8')
handoff=ROOT.parent/'选题试做交接_教育资源与财政投入.md';old=handoff.read_text(encoding='utf-8');marker='### 2026年10月6日年级深化：留出结果与待决策'
if marker in old:old=old[:old.index(marker)].rstrip()
handoff.write_text(old.rstrip()+'''\n\n### 2026年10月6日年级深化：留出结果与待决策
用户明确“继续深化”，本轮已完成180次回溯留出拟合与影响分配，无图表更新。两套固定两年块划分下，完整年级模型两个学段两个资源的主样本RMSE均高于总生源基线。小学班级样本内改善未转化为稳定留出收益；一年级简化模型仅小学班级RMSE微降，MAE仍增。年级结构保留需求描述价值，不认定稳定资源机制。西藏约占小学教师模型样本内残差平方和改善92.91%，不是全国教师变化份额；36个原表总量单元格回查一致，没有数据错误证据。4个留出拟合QR/SVD核对通过。详见报告第13节和grade_holdout_*、grade_deep_validation、tibet_primary_*。
新的关键节点：建议暂停增加年级模型复杂度，转全国城乡口径核验；另一选择为省份教师政策/编制/结构个案资料核查。待用户决断后执行。原题不变；需求分解结论仍有效；人口和财政资料仍待补；不新增可视化。
''',encoding='utf-8')
print('Deeper grade results and tightened interpretation recorded; awaiting next-stage decision.')
