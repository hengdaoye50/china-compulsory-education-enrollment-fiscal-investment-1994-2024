"""Record verified availability and stop before user-selected structural analysis."""
import json,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
audit=json.loads((ROOT/'data/grade_structure_validation.json').read_text(encoding='utf-8'))
availability=json.loads((ROOT/'data/structure_availability_validation.json').read_text(encoding='utf-8'))
inventory=list(csv.DictReader(open(ROOT/'data/structure_source_inventory.csv',encoding='utf-8-sig')))
urls={r['key']:r['source'] for r in inventory}
section='''## 11. 结构资料核验与待决策节点（2026年10月6日）

用户要求：继续下一步工作，在分析关键节点汇报具体思路与执行情况，待用户决断后再进行。本轮只完成既有原件的可用性与口径核查、字段提取和合计检查；未开展新的年级结构解释模型、城乡分解或可视化。原选题不变。

### 11.1 已完成的数据准备

检查已保存的350份含小学、初中、民办或城乡相关标题的HTML原件，SHA256均与下载清单一致。覆盖核查仅针对已下载原件及其保留的目录链接，不代表所有官网或年鉴均无其他资料。结果见 `structure_source_inventory.csv`、`structure_source_headers.json`、`structure_availability_validation.json`。

从现有资源面板对应的48份学生、班级原表提取2013—2024年年级字段，形成 `grade_structure_panel.csv`：31省×12年×2学段=744条分省记录，另24条全国记录。小学保留一至六年级，初中保留一至四年级；小学复式班单列，不混入任一单年级。现有资源主体面板未被替换或改写。

应有的学生年级字段共3840个，原表空白73个：初中四年级71个、小学六年级2个。班级单年级字段空白68个，另复式班空白29个。空白保留为缺失，没有擅自填0。年级合计对本学段总数、分省年级合计对全国年级数，1604项可完整计算的检查全部为零差异；184项含空白的检查未标为完整通过。其中168项含空白的行级检查，已填写年级之和与总数的差也均为零，但该算术结果未被当作原表明确填写了零。

逐字段原值、列位置、来源见 `grade_structure_cells.csv`；逐项检查见 `grade_structure_checks.csv`；表头与来源映射见 `grade_structure_sources.json`；汇总见 `grade_structure_validation.json`。核验发现原表某些“合计”表头与全国行文字接近，提取程序以总量列是否为数值区分表头和数据，避免把表头当观察。

### 11.2 分类资料的层级与覆盖限制

已保存的全国表中存在城区/镇区/乡村或历史城乡分类，也有分举办者学生、班级资料；本轮未发现已保存分省表及保留目录链接中的“省份×城乡”或“省份×举办者”可衔接面板。全国分类结果不能复制到每省，不能与省级面板做未经依据的分类控制或分解。各年度分类名称、统计范围和分类变化仍需另行核验，尚未声称全国分类已可连续拼接。

尤其需要区分“学校组织”与“教育学段”口径。2024年[小学学校教职工表]('''+urls['national_index_2024_25']+''')的专任教师为5,721,258人；[小学教育专任教师表]('''+urls['national_index_2024_26']+''')为6,590,072人，后者与现有省级面板全国数一致。前一表的举办者分类不能直接充当现有小学教师口径的分类。现有[中学学校教职工表]('''+urls['national_page_2024_2_9']+''')的专任教师7,408,090人覆盖多种中学组织形式，也不能充当初中教师总数4,148,831人的分类。不能用学生、班级分类的可得性，推定教师举办者分类已同口径齐全。

### 11.3 两条可行路径及建议

**路径A（建议优先）：省级年级结构与资源变化。** 沿用现有省级研究对象和2013—2024年窗口，先检验各年级人数变化如何构成总在校生变化，再比较一年级与高年级的变化与教师、班级变化的关系。年级人数不等于该年招生人数，两者分别保留；年级间、跨年差额也不能直接解释为净迁移或留存率。空白字段可先采用完整记录方案，并另列算术残差与空白敏感性，填零规则需有明确依据，不预先写入模型。若四年级或六年级缺失使特定地区不进入分年级比较，应披露选择影响。

该路径能继续处理“同样总生源变化，内部年级结构是否不同”这一子问题，保留省际比较基础；仍不直接测量适龄人口、县校空间配置或财政总投入。拟按算术构成检查、样本覆盖、条件关联三步推进，不预先将年级构成认作调整原因。

**路径B：全国城乡分类优先，并分别核查举办者。** 先建立各年分类定义和可比范围，验证同口径学生、班级、学段教师总量，再考察分类变化是否掩盖全国总量内部的差异。无法验证教师举办者覆盖的年份或表型不做三指标联合比较。该路径需要改用全国分类作为补充观察层级，不能回答哪些省的城乡资源如何调整，也不能将类别人数变化直接解释为人口迁移；分类重划可能改变统计数。

建议先A，因年级字段已经完成与省级面板的衔接，较少改变已有分析层级。B可在用户选择后作为补充，不能用它替代省级机制分析。**本轮停在此节点，等待用户选择A或B（或调整问题）后再开展对应结构分析；不因等待期间无回复而自行选路。**
'''
report=ROOT/'试做报告.md';old=report.read_text(encoding='utf-8');marker='## 11. 结构资料核验与待决策节点'
if marker in old:old=old[:old.index(marker)].rstrip()
report.write_text(old.rstrip()+'\n\n'+section,encoding='utf-8')
handoff=ROOT.parent/'选题试做交接_教育资源与财政投入.md';old=handoff.read_text(encoding='utf-8');marker='### 2026年10月6日结构资料：待用户决断'
if marker in old:old=old[:old.index(marker)].rstrip()
handoff.write_text(old.rstrip()+'''\n\n### 2026年10月6日结构资料：待用户决断
用户新增要求：到分析关键节点汇报具体思路与执行情况，待其决断后再进行。已核查350份结构相关原件，提取48份省级学生/班级表的年级字段；新表744条省级+24条全国记录，1604项完整合计检查无差异，184项含空白检查单列，原表空白未填零。详见试做报告第11节及grade_structure_*、structure_*资料。
现有城乡、举办者资料主要为全国分类，未发现已保存目录中的省×分类衔接表；小学学校教职工与小学教育教师口径不同，中学学校教职工不能替代初中教师分类。本轮未开展结构解释模型或可视化。
关键节点待决策：A省级年级结构（建议优先），B全国城乡分类并另核举办者口径。等待用户明确选择后再推进对应分析；无回复不自行选择。原选题和财政/适龄人口未完成项保持。
''',encoding='utf-8')
print('Verified data availability recorded; awaiting user choice before structural analysis.')
