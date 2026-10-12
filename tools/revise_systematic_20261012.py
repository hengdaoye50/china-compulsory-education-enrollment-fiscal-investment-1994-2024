from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy
from lxml import etree as E
import re, json, hashlib

ROOT=Path(__file__).resolve().parents[1]
SRC=next((ROOT/'reports/history/20261012-editing-baseline').glob('*.docx'))
OUT=ROOT/'reports/final'
OUT.mkdir(exist_ok=True)
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
W='{'+NS['w']+'}'
with ZipFile(SRC) as z: files={n:z.read(n) for n in z.namelist()}
root=E.fromstring(files['word/document.xml']); body=root.find(W+'body'); ps=body.findall(W+'p')
changes=[]
def txt(p): return ''.join(p.itertext()) if False else ''.join(p.xpath('.//w:t/text()',namespaces=NS))
def setp(i,s):
 p=ps[i]; old=txt(p); runs=p.findall(W+'r'); proto=deepcopy(runs[0].find(W+'rPr')) if runs and runs[0].find(W+'rPr') is not None else None
 for n in list(p):
  if n.tag!=W+'pPr':p.remove(n)
 # Preserve typography; citation superscripts authored as separate runs.
 for part in re.split(r'(\[\d+(?:[-,]\d+)*\])',s):
  if not part:continue
  r=E.SubElement(p,W+'r'); rp=deepcopy(proto) if proto is not None else E.Element(W+'rPr')
  for v in rp.findall(W+'vertAlign'):rp.remove(v)
  if i<227 and re.fullmatch(r'\[\d{1,2}(?:[-,]\d{1,2})*\]',part):E.SubElement(rp,W+'vertAlign').set(W+'val','superscript')
  r.append(rp); tt=E.SubElement(r,W+'t');tt.text=part;tt.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
 changes.append({'paragraph_index':i,'before':old,'after':s})

updates={
13:'本报告考察1995—2024年义务教育生源规模、财政性收入及支出结构的长期变化，并以1994年条件估算补充历史基期。研究结合全国年度资料与省级面板，采用趋势描述、举办者收入构成分解和支出项目条件关联分析。财政性收入与全来源支出分别解释。',
14:'小学在校生于1997年达到观察期峰值，2013年降至低点后回升，2024年再次下降；初中于2003年达到峰值，2015年降至低点后回升。两学段峰谷错位，多个地区反复出现连续下降。2013—2024年，两学段财政性收入名义金额分别增长107.31%和111.27%，财政性收入占比却回落，举办者收入权重变化参与了全国比例调整。',
15:'地方支出扩张由较快增长转向较低增速。在相同28个省级地区中，2013—2023年个人与公用合计的实际增速低于2007—2013年的地区，小学为28个、初中为26个。2017—2023年，小学8个、初中7个地区公用支出累计实际下降；公用内部商品服务与资本性项目的变化可能相互抵消。',
16:'2008—2023年省级面板中，商品服务相对工资福利的生源响应差，小学为0.766、初中为0.506，均通过相应检验族的多重检验校正。教师、班级和中央补助拓展未确认独立机制关联，分期结果亦不足以确认关系跨期稳定。',
17:'长期变化呈现生源下降与回升交替、财政性金额扩张与来源占比调整并存、地方支出增速放缓和项目分化的过程。全国保障扩张因此需要与学段时序、地区需求和运行及资本项目的分别观察相结合。',
35:'全国义务教育投入持续扩张，生源却经历下降与回升，不同地区和项目的支出也未按同一比例调整。本报告围绕三个问题展开：生源与投入经历了怎样的长期变化；收入来源和支出项目如何重组；不同项目与生源变化的条件关联有何差异。',
36:'现有研究关注师资需求、人员配置和小规模学校调整。[1-4] 本报告将长期序列与地区、项目分析连接起来，说明全国保障扩张中的配置差异；省级条件关联用于补充结构判断，不替代学校层面的机制证据。',
38:'资料来自教育、教育经费、财政和综合统计年鉴，按实际数据年整理。[5-10] 全国生源与主要经费序列延伸至2024年，支出细项回归覆盖2008—2023年。历史支出采用地方隶属口径，回归采用全隶属口径；长期端点比较固定为28个省级地区。',
40:'分析依次采用趋势描述、构成分解和控制省份、年份效应的条件关联模型；实际增长以地区CPI调整。1994年条件估算不进入回归。生源与财务统计覆盖尚未完全对应，不计算严格同范围的生均支出。详细规则列于附录。',
42:'2005年农村义务教育经费保障机制改革明确中央与地方分担及公用经费、校舍维修、教师工资等保障安排。[NEW] 2015年进一步完善城乡义务教育保障，2018年强调优化经费使用与教师待遇，2019年细化中央与地方事权和支出责任。[11-13]',
43:'上述制度构成观察长期投入变化的背景，学校保障需求还涉及服务范围、人员和设施存量。工资养老列支、项目完结和采购时点也会改变账面构成。本报告分别处理制度背景与统计边界，不将窗口分界或当年增长认定为改革净效应。',
113:'商品服务相对工资福利的学生响应差，小学为0.766、初中为0.506，相应校正p为0.0008、0.0033（图11）。在其他条件相同的模型比较中，在校生人数的年度增长率相差1个百分点（以对数变化近似），商品服务与工资福利实际支出增长率之差平均相差约0.77个百分点（小学）和0.51个百分点（初中）。剥离其他资本性和个人家庭补助后，项目关联差异仍然存在。',
115:'（三）分期估计及其不确定性',
119:'剔除2017—2018年后，学生响应差仍为0.816（小学）、0.450（初中）。分期估计中，前期为1.011、0.502，后期为1.128、−0.207。初中后期95%近似区间为−1.339至0.925，估计精度不足（图12）。现有分期结果不足以确认关系跨期稳定，也不足以认定关系逆转；不同窗口的点估计或显著性差异不等于已检验出系数差异。',
131:'全国财政保障扩张与生源、地区和项目调整共同构成三十年的变化。生源先后经历下降与回升，财政性金额增长伴随来源占比调整，地方支出则由较快扩张转向较低增速，并出现局部项目收缩。全国总量因而需要与学段时序及配置结构结合解释。',
139:'省级模型支持商品服务与工资福利具有不同的生源关联。2008—2023年，控制实际自身财政收入及省份、年份效应后，两项响应差为0.766（小学）和0.506（初中），均通过相应检验族的多重检验校正。年度生源增长率相差1个百分点（以对数变化近似），两项实际支出增长率之差平均相差约0.77和0.51个百分点。这是省级汇总资料中的条件关联，不直接说明学校如何调整人员或运行预算。教师、班级和补助拓展未确认独立机制关联，分期结果也不足以确认跨期稳定。现有证据支持项目间差异，尚不支持认定生源下降必然造成运行经费挤压。',
141:'政策重点是在财政保障扩张的基础上，提高配置对学段时序、地方需求和项目变化的适应性。以下建议分别对应资源规划、预算编制、地区复核和财政保障，具体额度依据县域、学校资料确定。',
142:'分学段开展县域滚动资源规划。教育部门应结合小学毕业队列、初中入学需求、人口流动及城乡学校分布，定期更新未来数年的学位、班级和教师需求。增长地区提前安排容量与师资，下降地区结合服务半径、班额和人员存量安排过渡。小学与初中增减错位、地区多轮下降的事实表明，单年人数变化不足以成为跨学段调拨或永久缩减资源的依据。',
143:'在预算编制中分别论证基本运行与资本项目。教育和财政部门应按学校服务任务核对教学运行、设施维护等经常性需求，并结合工资福利等人员支出安排核实保障水平；建设和集中采购则依据项目进度、存量设施及支付计划安排。商品服务项目可作为运行相关支出的观察线索，但不能替代学校实际成本清单。公用合计与人员份额用于提示结构变化，预算决策应落实到具体需求及项目明细。',
144:'对累计实际下降地区开展项目复核。小学8个、初中7个地区的公用支出下降可作为筛选线索，由地方教育和财政部门核对学校覆盖、细项金额及支付进度。项目收尾或支付时点变化，应调整后续项目计划；学校服务任务未减而基本运行资金不足，应据核实后的缺口研究补足安排。个人与公用合计也下降的地区，应同步核对生源、人员和设施变化。CPI平减仅反映一般购买力变化，不能单凭端点负增长认定运行缺口。',
145:'按资金用途和实际到位情况评估地方保障能力。共同样本中，84条自身财政收入实际下降记录有60条在加计中央补助后未下降，说明本级收入不足以完整代表财政背景。财政部门应核对中央地方分担、专项用途、上解及资金到位时间，区分财政总项与可用于学校运行的资金；教育部门按举办者列示财政性金额和来源占比。保障决策应依据学校可用资金与服务任务的对应关系，不能由总补助增长推定专项保障充分。',
167:'团队还使用profyunv学术指导知识库辅助审视问题意识、研究设计和结论边界，使用academic-human-writing技能检查中文学术表达、证据与判断的对应关系及重复表述。知识库辅助意见由团队审阅，不代表知识库所涉及学者本人参与或认可本报告。',
178:'实际对数变化为Δln X实际＝ln(X当年/X上年)−ln(CPI当年/100)。支出模型为Δln Y实际＝βSΔln S＋βRΔln R实际＋α省＋λ年＋ε。直接差模型以两项实际对数变化之差为因变量；同省同年使用相同CPI时，平减因子相消，可写作Δln C−Δln P或Δln G−Δln W。解释变量保持相同；资源模型加入教师、班级，补助模型加入Δln B实际或以R＋B替代R。',
242:'[16] 蒋鸣和. 中国教育经费投入的“八五”回顾与“九五”展望[J/OL]. 教育研究信息, 1996(9)[2026-10-12]. https://www.cnsaes.org.cn/homepage/Upfile/201029/2010020981343441.pdf.',
}
for i,s in updates.items():setp(i,s.replace('[NEW]','[0]'))
# Insert the newly verified historical policy as reference 11 and renumber subsequent citations.
for t in root.xpath('.//w:t',namespaces=NS):
 if t.text:
  t.text=re.sub(r'\[(\d{1,2}(?:[-,]\d{1,2})*)\]',lambda m:'['+re.sub(r'\d+',lambda n:str(int(n.group())+1) if int(n.group())>=11 else n.group(),m.group(1))+']',t.text).replace('[0]','[11]')
ref=deepcopy(ps[237]);
for n in list(ref):
 if n.tag!=W+'pPr':ref.remove(n)
r=E.SubElement(ref,W+'r');rpr=ps[237].find(W+'r/'+W+'rPr')
if rpr is not None:r.append(deepcopy(rpr))
E.SubElement(r,W+'t').text='[11] 国务院. 国务院关于深化农村义务教育经费保障机制改革的通知: 国发〔2005〕43号[EB/OL]. (2005-12-24)[2026-10-12]. https://www.moe.gov.cn/jyb_xxgk/gk_gbgg/moe_0/moe_1133/moe_1134/tnull_14171.html.'
body.insert(body.index(ps[237]),ref)
# Use the formal indicator name consistently in prose (short chart labels remain unchanged).
for t in root.xpath('.//w:t',namespaces=NS):
 if t.text:t.text=t.text.replace('实际自身收入','实际自身财政收入').replace('自身收入响应差','自身财政收入响应差').replace('未确认独立机制关联','未确认独立条件关联')
# The body section inherits its odd footer; explicitly use that part for even pages too.
rels=E.fromstring(files['word/_rels/document.xml.rels']); relmap={r.get('Id'):r.get('Target') for r in rels}
secs=root.xpath('.//w:sectPr',namespaces=NS)
odd_id=secs[0].find(W+'footerReference').get('{'+NS['r']+'}id')
evenref=E.Element(W+'footerReference');evenref.set(W+'type','even');evenref.set('{'+NS['r']+'}id',odd_id)
secs[-1].insert(0,evenref)
pp=ps[142].find(W+'pPr')
if pp is None:pp=E.Element(W+'pPr');ps[142].insert(0,pp)
E.SubElement(pp,W+'keepLines')
for sec in root.xpath('.//w:sectPr',namespaces=NS):
 refs={r.get(W+'type'):r.get('{'+NS['r']+'}id') for r in sec.findall(W+'footerReference')}
 if 'even' in refs and 'default' in refs:
  even='word/'+relmap[refs['even']]; odd='word/'+relmap[refs['default']]
  if not E.fromstring(files[even]).xpath('.//w:instrText',namespaces=NS):files[even]=files[odd]
# Replace only figure 3, preserving its display dimensions and all other images.
embed=ps[64].xpath('.//a:blip/@r:embed',namespaces=NS)[0]
for effect in ps[64].xpath('.//a:blip/a:lum',namespaces=NS):effect.getparent().remove(effect)
image_name='word/'+relmap[embed]
fig=OUT/'图3_举办者收入构成分解_白底.png'
if not fig.exists():raise RuntimeError('Generate figure 3 before saving the report')
files[image_name]=fig.read_bytes()
files['word/document.xml']=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
dest=OUT/SRC.name
with ZipFile(dest,'w',ZIP_DEFLATED) as z:
 for n,b in files.items():z.writestr(n,b)
(OUT/'修订记录.json').write_text(json.dumps({'source':str(SRC),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'changes':changes,'new_policy_reference':11,'all_subsequent_citations_renumbered':True,'figure3_media':image_name,'tables_and_other_media_preserved':True},ensure_ascii=False,indent=2),encoding='utf-8')
print(dest)
