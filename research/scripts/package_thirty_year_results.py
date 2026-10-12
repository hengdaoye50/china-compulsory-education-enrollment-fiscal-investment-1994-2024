"""Package executed verification/readout notebook and current handoff."""
import sys, json, io, contextlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/data/三十年纵向分析_20261010'
if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf8')

def main():
    runner=ROOT/'research/scripts/run_primary_exploration.py'
    src=runner.read_text(encoding='utf8')
    src=src.replace('H1_primary_exploratory=True,','H1_exploratory=True,stage=stage,')
    runner.write_text(src,encoding='utf8')
    codes=[
        "from pathlib import Path\nimport sys, pandas as pd\nROOT = Path("+repr(str(ROOT))+ ")\nOUT = ROOT / 'research/data/三十年纵向分析_20261010'\nsys.path.insert(0, str(ROOT / 'research/scripts'))\nfrom validate_thirty_year_analysis import main\nvalidation = main()\nassert validation['all_passed']",
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
    cells.append(dict(cell_type='code',metadata={},source=["# 可选重新生成，未在本笔记本执行\n", "# from build_thirty_year_history import main as rebuild_history\n", "# from run_primary_exploration import main as rerun_exploration\n", "# from extend_thirty_year_analysis import main as rerun_extensions\n", "# rebuild_history()\n", "# rerun_exploration(stage='junior', output=ROOT / 'research/data/初中探索分析_20261010')\n", "# rerun_extensions()\n"],execution_count=None,outputs=[]))
    notebook=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python')),cells=cells)
    (OUT/'三十年纵向分析_已执行.ipynb').write_text(json.dumps(notebook,ensure_ascii=False,indent=2),encoding='utf8')
    print('Executed verification notebook packaged.')

if __name__=='__main__':main()
