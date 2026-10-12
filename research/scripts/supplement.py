from parse import *
PROVINCES=['北京','天津','河北','山西','内蒙古','辽宁','吉林','黑龙江','上海','江苏','浙江','安徽','福建','江西','山东','河南','湖北','湖南','广东','广西','海南','重庆','四川','贵州','云南','西藏','陕西','甘肃','青海','宁夏','新疆']
def region(s):
    s=re.sub(r'\s','',s);s=re.sub(r'[A-Za-z\(\)\-]','',s)
    if s in ['总计','全国','合计']:return '全国'
    return next((p for p in PROVINCES if s.startswith(p)),None)
def number(s):
    s=s.replace(',','').replace(' ','')
    return float(s) if re.fullmatch(r'-?\d+(\.\d+)?',s) else None
rs=[]
for y,name in [(2010,'nbs_index_2011_additional_568'),(2011,'nbs_index_2012_additional_562')]:
    source=next(r for r in json.loads((ROOT/'further_sources.json').read_text(encoding='utf-8')) if r['key']==name)
    for tab in read(ROOT/source['path']).tables:
        for row in tab:
            p=region(row[0]) if row else None
            if p and len(row)>=7 and number(row[1]) is not None:
                rs.append(dict(year=y,province=p,schools=number(row[1]),entrants=number(row[2]),students=number(row[3]),graduates=number(row[4]),school_staff=number(row[5]),stage_teachers=number(row[6]),source=source['url'],status='补充样本；未与教育部主体面板续接；缺班级，教职工与学段教师覆盖不可混用'))
source=next(r for r in json.loads((ROOT/'legacy_xls.json').read_text(encoding='utf-8')) if r['key']=='nbs_index_2013_additional_514_xls')
for row in csv.reader(open(ROOT/'converted/nbs_index_2013_additional_514_xls.csv',encoding='utf-8-sig')):
    p=region(row[0]) if row else None
    if p and len(row)>=7 and number(row[1]) is not None:
        rs.append(dict(year=2012,province=p,schools=number(row[1]),entrants=number(row[4]),students=number(row[5]),graduates=number(row[6]),school_staff=number(row[2]),stage_teachers=number(row[3]),source=source['url'],status='补充样本；未与教育部主体面板续接；缺班级，教职工与学段教师覆盖不可混用'))
save_csv(ROOT/'data/primary_2010_2012_supplement.csv',rs)
checks=[];panel=json.loads((ROOT/'data/panel.json').read_text(encoding='utf-8'))
for row in csv.reader(open(ROOT/'converted/nbs_index_2014_additional_498_xls.csv',encoding='utf-8-sig')):
    p=region(row[0]) if row else None
    if p and len(row)>=7 and number(row[1]) is not None:
        r=next(r for r in panel if r['year']==2013 and r['province']==p and r['stage']=='primary')
        for k,i in [('schools',1),('teachers',3),('graduates',4),('entrants',5),('students',6)]:checks.append(dict(year=2013,province=p,metric=k,moe_value=r[k],nbs_value=number(row[i]),status='一致' if r[k]==number(row[i]) else '需核查',source='https://www.stats.gov.cn/sj/ndsj/2014/zk/html/Z2136C.xls'))
assert len(checks)==160 and all(r['status']=='一致' for r in checks)
save_csv(ROOT/'data/validation_nbs2013.csv',checks)
print('early supplement',len(rs),'cross-source2013',len(checks))
