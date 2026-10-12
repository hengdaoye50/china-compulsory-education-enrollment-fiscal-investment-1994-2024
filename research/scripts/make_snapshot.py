from parse import *
def rows(name):return list(csv.DictReader(open(ROOT/'data'/f'{name}.csv',encoding='utf-8-sig')))
def numeric(rs):
    for r in rs:
        for k,v in r.items():
            if v and re.fullmatch(r'-?\d+(\.\d+)?',v):r[k]=float(v)
    return rs
queries={}
specs=[('national_index','2013—2024全国两学段资源指数'),('changes_2024','2023—2024分省资源变化'),('teacher_density_decomposition','2023—2024分省师资密度恒等式分解'),('growth_shrink_phase','2014—2024增长与收缩阶段描述'),('finance_changes_2023','2022—2023分省生均经费变化'),('fiscal_2024','2024分省一般公共预算收支')]
for name,label in specs:
    rs=numeric(rows(name));urls=list(dict.fromkeys(v for r in rs for k,v in r.items() if 'source' in k and isinstance(v,str) and v.startswith('http')))
    if name in ['changes_2024','growth_shrink_phase','finance_changes_2023']:
        years={'changes_2024':{2023,2024},'growth_shrink_phase':set(range(2013,2025)),'finance_changes_2023':{2022,2023}}[name]
        schemas=json.loads((ROOT/'data/resource_schemas.json').read_text(encoding='utf-8'))
        urls=list(dict.fromkeys(urls+[s['source'] for s in schemas if s['year'] in years]))
    queries[name]={'rows':rs,'source':{'title':label,'provider':'教育部、国家统计局公开统计','files':[{'name':f'{name}.csv','path':f'../data/{name}.csv'}],'links':[{'label':u.split('/')[-1],'url':u} for u in urls], 'description':'2026年10月4日下载并核对；完整原件、逐字段来源与脚本保存在项目research目录。','evidenceFlow':[{'title':'获取原件','detail':'读取官方目录真实链接，保存HTML、Word附件或年鉴图片，并记录SHA256。'},{'title':'提取与核验','detail':'按逐年表头映射提取；31省求和与全国资源总数核对。经费保留原值、官方增长率、2021口径断点与2024分学段缺失。'},{'title':'计算','detail':'变化率=100×(本年/上年−1)。师资密度对数变化=100ln(T1/T0)−100ln(S1/S0)。不从生均经费推算小学总投入。'}],'caveats':['描述性关联，不作因果解释。增长与收缩组的地区、年份和变化幅度不同。','学校数与学生覆盖组织形式不同，不计算校均学生。','经费为名义金额；财力收入/支出是结构代理，不能等同财政压力。']}}
snapshot={'title':'人口变化下，教育资源如何调整？','status':'draft','buildStatus':'complete','surface':'report','filters':[],'queries':queries}
matched_source=ROOT/'data/matched_source.json'
if matched_source.exists():
    source=json.loads(matched_source.read_text(encoding='utf-8'))
    for name in ['matched_phase_summary','matched_pairs']:
        queries[name]={'rows':numeric(rows(name)),'source':source}
(ROOT/'snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
