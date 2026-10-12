"""Audit publication years and departmental expenditure candidates, not fiscal ratios.

Requires xlrd==2.0.2, installed locally in ../.tmp/finance_xls_reader.
PDF locators use one-based physical PDF pages, not printed page labels.
"""
import hashlib
import json
import re
import sys
from decimal import Decimal as D
from lxml import html
from pypdf import PdfReader
from parse import ROOT, save_csv

sys.path.insert(0, str(ROOT / '.tmp/finance_xls_reader'))
import xlrd

sources = []
for path in sorted(ROOT.glob('finance_continuity*_sources.json')):
    sources.extend(json.loads(path.read_text(encoding='utf-8')))
by_key = {r['key']: r for r in sources}
assert len(by_key) == len(sources)
for r in sources:
    assert r['status'] == 'downloaded'
    p = ROOT / r['path']
    assert len(p.read_bytes()) == r['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest() == r['sha256']
save_csv(ROOT / 'data/finance_continuity_source_receipt.csv', [
    {k: r.get(k) for k in ['key', 'url', 'status', 'path', 'bytes', 'sha256']} for r in sources])

checks = []
def check(name, actual, expected, tolerance='0', locator=''):
    difference = D(str(actual)) - D(str(expected))
    assert abs(difference) <= D(tolerance), (name, difference)
    checks.append(dict(check=name, actual=str(actual), expected=str(expected),
                       difference=str(difference), tolerance=tolerance, locator=locator, status='pass'))

unit = '烟台市牟平区武宁街道五里头学区小学'
pdf = PdfReader(ROOT / by_key['finance_continuity_wulitou_2023_pdf']['path'])
pages = [p.extract_text() or '' for p in pdf.pages]
text = '\n\n'.join(pages)
assert re.search(r'2023\s*年\s*度', pages[0]) and unit in text
assert '2022\n年度部门决算公开由主管部门汇总填报，23 年独立填报' in pages[21]
assert '2023年在校生704人' in pages[40]
for value in ['1,015.84', '835.26', '144.73', '35.84']:
    assert value in pages[6]
assert '992.45' in pages[9] and '23.39' in pages[9]
assert '人员经费合计 927.18 公用经费合计 65.27' in pages[16]

book = xlrd.open_workbook(str(ROOT / by_key['finance_continuity_wulitou_2024_xls']['path']))
assert book.nsheets == 1
s = book.sheet_by_index(0)
assert s.cell_value(2, 7) == '2024年度' and unit in s.cell_value(2, 0)
assert s.cell_value(2, 14) == '金额单位：元'
export = [{'row_zero_based': i, 'column_zero_based': j, 'value': str(s.cell_value(i, j))}
          for i in range(s.nrows) for j in range(s.ncols) if s.cell_value(i, j) != '']
save_csv(ROOT / 'data/finance_continuity_wulitou_2024_xls_cells.csv', export)
assert not any('学生' in r['value'] for r in export)

fields = [
    ('total_expenditure', '本年支出合计', '1015.84', 32, 14, 'PDF p7 公开01 / XLS Z01 r33 c15'),
    ('education_function_expenditure', '教育支出（功能分类）', '835.26', 10, 9, 'PDF p7 / XLS r11 c10'),
    ('social_security_expenditure', '社会保障和就业支出', '144.73', 13, 9, 'PDF p7 / XLS r14 c10'),
    ('health_expenditure', '卫生健康支出', '35.84', 14, 9, 'PDF p7 / XLS r15 c10'),
    ('basic_expenditure', '基本支出', '992.45', 6, 14, 'PDF p10 公开03 / XLS r7 c15'),
    ('basic_personnel_expenditure', '基本支出中的人员经费', '927.18', 7, 14, 'PDF p17 公开06 / XLS r8 c15'),
    ('basic_public_expenditure', '基本支出中的公用经费', '65.27', 8, 14, 'PDF p17 公开06 / XLS r9 c15'),
    ('project_expenditure', '项目支出', '23.39', 9, 14, 'PDF p10 / XLS r10 c15'),
]
rows, paired = [], []
values = {2023: {}, 2024: {}}
for field, label, prior, i, j, locator in fields:
    old = D(prior) * 10000
    new = D(str(s.cell_value(i, j)))
    values[2023][field], values[2024][field] = old, new
    for year, value, key, original_unit in [(2023, old, 'finance_continuity_wulitou_2023_pdf', '万元'),
                                            (2024, new, 'finance_continuity_wulitou_2024_xls', '元')]:
        rows.append(dict(unit=unit, year=year, field=field, label=label, value_yuan=str(value),
                         original_unit=original_unit, locator=locator, source=by_key[key]['url'],
                         scope='unit departmental final accounts; not education-finance statistics',
                         eligibility='source candidate only; institutional coverage bridge unresolved'))
    paired.append(dict(field=field, label=label, value_2023_yuan=str(old), value_2024_yuan=str(new),
                       change_yuan=str(new-old), nominal_change_percent=str((new/old-1)*100),
                       interpretation='published same-name unit fields; not population response or official per-student metric'))
save_csv(ROOT / 'data/finance_continuity_candidate_cells.csv', rows)
save_csv(ROOT / 'data/finance_continuity_candidate_changes.csv', paired)

for year, v in values.items():
    tolerance = '150' if year == 2023 else '0.01'  # 3 independently rounded 万元 entries.
    check(f'{year}_reported_function_subtotal_vs_total',
          v['education_function_expenditure']+v['social_security_expenditure']+v['health_expenditure'],
          v['total_expenditure'], tolerance, 'Only explicitly reported nonblank categories; no blank-to-zero conversion')
    check(f'{year}_personnel_plus_public_vs_basic',
          v['basic_personnel_expenditure']+v['basic_public_expenditure'], v['basic_expenditure'], tolerance)
    check(f'{year}_basic_plus_project_vs_total', v['basic_expenditure']+v['project_expenditure'],
          v['total_expenditure'], tolerance)
check('2024_reported_economic_categories_vs_total',
      sum(D(str(s.cell_value(i,14))) for i in [17,18,19,22]), values[2024]['total_expenditure'], '0.01')
check('2024_income_vs_expenditure', s.cell_value(32,4), s.cell_value(32,14), '0.01')
save_csv(ROOT / 'data/finance_continuity_quality_checks.csv', checks)

links = []
for page_key, file_key, year in [
    ('finance_continuity_wulitou_2023_decision', 'finance_continuity_wulitou_2023_pdf', 2023),
    ('finance_continuity_wulitou_2024_decision', 'finance_continuity_wulitou_2024_xls', 2024),
    ('finance_continuity_xinan_2024_decision', 'finance_continuity_xinan_2024_pdf', 2024)]:
    raw = (ROOT / by_key[page_key]['path']).read_bytes()
    filename = by_key[file_key]['url'].rsplit('/',1)[-1]
    assert filename.encode() in raw
    title = html.fromstring(raw).xpath('string(//title)')
    links.append(dict(page=by_key[page_key]['url'], attachment=by_key[file_key]['url'],
                      page_title=title, file_statistical_year=year, relationship='attachment basename present in original HTML'))
assert re.search(r'2024\s*年\s*度', PdfReader(ROOT / by_key['finance_continuity_xinan_2024_pdf']['path']).pages[0].extract_text())
save_csv(ROOT / 'data/finance_continuity_publication_bridge.csv', links)

student_rows = []
school_page = html.fromstring((ROOT / by_key['finance_continuity_wulitou_data_page']['path']).read_bytes())
for tr in school_page.xpath('//tr'):
    cells = [''.join(td.itertext()).strip() for td in tr.xpath('./td')]
    if len(cells) >= 3 and re.fullmatch(r'20\d\d—20\d\d', cells[0]):
        assert cells[1].isdigit() and cells[2].isdigit()
        student_rows.append(dict(unit=unit, period=cells[0], students=int(cells[1]),
                                 staff_or_teacher_reported=int(cells[2]),
                                 locator='school statistics table; 教师数据 column',
                                 source=by_key['finance_continuity_wulitou_data_page']['url'],
                                 eligibility='academic-year label; statistical time and fiscal scope unverified'))
assert len(student_rows) == 5
student_rows.append(dict(unit=unit, period='2023（具体时点未说明）', students=704,
                         staff_or_teacher_reported='', locator='2023 decision PDF p41 performance self-evaluation',
                         source=by_key['finance_continuity_wulitou_2023_pdf']['url'],
                         eligibility='not identified as weighted fiscal denominator'))
xinan_students = html.fromstring((ROOT / by_key['finance_continuity_xinan_2023_2024_students']['path']).read_bytes())
assert '在校生383人' in ''.join(xinan_students.itertext())
student_rows.append(dict(unit='海阳市辛安镇第一初级中学', period='2023-2024学年度', students=383,
                         staff_or_teacher_reported=57, locator='school statistics article body',
                         source=by_key['finance_continuity_xinan_2023_2024_students']['url'],
                         eligibility='academic year; not matched 2024 fiscal denominator'))
save_csv(ROOT / 'data/finance_continuity_student_scope_candidates.csv', student_rows)

coverage = [
    dict(source='wulitou 2023-2024 departmental final accounts', years='2023,2024', actual_spending='yes; unit accounts', students='2023 self-evaluation:704; time basis not specified; 2024 XLS none', weights='unknown', allocation='not needed for within-unit totals; education-finance scope bridge unknown', status='two-year expenditure candidate, not population/fiscal decomposition pair'),
    dict(source='xinan 2024 departmental final accounts', years='2024', actual_spending='yes; unit accounts', students='2023-2024 academic statistics:383; not matched annual denominator', weights='unknown', allocation='not verified', status='single verified fiscal year'),
    dict(source='two earlier Yantai teaching-finance PDFs', years='unverified', actual_spending='present', students='year-start/end present', weights='unknown', allocation='not verified', status='originals retained; publication-page association unresolved'),
    dict(source='Shucheng 2023 teaching-finance forms', years='2023', actual_spending='yes; primary/junior explicitly separated', students='year-start/end present', weights='unknown', allocation='stage allocation rules unknown', status='single year; original HTML unavailable; prior web extract retained')]
save_csv(ROOT / 'data/finance_continuity_coverage.csv', coverage)
summary = dict(download_records=len(sources), saved_originals=len(sources), verified_attachment_page_links=len(links),
               candidate_expenditure_cells=len(rows), arithmetic_checks=len(checks),
               student_scope_candidate_rows=len(student_rows),
               same_name_unit_two_year_expenditure_candidates=1,
               matched_continuous_weighted_fiscal_pairs=0, population_response_analysis_performed=False,
               earlier_teaching_finance_pdf_years_verified=False, historical_2022_zero_not_inferred=True,
               main_panel_modified=False, visualization_modified=False)
(ROOT / 'data/finance_continuity_audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
