"""Verify first ledger milestone and publish a local, inspectable acceptance record."""
from pathlib import Path
from collections import Counter, defaultdict
from decimal import Decimal
import csv,json,hashlib,sys,zipfile,io,re
import openpyxl
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'教育资源试做/data/长期财政数据建设_20261010'
sys.stdout.reconfigure(encoding='utf8')
def read(name):
    with (OUT/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(name,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
r=read('raw_value_ledger.csv');sources=read('source_registry.csv');student=read('student_candidate_series.csv')
panel=read('supplement_original_candidates.csv');checks=read('arithmetic_checks.csv');coverage=read('coverage_by_year_stage.csv')
summary=json.loads((OUT/'build_receipt.json').read_text(encoding='utf8'))
# Preserve data rows whose converted region labels cannot be safely standardized.
# They live in an explicit appendix and are never silently renamed.
tables=read('education_finance_table_dictionary.csv');unknown=[];tablecache={};zips={}
province_names='北京 天津 河北 山西 内蒙古 辽宁 吉林 黑龙江 上海 江苏 浙江 安徽 福建 江西 山东 河南 湖北 湖南 广东 广西 海南 重庆 四川 贵州 云南 西藏 陕西 甘肃 青海 宁夏 新疆 大连 宁波 厦门 青岛 深圳 全国 合计 总计 总数'.split()
src_lookup={a['source_id']:a for a in sources}
sys.path.insert(0,str(ROOT/'教育资源试做/.tmp/yearbook_read_deps'))
for t in tables:
    src=src_lookup[t['source_id']];key=(src['archive'],src['table'])
    if key not in tablecache:
        if key[0] not in zips:
            z=zipfile.ZipFile(ROOT/key[0]);idx={}
            for i in z.infolist():
                n=i.filename
                if not i.flag_bits & 0x800:
                    try:n=n.encode('cp437').decode('gbk')
                    except UnicodeError:pass
                idx[n]=i
            zips[key[0]]=(z,idx)
        z,idx=zips[key[0]];b=z.read(idx[key[1]])
        if b[:2]==b'PK':
            w=openpyxl.load_workbook(io.BytesIO(b),read_only=True,data_only=True)
            tablecache[key]={s.title:list(s.iter_rows(values_only=True)) for s in w};w.close()
        else:
            import xlrd
            w=xlrd.open_workbook(file_contents=b);tablecache[key]={s.name:[s.row_values(i) for i in range(s.nrows)] for s in w.sheets()}
    rows=tablecache[key][src['sheet']];offset=int(t['source_row_offset'])
    start=offset+len(json.loads(t['headers']))
    later=[int(a['source_row_offset']) for a in tables if a['source_id']!=t['source_id'] and src_lookup[a['source_id']]['archive']==key[0] and src_lookup[a['source_id']]['table']==key[1] and src_lookup[a['source_id']]['sheet']==src['sheet'] and int(a['source_row_offset'])>offset]
    end=min(later) if later else len(rows)
    for ri in range(start,end):
        row=rows[ri];label=re.sub(r'\s+','',str(row[0] or ''))
        if any(label.startswith(p) for p in province_names):continue
        if not any(re.fullmatch(r'\d+(?:\.\d+)?',str(v or '').strip().replace(',','')) for v in row[1:3]):continue
        unknown.append(dict(source_id=t['source_id'],year=t['year'],stage=t['stage'],source_row=ri+1,raw_region=str(row[0] or ''),raw_row=json.dumps(row,ensure_ascii=False),status='unresolved_region_conversion; not standardized or model admitted',unit=t['unit'],school_scope=t['school_scope'],funding_scope=t['funding_scope']))
for z,idx in zips.values():z.close()
write('unresolved_region_source_rows.csv',unknown)
tests={}
tests['source_ids_unique']=len(set(a['source_id'] for a in sources))==len(sources)
tests['record_ids_unique']=len(set(a['record_id'] for a in r))==len(r)
tests['source_foreign_keys_complete']=not(set(a['source_id'] for a in r)-set(a['source_id'] for a in sources))
tests['student_province_grain_unique']=len({(a['data_year'],a['province'],a['stage']) for a in student})==len(student)
tests['student_expected_1856_province_rows']=sum(a['province']!='全国' for a in student)==1856
tests['panel_grain_unique']=len({(a['data_year'],a['province'],a['metric']) for a in panel})==len(panel)
tests['overall_CPI_only']=sum(a['metric']=='CPI_yoy' for a in panel)==930 and len(set(a['original_label'] for a in panel if a['metric']=='CPI_yoy'))==1
tests['missing_not_imputed']=all(not a['accepted_value'] for a in r if not a['numeric_candidate'])
tests['no_model_admission_claim']=all(a['model_eligible']=='False' for a in r)
tests['protected_hashes']=all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in summary['protected_hashes'].items())
src={a['source_id']:a for a in sources}
split=[a for a in r if src[a['source_id']]['family']=='education_finance' and a['data_year']=='2011' and a['stage']=='junior' and a['province']=='北京' and a['funding_scope']=='all_source' and a['school_scope']=='all_affiliations_candidate' and a['metric'] in ['E','P','C','K']]
parts={a['metric']:Decimal(a['numeric_candidate']) for a in split}
tests['2012_volume_continuation_headers_distinct']=len(split)==4 and set(parts)==set(['E','P','C','K']) and abs(parts['E']-parts['P']-parts['C']-parts['K'])<=2
tests['2012_volume_continuation_original_rows']=any(a['metric']=='C' and a['source_row']=='49' and a['cell']=='B49' for a in split)
assert all(tests.values()),tests
write('verification_checks.csv',[dict(check=k,passed=v) for k,v in tests.items()])
numeric_cov=[]
g=defaultdict(list)
for a in r:
    if a['province']=='全国' or a['stage'] not in ['primary','junior'] or a['metric'] not in ['S','E','P','C','K']:continue
    if a['funding_scope'] not in ['all_source','all-source education spending','not_applicable']:continue
    scope='all_affiliations_candidate' if a['school_scope']=='all_affiliations' else a['school_scope']
    g[(a['data_year'],a['stage'],a['metric'],scope)].append(a)
for key,rows in sorted(g.items()):
    counts=Counter(a['province'] for a in rows)
    numeric_cov.append(dict(year=key[0],stage=key[1],metric=key[2],school_scope=key[3],source_records=len(rows),provinces_with_records=len(counts),provinces_with_multiple_records=sum(n>1 for n in counts.values()),provinces_with_positive_numeric_candidate=len(set(a['province'] for a in rows if a['numeric_candidate'] and Decimal(a['numeric_candidate'])>0)),model_ready=0))
write('coverage_numeric_by_scope.csv',numeric_cov)
write('ledger_field_dictionary.csv',[dict(field=k,description=d) for k,d in {
    'record_id':'唯一原表单元格与指标记录号；不以省年作为原值账本唯一键',
    'source_id':'关联source_registry；可追溯压缩包、表名、工作表、表块、卷年和实际年份依据',
    'data_year':'实际年份候选；是否已核准须查source_registry.data_year_status',
    'province':'原表地区标准短名；全国汇总不作为省级观察',
    'stage':'primary小学、junior初中、province_only财政经济、secondary_combined_excluded普通中学合并且不进入初中样本',
    'metric':'研究变量或原表字段；finance_original_field未批准映射为研究变量',
    'source_row':'原工作表1起算行号；续表保留原行号',
    'source_column':'原工作表1起算列号',
    'cell':'原工作表坐标；表块由source_registry.table_block区分',
    'raw_value':'原始值文字表示；保留内空格、字母和符号；未改变原文件',
    'numeric_candidate':'只解析明确数值格式；并不表示通过核准',
    'accepted_value':'本轮限原表内部数值核查通过；不等于跨年可比或模型准入',
    'value_status':'原始数值、零、空白、符号、无效文字、地域不适用、冲突等分开编码',
    'unit':'原表单位；unit_pending不得用于换算；CPI由指标定义标记上年=100',
    'school_scope':'原表学校与隶属范围候选；全隶属与地方隶属不自动合并',
    'funding_scope':'全来源、预算/补助原分类、经费收入分别保存；具体原定义在表名与标签',
    'original_label':'原表表头或财政项目；保留组成和包含关系线索',
    'arithmetic_status':'恒等式内部核查状态；空白不等于零',
    'bridge_status':'跨期/跨来源口径核准状态；本轮尚未批准共同样本',
    'model_eligible':'本轮全部False，避免候选覆盖被误当回归样本',
    'verification_basis':'批准内部数值的具体依据；纠正依据尚无时不改值',
    'notes':'异常、原表块、口径待核等补充信息'}.items()])
student_fail=[a for a in checks if a['check'].startswith('student') and a['status']!='pass_exact']
invalidS=[a for a in r if a['metric'].startswith('S') and a['value_status']=='invalid_numeric_text']
blankS=[a for a in r if a['metric'].startswith('S') and a['value_status']=='missing_blank']
financechecks=[a for a in checks if a['check'].startswith('finance')]
receipt=dict(checks=tests,ledger_rows=len(r),numeric_coverage_rows=len(numeric_cov),student_invalid_text_cells=len(invalidS),student_blank_grade_cells=len(blankS),student_failed_or_uncheckable_checks=len(student_fail),unresolved_finance_region_rows=len(unknown),finance_original_component_checks=len(financechecks),finance_original_component_status=dict(Counter(a['status'] for a in financechecks)))
(OUT/'verification_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
code="""from pathlib import Path
import csv, json, hashlib
base = Path.cwd()
if not (base / 'raw_value_ledger.csv').exists():
    base = base / '教育资源试做/data/长期财政数据建设_20261010'
def read(name):
    with (base / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))
ledger = read('raw_value_ledger.csv')
sources = read('source_registry.csv')
students = read('student_candidate_series.csv')
assert len({r['record_id'] for r in ledger}) == len(ledger)
assert not ({r['source_id'] for r in ledger} - {r['source_id'] for r in sources})
assert sum(r['province'] != '全国' for r in students) == 1856
assert all(not r['accepted_value'] for r in ledger if not r['numeric_candidate'])
assert all(r['model_eligible'] == 'False' for r in ledger)
print(json.dumps(json.loads((base / 'verification_receipt.json').read_text(encoding='utf8')), ensure_ascii=False, indent=2))
"""
nb=dict(nbformat=4,nbformat_minor=5,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},cells=[
    dict(cell_type='markdown',metadata={},source=['# 长期财政原值账本验收\n','原表内部数值核查与跨期可比性分开。本笔记不运行回归、不插值、不绘图。完整核查见verification_checks.csv与verification_receipt.json；原表读取逻辑见项目scripts/build_longitudinal_ledger.py。']),
    dict(cell_type='code',metadata={},execution_count=1,source=code.splitlines(True),outputs=[dict(output_type='stream',name='stdout',text=[json.dumps(receipt,ensure_ascii=False,indent=2)+'\n'])])])
# Execute the companion checks before embedding their verified output.
exec(compile(code,'ledger_acceptance_notebook','exec'),{'__builtins__':__builtins__})
(OUT/'数据验收.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=2),encoding='utf8')
fstatus=receipt['finance_original_component_status']
text=f'''# 长期义务教育财政数据建设：第一阶段验收

日期：2026年10月10日。研究设计已获用户认可。本文件是数据建设工作记录，不是正式报告、引言或假设检验结果。

## 本轮完成了什么

形成变量字典、字段/状态字典、来源登记、原值账本、学生列位字典、财政决算候选值、附带面板原始层、教育经费表块字典、异常清单和匹配覆盖。所有派生文件独立保存在本目录，四个旧主体文件的哈希保持不变。

- 原值账本共{len(r):,}条字段记录，来源登记{len(sources):,}个表/表块。数量包含原分类细项、不同资金范围和全国行，不代表独立省年样本量。
- 学生读取1995—2024两学段60张原表，1,856条省份×学段×年记录，另有60条全国汇总；省级键无重复。1995—1996各30地区，1997以后31地区，未伪造早期重庆。
- {summary['student_numeric_internal_accepted']:,}条省级学生总数同时通过年级加总和分省合计核查，仅批准其原表内部数值；学校类型、隶属范围、附设班和统计时点尚待与经费说明匹配。
- 附带面板只读“原始数据-长面板”，自身收入、财政支出、GDP、综合CPI各930个省年字段位置。字段位置包含空值及早期重庆不适用记录，不能称为930个有效观察。未使用任何填补层。
- 财政读取938个1995—2024目标期候选决算文件，提取{summary['fiscal_cells']:,}条补助、返还、上解及收入相关决算候选字段；预算数与决算数分开。全省/省本级、计划单列市、单位与项目包含关系仍待核准。
- 教育经费原表登记包含收入与支出、早期“初级中学”及普通小学表、不同隶属和资金范围；普通中学合并表保留但排除出初中候选。2024经费RAR的已解压候选值经哈希复核后接入。
- 教育经费同工作表原组成核查{len(financechecks):,}项，其中{fstatus.get('pass_rounding',0):,}项在2个原单位的加总容差内通过。通过仅说明公布E与原P、C、K相符，不说明早晚期分类已经等价，也不替代分省/全国和独立来源复核。

## 本轮核准的读取规则

1. 教育统计年鉴按当年数据包标签登记实际年份候选；1995初中取D列初中小计，不取普通中学合计。每张表分别记录总数、年级列和原始表头。
2. 教育经费早期文件使用“初级中学”，不能只检索“普通初中”而漏表。早期地方隶属资料与后期全隶属资料分别保留，不能因后者覆盖更广就拼接。
3. 2012卷同一工作表上下两块采用不同表头。以北京普通初中为例，前块E、P与后块B49的C分别读取，同表原E=P+C+K核查通过；原行号未重置。
4. 早期经费全来源表内还嵌套“其中财政预算内”列，右侧个人、公用字段不重复映射为全来源P、C，不将内含项目相加。
5. 综合CPI只取总指数的原始系列，排除短名称相同的分类序列。尚未生成链式价格指数、实际金额、D或Z。

## 具体异常及其影响

- **2005年初中全国—分省不一致**：全国总数61,718,079人，比分省合计多4,108,764人；这是当前转换表的核查结果，原因尚未确认，不能据此解释生源变化。本表跨来源复核前不批准长期比较。
- **2006年小学全国总数**：原E13为“1071 15346”，属于含内空格的无效数字文本；不静默删空格。它会阻断当表全国合计验证。
- 学生字段中{len(invalidS)}个含内空格、下划线、波浪符等无效数字文本，{len(blankS)}个年级空栏。后者多数为初中四年级，可能属于学制/不适用，需要查说明；空栏不填零，也不把它们一概当作学生总数错误。
- 河北2008财政卷的天津/河北冲突块全部保留，尚未选取任何块作为核准补助值。
- 经费转换表有{len(unknown)}个地区名称待核的数据行，另存unresolved_region_source_rows.csv，不静默更名。例如2012卷地方初中第12行“内蒙占”、地方小学第15行“黑龙汀”，使当前标准地区候选匹配分别少一行。原整行及其来源已保留，后续须用原表或独立来源核准。
- 财政原表单位未唯一定位、决算列未唯一定位时列入异常，禁止据其换算或合并。早期重庆编制面板数值被标为地域不适用，不能参与收入变化计算。

异常有轻重之分：全国合计冲突、地域伪回填与表块错配会直接影响长期比较；年级空栏主要影响内部核准完整性。exception_ledger.csv中severity是首轮核查优先级，仍须结合具体字段与说明复核，不是错误概率。

## 匹配验收结论

matching_availability.csv保留1,860个目标省份×学段×年位置，其中早期重庆4个位置为不适用。coverage_by_year_stage.csv区分全隶属与地方隶属候选覆盖；coverage_numeric_by_scope.csv进一步区分有字段、有正数和重复来源。

**当前模型准入记录仍为0**：这表示本轮没有签发联合口径核准，并不表示资料不可用。候选列齐全不等于数值已通过、范围已一致或可跨年连接。本轮不检验H1/H2、不计算未经匹配的生均值。

## 下一步的具体顺序

1. 定向复核2005初中全国及省级总数、2006小学总数和8处学生转换文字；查初中四年级/小学六年级空栏的原说明。保留原值、核准值和独立证据，不自动修字符。
2. 阅读教育与经费统计说明，核准1995—2004的地方隶属、初级中学与学生范围；核准2006—2007和2011—2012等分类及表块变化。形成明确批准或分段使用的桥接表。
3. 对地方自身收入与决算原表做同省同年单位换算、包含关系和地区范围核对；解决财政单位/决算列异常、河北冲突及早期计划单列市范围。补助建设可以与其他序列分开验收。
4. 口径批准后再链式调整价格、生成连续可比段和共同样本，报告各阶段有效省年及收入收缩的真实组内变异，然后实施长期生均核算与H1/H2。

## 文件入口

- variable_dictionary.csv：研究变量及准入规则。
- ledger_field_dictionary.csv、status_dictionary.csv：原值账本字段与状态。
- source_registry.csv、raw_value_ledger.csv：出处与原值，可用source_id关联。
- student_column_dictionary.csv、education_finance_table_dictionary.csv：逐表/逐块映射证据。
- exception_ledger.csv、arithmetic_checks.csv：待核问题及每项算术核查。
- unresolved_region_source_rows.csv：无法标准化地区名的原始整行补充账本。
- coverage_by_year_stage.csv、coverage_numeric_by_scope.csv、matching_availability.csv：覆盖和匹配状态。
- 数据验收.ipynb、verification_checks.csv、verification_receipt.json：可复核的唯一键、来源关联、缺失保留、CPI筛选、续表列位等验收。

验收通过{len(tests)}项稳定检查；原始资料及旧主体成果未覆写。可视化尚未启动。
'''
(OUT/'阶段验收说明.md').write_text(text,encoding='utf8')
print('ACCEPTANCE DOCUMENT SAVED',len(tests),'checks')
