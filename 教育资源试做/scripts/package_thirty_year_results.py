"""Package executed verification/readout notebook and current handoff."""
import sys, json, io, contextlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'教育资源试做/data/三十年纵向分析_20261010'
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')

def main():
    runner=ROOT/'教育资源试做/scripts/run_primary_exploration.py'
    src=runner.read_text(encoding='utf8')
    src=src.replace('H1_primary_exploratory=True,','H1_exploratory=True,stage=stage,')
    runner.write_text(src,encoding='utf8')
    codes=[
        "from pathlib import Path\nimport sys, pandas as pd\nROOT = Path("+repr(str(ROOT))+ ")\nOUT = ROOT / '教育资源试做/data/三十年纵向分析_20261010'\nsys.path.insert(0, str(ROOT / '教育资源试做/scripts'))\nfrom validate_thirty_year_analysis import main\nvalidation = main()\nassert validation['all_passed']",
        "for name in ['national_student_endpoints.csv', 'segmented_finance_structure_changes.csv', 'four_exploratory_hypotheses.csv']:\n    print('\\n' + name)\n    print(pd.read_csv(OUT / name).to_string(index=False))",
        "print('同省年配对：')\nprint(pd.read_csv(OUT / 'paired_stage_H1_difference.csv').to_string(index=False))\nprint('转列年份敏感性，仅点估计及标准误：')\nprint(pd.read_csv(OUT / 'additional_reclassification_sensitivity.csv').to_string(index=False))"
    ]
    cells=[dict(cell_type='markdown',metadata={},source=['# 1995—2024年纵向分析与学段对照\n','本笔记本已执行新增结果复算及结果读取；原探索自助检验由独立分析程序生成。置信集合未闭合时不将诊断区间当作主区间。'])]
    namespace={}
    for count,code in enumerate(codes,1):
        output=io.StringIO()
        with contextlib.redirect_stdout(output):exec(compile(code,f'notebook_cell_{count}','exec'),namespace)
        cells.append(dict(cell_type='code',metadata={},source=code.splitlines(True),execution_count=count,outputs=[dict(output_type='stream',name='stdout',text=output.getvalue().splitlines(True))]))
    cells.append(dict(cell_type='markdown',metadata={},source=['完整历史和初中探索已经在各自程序中运行；下面提供重新生成入口，避免打开笔记本即自动重跑9,999次抽样。']))
    cells.append(dict(cell_type='code',metadata={},source=["# 可选重新生成，未在本笔记本执行\n", "# from build_thirty_year_history import main as rebuild_history\n", "# from run_primary_exploration import main as rerun_exploration\n", "# from extend_thirty_year_analysis import main as rerun_extensions\n", "# rebuild_history()\n", "# rerun_exploration(stage='junior', output=ROOT / '教育资源试做/data/初中探索分析_20261010')\n", "# rerun_extensions()\n"],execution_count=None,outputs=[]))
    notebook=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python')),cells=cells)
    (OUT/'三十年纵向分析_已执行.ipynb').write_text(json.dumps(notebook,ensure_ascii=False,indent=2),encoding='utf8')
    handoff=ROOT/'研究交接_20261010_最新设计与数据状态.md'
    text=handoff.read_text(encoding='utf8')
    if '**第七阶段：三十年历史与两学段分析' not in text:
        text+='\n\n**第七阶段：三十年历史与两学段分析（10月10日）。** 用户强调1995—2024年完整30年，已完成60条全国学生历史、1,790条省级年度变化、125轮持续下降识别。至少两轮下降的省份小学21、初中18；改用连续三年标准仍15/11。地方隶属P/C历史分段核算，两学段原表个人占比均呈早期升、2007—2013降、2013—2023升；不跨2006→2007经费分类断点，不用地方隶属经费除以全举办者学生。初中2008—2023主样本202条，H1=-0.767/p=.0719，H2阶段差异=.585/p=.1254；连同小学四检验Holm校正均未确认。98条同省年双方持续下降配对的H1学段差异=-.00136/p=.9777，压力观察仅5条/3省，反演置信集合不连通且边界未闭合，不报告有限区间。辽宁2014官方决算支持全省范围；黑龙江2015收入快报下降而全省支出增长，说明自身收入不等于资源总量，快报不覆盖年鉴决算候选。2015/2016基金转列敏感性已报告，禁止选有利版本替换主模型。12项复算通过，原成果保持。最新工作备忘及已执行笔记本在 `教育资源试做/data/三十年纵向分析_20261010/`。下一步实质推进经费来源分段构成、同省多轮响应和同范围支出/学生分解，不再循环全面核查，不因短窗口不显著放弃长期研究，也不以30年跨度代替识别质量。\n'
    handoff.write_text(text,encoding='utf8')
    print('Executed notebook packaged; latest handoff updated.')

if __name__=='__main__':main()
