"""Prepare local release candidate; no GitHub upload or git mutations."""
from pathlib import Path
import shutil,hashlib,json,csv,sys,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'教育资源试做/data';FIG=ROOT/'教育资源试做/正式学术图组_20261011';OUT=ROOT/'研究复现交付_20261011'
OUT.mkdir(exist_ok=True)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(p):
 target=OUT/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
registry=[]
for directory in sorted(DATA.iterdir()):
 if not directory.is_dir() or not any(date in directory.name for date in ['20261010','20261011']):continue
 for p in sorted(directory.rglob('*')):
  if p.is_file() and p.suffix.lower() in {'.csv','.json','.md','.ipynb','.txt'}:
   copy(p);registry.append({'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':digest(p),'role':'processed_table_or_evidence_or_analysis_record'})
for p in (ROOT/'教育资源试做/scripts').glob('*.py'):copy(p)
copy(ROOT/'研究交接_20261010_最新设计与数据状态.md')
report_dir=ROOT/'正式分析报告_20261011'
if report_dir.exists():
 for p in report_dir.iterdir():
  if p.is_file() and p.suffix.lower() in {'.docx','.pdf','.md','.json'}:copy(p)
for p in FIG.rglob('*'):
 if p.is_file() and ('qa' not in p.relative_to(FIG).parts or p.suffix in {'.json','.md'}):copy(p)
with (OUT/'processed_data_manifest.csv').open('w',encoding='utf-8-sig',newline='') as h:
 w=csv.DictWriter(h,fieldnames=['path','bytes','sha256','role']);w.writeheader();w.writerows(registry)
(OUT/'requirements-figures.txt').write_text('matplotlib==3.11.2\nnumpy==2.5.3\npandas==3.0.1\nPillow==12.3.0\n',encoding='utf8')
(OUT/'requirements-reconstruction.txt').write_text('pandas==3.0.1\nopenpyxl==3.1.5\nxlrd==2.0.2\n',encoding='utf8')
(OUT/'.gitignore').write_text('.venv/\n.tmp/\n__pycache__/\n*.pyc\n.DS_Store\n',encoding='utf8')
readme='''# 义务教育经费三十年研究复现资料

本目录是本地发布候选包，尚未上传GitHub。研究范围为1995—2024年，描述生源、收入来源、举办者和地方隶属支出变化；H1/H2探索保留为辅助。

## 目录和覆盖

- 教育资源试做/data：收集日期为20261010及20261011的研究阶段目录内CSV、JSON、Markdown、文本及笔记本。包括候选原值账本、核准记录、探索结果和历史描述，未将候选数据误改成核准数据。
- processed_data_manifest.csv：逐文件路径、字节数及SHA256，界定本包处理资料范围。
- 教育资源试做/scripts：既有处理与分析程序，以及正式图组生成程序。
- 教育资源试做/正式学术图组_20261011：8幅正式图及精确绘图数据、图注和来源清单。

未包含年鉴压缩包、扫描页、原Excel及论文全文。原表路径、卷年、数据年、单元格与散列值保留在证据记录中，复跑原表抽取需另按来源清单提供对应原件。本包保留历史范围和学校口径待核标记，不等于全部数据已跨期可比。部分笔记本是执行结果记录，不保证全部可独立运行。

## 已验证的图组复现

建议Python 3.12，创建独立环境，安装requirements-figures.txt。准备具有合法使用权限的中文字体，用绝对路径指定：

```text
python 教育资源试做/scripts/build_publication_figures.py --root . --font /absolute/path/to/chinese-font.ttf
```

Windows默认使用本机微软雅黑。字体不随包分发。该程序只读取本包已处理表格，生成8幅PNG、SVG、PDF及逐图CSV。无需联网，不运行统计检验。文件时间戳、系统及字体可影响二进制字节，验收以数据数值、标注和范围为准。

原表抽取、核准和回归脚本已保留，但整套流程从原始年鉴到成图的跨电脑端到端复跑尚未验收；不能把已验证的成图复现等同于全流程复现。图组元数据与审校记录见qa资料和交接文件。

## Word插图

PNG为600 dpi纯白背景，标准宽度16.51厘米。建议锁定纵横比，禁用Word图片压缩。SVG文字已转路径以保存字形，PDF嵌入字体。图7较高，建议独占页。图注同时提供文本，便于设为Word正文。尚未声称符合任何特定期刊或比赛的最终版式要求。

## 统计表达

图组以描述性结果为主。省份为观察单位；阶段比较采用相同的28个省级行政单位，地方经费范围与全部举办者学生数未完成桥接，故不计算生均。箱线表示地区分布而非置信区间。增速是窗口内复合年均增速；图2早期为财政性支出、后期为收入，在1998、2002、2007年边界断线。1994年为有条件模型暂估，情景范围不是置信区间，外部小学总额不一致仍待核。主体30年及前置估算补充分开标记。

正式报告的Word及PDF位于正式分析报告_20261011。1994年最终采用当年全国来源构成及义务教育预算比例约束的条件暂估，小学399.27亿元、初中257.35亿元，图2已同步。仍未解释官方白皮书小学总额594亿元的范围差异。正式长表为national_fiscal_1994_2024_report_final.csv，原回推长表另行保留；1995—2024年数据不改。先运行finalize_report_finance.py可从既有情景表恢复最终选择；build_final_report.py使用最终长表及图组制作Word。PDF由Word转换后逐页审校；跨系统PDF转换和字体分页一致性未认证。

## 软件及方法工具

图组使用Matplotlib 3.11.2。审校参考用户安装的scientific-visualization、matplotlib、statistical-analysis技能；技能建议不构成科学有效性或无障碍认证。

Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents. https://doi.org/10.48550/arXiv.2609.00065

引文作者及年份按2026年10月10日读取的arXiv记录核对。年鉴数据及原件的来源权利与自编代码分别处理，本候选包未替原始材料指定开放许可。
'''
(OUT/'README.md').write_text(readme,encoding='utf8')
old=json.loads((DATA/'长期财政数据建设_20261010/build_receipt.json').read_text(encoding='utf8'))['protected_hashes']
receipt={'processed_file_count':len(registry),'processed_bytes':sum(x['bytes'] for x in registry),'all_copied_hashes_match':all(digest(OUT/x['path'])==x['sha256'] for x in registry),'protected_files_unchanged':all(digest(ROOT/p)==v for p,v in old.items()),'github_uploaded':False,'figure_reproduction_verified':True,'full_raw_to_figure_pipeline_verified':False}
(OUT/'release_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
assert receipt['all_copied_hashes_match'] and receipt['protected_files_unchanged']
archive=ROOT/'研究复现交付_20261011.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in OUT.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(ROOT))
print(json.dumps(receipt,ensure_ascii=False));print('Archive:',archive)
