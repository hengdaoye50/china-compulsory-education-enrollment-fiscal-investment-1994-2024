"""Local release candidate with analysis inputs and original-source traceability."""
from pathlib import Path
import json,hashlib,zipfile
import pandas as pd
from docx import Document
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'教育资源试做/data';NEW=DATA/'支出细项与补助拓展_20261011';FIG=ROOT/'教育资源试做/支出细项与补助图组_20261011';OUT=ROOT/'支出细项与补助拓展报告_20261011'
def main():
    doc=Document(OUT/'义务教育支出细项与中央补助拓展报告.docx');captions=[p.text for p in doc.paragraphs if p.style.name=='Caption'];names=['图F3_商品服务与工资响应差','图F1_支出内部构成','图F2_公用增长贡献','图F4_支出细项响应','图F7_时期分段响应','图F5_自身收入与补助合计变化','图F6_中央补助关联'];assert len(captions)==7
    plotdata={'图F1':'composition_plot_data.csv','图F2':'annual_mean_contribution_plot_data.csv','图F3':'component_primary_tests.csv','图F4':'all_coefficients.csv','图F5':'fiscal_state_plot_data.csv','图F6':'subsidy_exploratory_tests.csv','图F7':'period_contrast_plot_data.csv'}
    (FIG/'图注与绘图数据.md').write_text('# 支出细项与补助图组图注\n\n白底；南开紫 #7E0C6E、金色 #B68A3A；600dpi PNG及SVG/PDF。来源为用户提供年鉴原表，详见原格回读与补助候选账本。原文件编号F与报告阅读顺序编号不同，以下明确对应。\n\n'+'\n\n'.join(f'## {name}\n\n{cap}\n\n绘图数据：教育资源试做/data/支出细项与补助拓展_20261011/{plotdata[name[:3]]}' for name,cap in zip(names,captions)),encoding='utf8')
    # Complete fiscal coverage, including failed parsing/missing entries rather than only successful records.
    accepted=pd.read_csv(NEW/'subsidy_levels_numeric.csv');rejected=pd.read_csv(NEW/'subsidy_exclusions.csv');provs=sorted(pd.read_csv(NEW/'component_levels.csv').province.unique());coverage=[]
    for y in range(2007,2024):
        for p in provs:
            a=accepted[(accepted.year==y)&(accepted.province==p)];r=rejected[(rejected.year==y)&(rejected.province==p)];coverage.append(dict(year=y,province=p,numeric_accepted=len(a)==1,reason='numeric_source_match_scope_pending' if len(a)==1 else '|'.join(sorted(set(r.reason.dropna()))) if len(r) else 'no_explicit_unit_actual_column_or_matching_income_subsidy_block_found'))
    pd.DataFrame(coverage).to_csv(NEW/'subsidy_full_coverage.csv',index=False,encoding='utf-8-sig');assert len(coverage)==527 and sum(x['numeric_accepted'] for x in coverage)==495
    (NEW/'visualization_receipt.json').write_text(json.dumps(dict(figures=7,report_order=names,dpi=600,white_background=True,raw_cell_checks=4216,independent_checks=130,period_checks_post_chart_adaptive=True),ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'复现说明.md').write_text('''# 本轮复现增量包

本地候选交付，接续长期主报告及第17、18阶段，不替换历史数据。七页七图两表报告已逐页审校。

最低运行环境：Python、pandas、numpy、matplotlib、Pillow、python-docx、openpyxl；原表读取另外需要xlrd、pdfplumber。研究环境版本pandas3.0.1、numpy2.5.3、matplotlib3.11.2。原脚本中的工作区依赖路径应按复现环境调整，中文绘图字体需替换为可用中文字体。Windows默认字体路径不是跨平台假设。

直接复算：在解压项目根目录依次运行analyze_spending_components_subsidies.py、check_component_regime_sensitivity.py、audit_spending_components_subsidies.py。输入为本包带坐标与来源账本的component_levels.csv、subsidy_levels_numeric.csv及前阶段两学段模型输入。随机种子及9999次约束野生自助固定；不同BLAS与浮点环境可能有微小尾差。图F7与追加方案为看图后探索性检查。独立审校包括完整虚拟变量估计及省级CR1协方差。

从原始年鉴重读：先运行extract_spending_components_subsidies.py，需要将用户提供的原年鉴压缩包和2024教育经费年鉴解压目录按source_registry及原格账本路径放入根目录。原年鉴未并入增量包；原表路径、文件哈希、单位、单元格坐标及所有候选/排除均保留。缺少授权原件时可复算派生分析，不可冒充重新验证原文件。所有范围待核标记保留，不将数值核准等同口径认证。

报告制作使用build_spending_subsidy_report.py及Word兼容渲染器，需要逐页检查，不能将生成成功当作版式通过。PDF由报告Word渲染，正文与图表相同。SVG/PDF保留矢量，PNG600dpi纯白。

保护哈希包括历史主表和前阶段输入，复算后应保持不变。zip内增量清单包含所有文件SHA256；封包后逐项读回核对。发布GitHub前仍应以既有全项目交付和原资料授权范围为准，不能用本增量包替代完整三十年数据库。
''',encoding='utf8')
    receipt=json.loads((NEW/'analysis_receipt.json').read_text(encoding='utf8'));files=[]
    for folder in [NEW,FIG]:files.extend(p for p in folder.rglob('*') if p.is_file())
    files.extend(p for p in OUT.iterdir() if p.is_file() and p.suffix in ['.docx','.pdf','.json','.md'])
    files.extend(ROOT/p for p in receipt['protected_sha256'])
    files.extend(DATA/p for p in ['province_finance_next_protected_baseline.json','经费共同样本核查_20261010/PC_original_evidence.json','经费共同样本核查_20261010/SPCR_numeric_availability.csv','长期财政数据建设_20261010/source_registry.csv','财政收入补核_20261010/R_province_year_numeric_panel_with_summaries.csv','年鉴资料核查_20261010/all_archive_tables.csv'])
    scripts=['extract_spending_components_subsidies.py','analyze_spending_components_subsidies.py','check_component_regime_sensitivity.py','audit_spending_components_subsidies.py','build_spending_subsidy_report.py','package_spending_subsidy_extension.py','exploratory_panel_stats.py','infer_resource_timing.py','inspect_bridge_evidence.py']
    files.extend(ROOT/'教育资源试做/scripts'/p for p in scripts);files.extend([ROOT/'研究接续_20261011_支出细项与补助拓展.md',ROOT/'研究交接_20261010_最新设计与数据状态.md']);files=sorted(set(files))
    manifest=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files];target=OUT/'支出细项与补助拓展复现增量包.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,p.relative_to(ROOT).as_posix())
        z.writestr('支出细项与补助增量清单.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for row in manifest:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
    print(len(files),'files; archive hashes verified;',target.stat().st_size,'bytes')
if __name__=='__main__':main()
